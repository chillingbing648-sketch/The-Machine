"""Pluggable Repair Engine and Candidate Patch Synthesizers."""

import ast
import difflib
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from the_machine.core.models import (
    PatchCandidate,
    SuspiciousLocation,
    TestExecutionReport,
)


class RepairStrategy(ABC):
    """Abstract base class for automated program repair strategies."""
    name: str = "base"

    @abstractmethod
    def generate_patches(
        self,
        location: SuspiciousLocation,
        report: TestExecutionReport,
        workspace_path: Path,
    ) -> List[PatchCandidate]:
        """Synthesize candidate patches targeting the given suspicious location."""
        raise NotImplementedError


def generate_diff(original_file: Path, modified_content: str) -> str:
    """Generate a clean unified diff between original file and modified string."""
    orig_lines = original_file.read_text(encoding="utf-8").splitlines(keepends=True)
    mod_lines = [line + "\n" if not line.endswith("\n") else line for line in modified_content.splitlines()]
    diff = difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{original_file.name}",
        tofile=f"b/{original_file.name}",
    )
    return "".join(diff)


class DeterministicTemplateStrategy(RepairStrategy):
    """
    Template-based deterministic transformations for common syntax faults:
    - Inversion of comparison operators (<->, ==, !=, <=, >=)
    - Reversal of arithmetic boundary shifts (+1 / -1)
    - Boolean logic negation
    """
    name: str = "deterministic_template"

    COMPARISON_INVERSIONS = {
        ast.Lt: [ast.LtE, ast.Gt, ast.Eq],
        ast.LtE: [ast.Lt, ast.GtE, ast.Eq],
        ast.Gt: [ast.GtE, ast.Lt, ast.Eq],
        ast.GtE: [ast.Gt, ast.LtE, ast.Eq],
        ast.Eq: [ast.NotEq],
        ast.NotEq: [ast.Eq],
    }

    def generate_patches(
        self,
        location: SuspiciousLocation,
        report: TestExecutionReport,
        workspace_path: Path,
    ) -> List[PatchCandidate]:
        target_file = Path(location.file_path)
        if not target_file.exists():
            return []

        original_text = target_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(original_text)
        except SyntaxError:
            return []

        candidates: List[PatchCandidate] = []
        target_lines = {location.line_number + offset for offset in range(-2, 3)}

        # Find target node at or adjacent to suspicious line
        for node in ast.walk(tree):
            node_line = getattr(node, "lineno", None)
            if node_line in target_lines:
                # 1. Comparison Operator Inversion Template
                if isinstance(node, ast.Compare) and len(node.ops) == 1:
                    op_type = type(node.ops[0])
                    replacement_ops = self.COMPARISON_INVERSIONS.get(op_type, [])
                    for rep_op_cls in replacement_ops:
                        new_node = ast.Compare(
                            left=node.left,
                            ops=[rep_op_cls()],
                            comparators=node.comparators,
                        )
                        patch = self._build_candidate(
                            tree, node, new_node, target_file, node_line,
                            f"Invert comparison operator from {op_type.__name__} to {rep_op_cls.__name__}"
                        )
                        if patch:
                            candidates.append(patch)

                # 2. Boolean Negation Template
                elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                    # Remove 'not'
                    patch = self._build_candidate(
                        tree, node, node.operand, target_file, node_line,
                        "Remove unary 'not' operator"
                    )
                    if patch:
                        candidates.append(patch)

                # 3. Off-by-one Boundary Template
                elif isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
                    for offset in [-1, 1]:
                        new_val = node.value + offset
                        new_node = ast.Constant(value=new_val)
                        patch = self._build_candidate(
                            tree, node, new_node, target_file, node_line,
                            f"Adjust boundary integer constant by {offset} (from {node.value} to {new_val})"
                        )
                        if patch:
                            candidates.append(patch)

        return candidates

    def _build_candidate(
        self,
        tree: ast.AST,
        target_node: ast.AST,
        new_node: ast.AST,
        file_path: Path,
        line_no: int,
        explanation: str,
    ) -> Optional[PatchCandidate]:
        class Replacer(ast.NodeTransformer):
            def __init__(self, old: ast.AST, replacement: ast.AST):
                self.old = old
                self.replacement = replacement
                self.done = False

            def visit(self, n: ast.AST) -> ast.AST:
                if n is self.old and not self.done:
                    self.done = True
                    return ast.copy_location(self.replacement, self.old)
                return self.generic_visit(n)

        # Clone AST for mutation
        tree_copy = ast.parse(file_path.read_text(encoding="utf-8"))
        # Re-find matching node in tree_copy
        matching_node = None
        for n in ast.walk(tree_copy):
            if getattr(n, "lineno", None) == line_no and type(n) is type(target_node):
                matching_node = n
                break

        if not matching_node:
            return None

        transformer = Replacer(matching_node, new_node)
        modified_tree = transformer.visit(tree_copy)
        ast.fix_missing_locations(modified_tree)

        modified_source = ast.unparse(modified_tree)
        diff = generate_diff(file_path, modified_source)
        if not diff:
            return None

        return PatchCandidate(
            candidate_id=f"cand_{uuid.uuid4().hex[:8]}",
            strategy_name=self.name,
            file_path=str(file_path.resolve()),
            line_number=line_no,
            original_code=ast.unparse(target_node),
            replacement_code=ast.unparse(new_node),
            diff=diff,
            explanation=explanation,
            cost=1.0,
        )


