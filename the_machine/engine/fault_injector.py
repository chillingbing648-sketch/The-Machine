"""Controlled AST-level Fault Injection Engine for Python software."""

import ast
import difflib
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from the_machine.core.models import MutationRecord


class MutationOperator:
    """Base class for AST mutation operators."""
    name: str = "BASE"

    def can_mutate(self, node: ast.AST) -> bool:
        raise NotImplementedError

    def apply(self, node: ast.AST) -> ast.AST:
        raise NotImplementedError


class ComparisonOperatorMutation(MutationOperator):
    """Inverts or alters comparison operators (e.g., < to <=, == to !=, > to <)."""
    name: str = "COMPARISON_OPERATOR"

    SWAPS = {
        ast.Lt: ast.LtE,
        ast.LtE: ast.Lt,
        ast.Gt: ast.GtE,
        ast.GtE: ast.Gt,
        ast.Eq: ast.NotEq,
        ast.NotEq: ast.Eq,
    }

    def can_mutate(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            return type(node.ops[0]) in self.SWAPS
        return False

    def apply(self, node: ast.AST) -> ast.AST:
        if not self.can_mutate(node):
            return node
        op_cls = type(node.ops[0])
        new_op_cls = self.SWAPS[op_cls]
        new_compare = ast.Compare(
            left=node.left,
            ops=[new_op_cls()],
            comparators=node.comparators,
        )
        return ast.copy_location(new_compare, node)


class BooleanInversionMutation(MutationOperator):
    """Inverts boolean conditions with 'not' or flips and/or."""
    name: str = "BOOLEAN_INVERSION"

    def can_mutate(self, node: ast.AST) -> bool:
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return True
        if isinstance(node, ast.BoolOp):
            return True
        return False

    def apply(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return node.operand
        if isinstance(node, ast.BoolOp):
            new_op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
            return ast.copy_location(ast.BoolOp(op=new_op, values=node.values), node)
        return node


class BoundaryOffByOneMutation(MutationOperator):
    """Shifts numerical boundary constants by +1 or -1."""
    name: str = "BOUNDARY_OFF_BY_ONE"

    def can_mutate(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return True
        return False

    def apply(self, node: ast.AST) -> ast.AST:
        if not self.can_mutate(node):
            return node
        # Shift boundary by 1
        new_val = node.value + 1
        return ast.copy_location(ast.Constant(value=new_val), node)


class ConstantReturnSubstitutionMutation(MutationOperator):
    """Substitutes return values or constants (e.g. 0 to 1, True to False, return to None)."""
    name: str = "CONSTANT_RETURN_SUBSTITUTION"

    def can_mutate(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Return) and node.value is not None:
            return True
        return False

    def apply(self, node: ast.AST) -> ast.AST:
        if not self.can_mutate(node):
            return node
        # Replace returned value with None or 0
        return ast.copy_location(ast.Return(value=ast.Constant(value=None)), node)


class FaultInjector:
    """Systematic, AST-driven fault injector supporting narrow, traceable mutations."""

    OPERATORS = {
        "COM": ComparisonOperatorMutation(),
        "BLI": BooleanInversionMutation(),
        "OB1": BoundaryOffByOneMutation(),
        "CRS": ConstantReturnSubstitutionMutation(),
    }

    def __init__(self, allowed_paths: Optional[List[str]] = None):
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths] if allowed_paths else None

    def _verify_path_allowed(self, target_path: Path) -> None:
        resolved = target_path.resolve()
        if self.allowed_paths is not None:
            if not any(resolved == ap or ap in resolved.parents for ap in self.allowed_paths):
                raise PermissionError(f"Target path {resolved} is outside allowed mutation scope")

    def inspect_mutation_targets(self, file_path: Path, operator_name: str = "COM") -> List[Tuple[int, str]]:
        """List candidate lines in file where operator can be applied."""
        self._verify_path_allowed(file_path)
        operator = self.OPERATORS.get(operator_name)
        if not operator:
            raise ValueError(f"Unknown operator: {operator_name}")

        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        targets = []

        for node in ast.walk(tree):
            if operator.can_mutate(node):
                lineno = getattr(node, "lineno", None)
                if lineno is not None:
                    snippet = ast.unparse(node)
                    targets.append((lineno, snippet))

        return targets

    def inject_mutation(
        self,
        file_path: Path,
        operator_name: str = "COM",
        target_line: Optional[int] = None,
    ) -> MutationRecord:
        """
        Inject a controlled mutation into target file.
        If target_line is None, selects the first matching AST node.
        """
        self._verify_path_allowed(file_path)
        operator = self.OPERATORS.get(operator_name)
        if not operator:
            raise ValueError(f"Unknown operator: {operator_name}")

        original_content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(original_content)

        chosen_node = None
        candidates = []
        for node in ast.walk(tree):
            if operator.can_mutate(node):
                lineno = getattr(node, "lineno", None)
                if lineno is not None:
                    candidates.append((lineno, node))
                    if target_line is not None and lineno == target_line:
                        chosen_node = node
                        break

        # If exact line not matched but target_line specified, choose closest candidate
        if chosen_node is None and candidates:
            if target_line is not None:
                candidates.sort(key=lambda pair: abs(pair[0] - target_line))
                chosen_node = candidates[0][1]
            else:
                chosen_node = candidates[0][1]

        if chosen_node is None:
            raise RuntimeError(
                f"No compatible AST node found for operator '{operator_name}' in {file_path} (line: {target_line})"
            )

        lineno = chosen_node.lineno
        original_node_unparse = ast.unparse(chosen_node)

        # Replace chosen node in AST
        class NodeReplacer(ast.NodeTransformer):
            def __init__(self, target: ast.AST, op: MutationOperator):
                self.target = target
                self.op = op
                self.mutated = False

            def visit(self, node: ast.AST) -> ast.AST:
                if node is self.target and not self.mutated:
                    self.mutated = True
                    return self.op.apply(node)
                return self.generic_visit(node)

        transformer = NodeReplacer(chosen_node, operator)
        mutated_tree = transformer.visit(tree)
        ast.fix_missing_locations(mutated_tree)

        mutated_content = ast.unparse(mutated_tree)
        file_path.write_text(mutated_content, encoding="utf-8")

        return MutationRecord(
            mutation_id=f"mut_{uuid.uuid4().hex[:8]}",
            operator=operator.name,
            file_path=str(file_path.resolve()),
            line_number=lineno,
            original_code=original_node_unparse,
            mutated_code=ast.unparse(operator.apply(chosen_node)),
        )

    def revert_mutation(self, record: MutationRecord, original_full_content: Optional[str] = None) -> None:
        """Revert mutation either from original text or by inverse transformation."""
        target_path = Path(record.file_path)
        self._verify_path_allowed(target_path)
        if original_full_content is not None:
            target_path.write_text(original_full_content, encoding="utf-8")
        else:
            # Fallback line-based replacement
            content = target_path.read_text(encoding="utf-8")
            if record.mutated_code in content:
                content = content.replace(record.mutated_code, record.original_code, 1)
                target_path.write_text(content, encoding="utf-8")
