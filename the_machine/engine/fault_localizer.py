"""Evidence-based Fault Localization Engine implementing Ochiai, Tarantula, DStar, and STS."""

import ast
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from the_machine.core.models import (
    LocalizationMetrics,
    SuspiciousLocation,
    TestExecutionReport,
)
from the_machine.engine.coverage_collector import CoverageMatrix


class FaultLocalizer:
    """Localizes likely fault locations using spectrum analysis (Ochiai/Tarantula/DStar) and stack slicing."""

    def __init__(self, workspace_path: Optional[Path] = None, alpha: float = 0.6):
        self.workspace_path = Path(workspace_path).resolve() if workspace_path else None
        self.alpha = alpha  # Weight for SBFL vs Stack Trace Slicing in hybrid ranking

    def compute_ochiai(self, ef: int, ep: int, nf: int, np: int) -> float:
        """Ochiai metric: ef / sqrt((ef + nf) * (ef + ep))"""
        denom = math.sqrt((ef + nf) * (ef + ep))
        return (ef / denom) if denom > 0 else 0.0

    def compute_tarantula(self, ef: int, ep: int, nf: int, np: int) -> float:
        """Tarantula metric: (ef / (ef + nf)) / ((ef / (ef + nf)) + (ep / (ep + np)))"""
        total_f = ef + nf
        total_p = ep + np
        if total_f == 0:
            return 0.0
        fail_ratio = ef / total_f
        pass_ratio = (ep / total_p) if total_p > 0 else 0.0
        denom = fail_ratio + pass_ratio
        return (fail_ratio / denom) if denom > 0 else 0.0

    def compute_dstar(self, ef: int, ep: int, nf: int, np: int, star: int = 2) -> float:
        """DStar metric: (ef ** star) / (ep + nf)"""
        denom = ep + nf
        if denom == 0:
            return float(ef ** star) if ef > 0 else 0.0
        return (ef ** star) / denom

    def localize_fault(
        self,
        report: TestExecutionReport,
        workspace_path: Optional[Path] = None,
        matrix: Optional[CoverageMatrix] = None,
        metric_name: str = "ochiai",
    ) -> List[SuspiciousLocation]:
        """
        Synthesize suspicious locations combining SBFL spectrum and stack trace evidence.
        Scores are normalized to [0.0, 1.0].
        """
        workspace = Path(workspace_path or self.workspace_path or ".").resolve()

        # Step 1: Compute Stack Trace Slicing (STS) scores
        sts_scores: Dict[Tuple[str, int], float] = {}
        sts_evidence: Dict[Tuple[str, int], List[str]] = {}

        for failure in report.failures:
            if failure.file_path and failure.line_number:
                key = (failure.file_path, failure.line_number)
                sts_scores[key] = sts_scores.get(key, 0.0) + 1.0
                sts_evidence.setdefault(key, []).append(
                    f"Direct target from failure in {failure.test_id} ({failure.exception_type})"
                )

            trace_lines = failure.stack_trace.splitlines()
            for idx, line in enumerate(trace_lines):
                m = re.search(r"([a-zA-Z0-9_\-\\\/\.]+\.py):(\d+):", line)
                if m:
                    rel_or_abs = m.group(1)
                    line_no = int(m.group(2))
                    file_p = Path(rel_or_abs)
                    if not file_p.is_absolute():
                        file_p = (workspace / file_p).resolve()

                    if file_p.exists() and "test_" not in file_p.name and ".venv" not in file_p.parts:
                        key = (str(file_p), line_no)
                        weight = 0.8 if idx == 0 else 0.5
                        sts_scores[key] = sts_scores.get(key, 0.0) + weight
                        sts_evidence.setdefault(key, []).append(
                            f"Stack frame in {failure.test_id} (line {line_no})"
                        )

        # Normalize STS scores
        max_sts = max(sts_scores.values()) if sts_scores else 1.0
        norm_sts = {k: v / max_sts for k, v in sts_scores.items()}

        # Step 2: Compute Spectrum-Based (SBFL) scores if matrix is provided
        sbfl_scores: Dict[Tuple[str, int], float] = {}
        sbfl_evidence: Dict[Tuple[str, int], str] = {}

        if matrix and matrix.spectrum and matrix.target_file:
            target_path_str = str(Path(matrix.target_file).resolve())
            raw_sbfl = {}
            for line_no, (ef, ep, nf, np) in matrix.spectrum.items():
                if metric_name.lower() == "tarantula":
                    score = self.compute_tarantula(ef, ep, nf, np)
                elif metric_name.lower() == "dstar":
                    score = self.compute_dstar(ef, ep, nf, np)
                else:
                    score = self.compute_ochiai(ef, ep, nf, np)

                key = (target_path_str, line_no)
                raw_sbfl[key] = score
                sbfl_evidence[key] = f"SBFL({metric_name.upper()}={score:.3f}; ef={ef}, ep={ep}, nf={nf}, np={np})"

            max_sbfl = max(raw_sbfl.values()) if raw_sbfl and max(raw_sbfl.values()) > 0 else 1.0
            sbfl_scores = {k: v / max_sbfl for k, v in raw_sbfl.items()}

        # Step 3: Combine SBFL and STS into Hybrid Score
        all_keys: Set[Tuple[str, int]] = set(norm_sts.keys()) | set(sbfl_scores.keys())
        combined_scores: Dict[Tuple[str, int], float] = {}
        combined_evidence: Dict[Tuple[str, int], str] = {}

        for key in all_keys:
            s_sts = norm_sts.get(key, 0.0)
            s_sbfl = sbfl_scores.get(key, 0.0)

            if sbfl_scores and norm_sts:
                # Hybrid blending
                score = (self.alpha * s_sbfl) + ((1.0 - self.alpha) * s_sts)
            elif sbfl_scores:
                score = s_sbfl
            else:
                score = s_sts

            ev_parts = []
            if key in sbfl_evidence:
                ev_parts.append(sbfl_evidence[key])
            if key in sts_evidence:
                ev_parts.append("; ".join(set(sts_evidence[key])))

            combined_scores[key] = score
            combined_evidence[key] = " | ".join(ev_parts)

        # Retrieve source snippets
        snippets: Dict[Tuple[str, int], str] = {}
        for (fpath, lno) in all_keys:
            try:
                lines = Path(fpath).read_text(encoding="utf-8").splitlines()
                if 1 <= lno <= len(lines):
                    snippets[(fpath, lno)] = lines[lno - 1].strip()
            except Exception:
                snippets[(fpath, lno)] = ""

        # Normalize and construct ranked list
        max_comb = max(combined_scores.values()) if combined_scores else 1.0
        ranked: List[SuspiciousLocation] = []

        for key, raw_val in sorted(combined_scores.items(), key=lambda it: it[1], reverse=True):
            fpath, lno = key
            norm_val = round(min(1.0, raw_val / max_comb), 4) if max_comb > 0 else 0.0
            # Exclude lines with 0 score
            if norm_val > 0.0:
                ranked.append(
                    SuspiciousLocation(
                        file_path=fpath,
                        line_number=lno,
                        score=norm_val,
                        evidence=combined_evidence.get(key, "Execution evidence"),
                        statement_code=snippets.get(key, ""),
                    )
                )

        # Fallback if no locations were isolated
        if not ranked and report.failures:
            for py_file in workspace.rglob("*.py"):
                if "test_" in py_file.name or ".venv" in py_file.parts:
                    continue
                try:
                    tree = ast.parse(py_file.read_text(encoding="utf-8"))
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.Compare, ast.Return)):
                            lineno = getattr(node, "lineno", 1)
                            ranked.append(
                                SuspiciousLocation(
                                    file_path=str(py_file.resolve()),
                                    line_number=lineno,
                                    score=0.3,
                                    evidence=f"Static AST candidate in {py_file.name}",
                                    statement_code=ast.unparse(node),
                                )
                            )
                            break
                except Exception:
                    continue

        return ranked

    @staticmethod
    def evaluate_localization(
        ranked_locations: List[SuspiciousLocation],
        ground_truth_line: int,
        window: int = 2,
    ) -> LocalizationMetrics:
        """
        Evaluate fault localization ranking against known ground truth fault line.
        Permits statement window around exception boundary if configured.
        """
        predicted_rank = -1
        target_lines = {ground_truth_line + off for off in range(-window, window + 1)}

        for rank_idx, loc in enumerate(ranked_locations, 1):
            if loc.line_number in target_lines:
                predicted_rank = rank_idx
                break

        if predicted_rank != -1:
            top_1 = (predicted_rank == 1)
            top_3 = (predicted_rank <= 3)
            top_5 = (predicted_rank <= 5)
            reciprocal_rank = round(1.0 / predicted_rank, 4)
        else:
            top_1, top_3, top_5 = False, False, False
            reciprocal_rank = 0.0

        return LocalizationMetrics(
            ground_truth_line=ground_truth_line,
            predicted_rank=predicted_rank,
            top_1=top_1,
            top_3=top_3,
            top_5=top_5,
            reciprocal_rank=reciprocal_rank,
            total_suspicious_lines=len(ranked_locations),
        )