class SearchBasedASTStrategy(RepairStrategy):
    """
    Search-based program repair strategy: explores allowable AST mutations
    within suspicious statement boundaries.
    """
    name: str = "search_ast"

    def generate_patches(
        self,
        location: SuspiciousLocation,
        report: TestExecutionReport,
        workspace_path: Path,
    ) -> List[PatchCandidate]:
        target_file = Path(location.file_path)
        if not target_file.exists():
            return []

        original_text = target_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(original_text)
        except SyntaxError:
            return []

        candidates: List[PatchCandidate] = []
        target_lines = {location.line_number + offset for offset in range(-2, 3)}
        for node in ast.walk(tree):
            node_line = getattr(node, "lineno", None)
            if node_line in target_lines:
                # Search comparisons in statement
                if isinstance(node, ast.Compare):
                    for alt_op in [ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE]:
                        if not isinstance(node.ops[0], alt_op):
                            new_comp = ast.Compare(
                                left=node.left,
                                ops=[alt_op()],
                                comparators=node.comparators,
                            )
                            patch = self._make_candidate(
                                tree, node, new_comp, target_file, node_line,
                                f"Search substitution: {type(node.ops[0]).__name__} -> {alt_op.__name__}"
                            )
                            if patch:
                                candidates.append(patch)
        return candidates

    def _make_candidate(
        self,
        tree: ast.AST,
        old_node: ast.AST,
        new_node: ast.AST,
        file_path: Path,
        line_no: int,
        explanation: str,
    ) -> Optional[PatchCandidate]:
        class ASTReplacer(ast.NodeTransformer):
            def __init__(self, target: ast.AST, replacement: ast.AST):
                self.target = target
                self.replacement = replacement
                self.replaced = False

            def visit(self, n: ast.AST) -> ast.AST:
                if n is self.target and not self.replaced:
                    self.replaced = True
                    return ast.copy_location(self.replacement, self.target)
                return self.generic_visit(n)

        tree_copy = ast.parse(file_path.read_text(encoding="utf-8"))
        match = None
        for n in ast.walk(tree_copy):
            if getattr(n, "lineno", None) == line_no and type(n) is type(old_node):
                match = n
                break
        if not match:
            return None

        transformer = ASTReplacer(match, new_node)
        mod_tree = transformer.visit(tree_copy)
        ast.fix_missing_locations(mod_tree)

        mod_code = ast.unparse(mod_tree)
        diff = generate_diff(file_path, mod_code)
        if not diff:
            return None

        return PatchCandidate(
            candidate_id=f"cand_{uuid.uuid4().hex[:8]}",
            strategy_name=self.name,
            file_path=str(file_path.resolve()),
            line_number=line_no,
            original_code=ast.unparse(old_node),
            replacement_code=ast.unparse(new_node),
            diff=diff,
            explanation=explanation,
            cost=2.0,
        )


class RepairEngine:
    """Coordinates registered repair strategies and prioritizes candidate patch synthesis."""

    def __init__(self, strategies: Optional[List[RepairStrategy]] = None):
        self.strategies: Dict[str, RepairStrategy] = {}
        defaults = [DeterministicTemplateStrategy(), SearchBasedASTStrategy()]
        for strat in strategies or defaults:
            self.register_strategy(strat)

    def register_strategy(self, strategy: RepairStrategy) -> None:
        self.strategies[strategy.name] = strategy

    def synthesize_candidates(
        self,
        locations: List[SuspiciousLocation],
        report: TestExecutionReport,
        workspace_path: Path,
        enabled_strategies: Optional[List[str]] = None,
        max_candidates: int = 10,
    ) -> List[PatchCandidate]:
        """
        Evaluate suspicious locations across enabled strategies and yield ranked candidate patches.
        """
        all_candidates: List[PatchCandidate] = []
        selected_strategies = [
            self.strategies[s] for s in (enabled_strategies or self.strategies.keys())
            if s in self.strategies
        ]

        # Prioritize locations with higher suspiciousness scores
        for location in sorted(locations, key=lambda l: l.score, reverse=True):
            for strat in selected_strategies:
                patches = strat.generate_patches(location, report, workspace_path)
                for patch in patches:
                    # Prevent exact duplicate diffs
                    if not any(existing.diff == patch.diff for existing in all_candidates):
                        all_candidates.append(patch)
                        if len(all_candidates) >= max_candidates:
                            return all_candidates

        return all_candidates
