"""Evidence-based Fault Localization Engine."""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional
from the_machine.core.models import SuspiciousLocation, TestExecutionReport


class FaultLocalizer:
    """Localizes likely fault locations using stack trace analysis and execution evidence."""

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = Path(workspace_path).resolve() if workspace_path else None

    def localize_fault(
        self,
        report: TestExecutionReport,
        workspace_path: Optional[Path] = None,
    ) -> List[SuspiciousLocation]:
        """
        Synthesize suspicious locations from execution failure report and stack traces.
        Assigns scores normalized between 0.0 and 1.0.
        """
        workspace = Path(workspace_path or self.workspace_path or ".").resolve()
        scores: Dict[tuple[str, int], float] = {}
        evidence_map: Dict[tuple[str, int], List[str]] = {}
        snippets: Dict[tuple[str, int], str] = {}

        for failure in report.failures:
            # 1. Direct failure location (if already parsed by detector)
            if failure.file_path and failure.line_number:
                key = (failure.file_path, failure.line_number)
                scores[key] = scores.get(key, 0.0) + 1.0
                evidence_map.setdefault(key, []).append(
                    f"Direct target from failure in {failure.test_id} ({failure.exception_type})"
                )

            # 2. Extract frames from stack trace
            trace_lines = failure.stack_trace.splitlines()
            for idx, line in enumerate(trace_lines):
                # Pattern: file.py:line: in func or > line_content
                m = re.search(r"([a-zA-Z0-9_\-\\\/\.]+\.py):(\d+):", line)
                if m:
                    rel_or_abs = m.group(1)
                    line_no = int(m.group(2))
                    file_p = Path(rel_or_abs)
                    if not file_p.is_absolute():
                        file_p = (workspace / file_p).resolve()

                    # Filter: must exist, inside workspace, not a test file
                    if file_p.exists() and "test_" not in file_p.name:
                        key = (str(file_p), line_no)
                        # Top-of-stack gets higher weight
                        weight = 0.8 if idx == 0 else 0.5
                        scores[key] = scores.get(key, 0.0) + weight
                        evidence_map.setdefault(key, []).append(
                            f"Stack frame in {failure.test_id} (line {line_no})"
                        )

        # Retrieve source statements for ranked locations
        for (fpath, lno) in scores.keys():
            try:
                p = Path(fpath)
                lines = p.read_text(encoding="utf-8").splitlines()
                if 1 <= lno <= len(lines):
                    snippets[(fpath, lno)] = lines[lno - 1].strip()
            except Exception:
                snippets[(fpath, lno)] = ""

        # Normalize scores to [0.1, 1.0]
        max_score = max(scores.values()) if scores else 1.0
        ranked_locations = []
        for key, raw_score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
            fpath, lno = key
            norm_score = round(min(1.0, raw_score / max_score), 4)
            evidences = "; ".join(set(evidence_map[key]))
            ranked_locations.append(
                SuspiciousLocation(
                    file_path=fpath,
                    line_number=lno,
                    score=norm_score,
                    evidence=evidences,
                    statement_code=snippets.get(key, ""),
                )
            )

        # Fallback if no trace frames found in app code: scan project files for relevant functions
        if not ranked_locations and report.failures:
            first_fail = report.failures[0]
            for py_file in workspace.rglob("*.py"):
                if "test_" in py_file.name or ".venv" in py_file.parts:
                    continue
                try:
                    tree = ast.parse(py_file.read_text(encoding="utf-8"))
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.Compare, ast.Return)):
                            lineno = getattr(node, "lineno", 1)
                            ranked_locations.append(
                                SuspiciousLocation(
                                    file_path=str(py_file.resolve()),
                                    line_number=lineno,
                                    score=0.3,
                                    evidence=f"Static fallback candidate in {py_file.name}",
                                    statement_code=ast.unparse(node),
                                )
                            )
                            break
                except Exception:
                    continue

        return ranked_locations
