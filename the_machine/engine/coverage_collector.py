"""Spectrum-Based Fault Localization (SBFL) Coverage Collector."""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class TestCoverageResult:
    """Coverage trace recorded for a single test execution."""
    test_id: str
    passed: bool
    executed_lines: List[int]
    duration_sec: float = 0.0


@dataclass
class CoverageMatrix:
    """Contingency table representing execution spectrum across all tests."""
    target_file: str
    total_passing_tests: int
    total_failing_tests: int
    # line -> (ef, ep, nf, np)
    spectrum: Dict[int, tuple[int, int, int, int]] = field(default_factory=dict)
    test_results: List[TestCoverageResult] = field(default_factory=list)


class CoverageCollector:
    """Collects per-test statement execution traces for spectrum calculation."""

    def __init__(self, python_executable: Optional[str] = None):
        self.python_executable = python_executable or sys.executable

    def collect_matrix(
        self,
        workspace_path: Path,
        target_rel_path: str,
        test_rel_path: str,
        failing_tests: Optional[Set[str]] = None,
        timeout_sec: float = 60.0,
    ) -> CoverageMatrix:
        """
        Execute test suite under statement tracer and build SBFL contingency matrix.
        failing_tests: optional ground truth set of failing test IDs from FailureDetector.
        """
        workspace = Path(workspace_path).resolve()
        target_file = (workspace / target_rel_path).resolve()
        test_file = (workspace / test_rel_path).resolve()

        if not target_file.exists() or not test_file.exists():
            return CoverageMatrix(target_file=str(target_file), total_passing_tests=0, total_failing_tests=0)

        repo_root = Path(__file__).resolve().parent.parent.parent
        python_paths = [str(workspace), str(repo_root)]

        sanitized_env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "WINDIR": os.environ.get("WINDIR", "C:\\Windows"),
            "PYTHONPATH": os.pathsep.join(python_paths),
            "PYTHONUNBUFFERED": "1",
            "TEMP": os.environ.get("TEMP", ""),
            "TMP": os.environ.get("TMP", ""),
        }

        cmd = [
            self.python_executable,
            "-m",
            "the_machine.engine.sbfl_tracer",
            str(target_file),
            str(test_file),
        ]

        stdout = ""
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(workspace),
                env=sanitized_env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            stdout = proc.stdout.decode("utf-8", errors="replace") if isinstance(proc.stdout, bytes) else (proc.stdout or "")
        except Exception:
            stdout = ""

        raw_test_data = []
        if "===SBFL_SPECTRUM_BEGIN===" in stdout and "===SBFL_SPECTRUM_END===" in stdout:
            try:
                raw_json = stdout.split("===SBFL_SPECTRUM_BEGIN===")[1].split("===SBFL_SPECTRUM_END===")[0].strip()
                raw_test_data = json.loads(raw_json)
            except Exception:
                raw_test_data = []

        fail_set = failing_tests or set()
        test_results = []
        for item in raw_test_data:
            t_id = item.get("test_id", "")
            # If failing_tests is provided, override outcome based on FailureDetector
            passed = (t_id not in fail_set) if failing_tests is not None else item.get("passed", True)
            test_results.append(
                TestCoverageResult(
                    test_id=t_id,
                    passed=passed,
                    executed_lines=item.get("executed_lines", []),
                )
            )

        total_passing = sum(1 for r in test_results if r.passed)
        total_failing = sum(1 for r in test_results if not r.passed)

        all_lines: Set[int] = set()
        for r in test_results:
            all_lines.update(r.executed_lines)

        spectrum: Dict[int, tuple[int, int, int, int]] = {}
        for line in sorted(all_lines):
            ef = sum(1 for r in test_results if not r.passed and line in r.executed_lines)
            ep = sum(1 for r in test_results if r.passed and line in r.executed_lines)
            nf = total_failing - ef
            np = total_passing - ep
            spectrum[line] = (ef, ep, nf, np)

        return CoverageMatrix(
            target_file=str(target_file),
            total_passing_tests=total_passing,
            total_failing_tests=total_failing,
            spectrum=spectrum,
            test_results=test_results,
        )
