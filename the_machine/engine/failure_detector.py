"""Sandboxed Failure Detection Engine for Python test suites."""

import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional
from the_machine.core.models import TestExecutionReport, TestFailure


class FailureDetector:
    """Executes test suites under controlled subprocess isolation and parses failure evidence."""

    def __init__(self, python_executable: Optional[str] = None):
        self.python_executable = python_executable or sys.executable

    def run_tests(
        self,
        workspace_path: Path,
        test_target: Optional[str] = None,
        timeout_sec: float = 30.0,
    ) -> TestExecutionReport:
        """
        Run pytest within workspace and parse results into structured telemetry.
        """
        workspace = Path(workspace_path).resolve()
        cmd = [self.python_executable, "-m", "pytest", "-v", "--tb=short"]
        if test_target:
            if "::" in test_target or test_target.endswith(".py"):
                cmd.append(test_target)
            else:
                cmd.extend(["-k", test_target])

        # Sanitize environment: keep minimal necessary paths, strip secrets
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

        start_time = time.time()
        timed_out = False
        stdout, stderr = "", ""
        exit_code = 0

        try:
            process = subprocess.run(
                cmd,
                cwd=str(workspace),
                env=sanitized_env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            stdout = process.stdout
            stderr = process.stderr
            exit_code = process.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            exit_code = -1
        except Exception as exc:
            stderr = f"Subprocess invocation error: {str(exc)}"
            exit_code = 2

        duration = time.time() - start_time
        failures = self._parse_failures(stdout, stderr, workspace)

        passed_count, failed_count, total_count = self._parse_summary_counts(stdout)
        if total_count == 0:
            total_count = len(failures)
            failed_count = len(failures)

        passed = (exit_code == 0) and not timed_out and len(failures) == 0

        return TestExecutionReport(
            passed=passed,
            total_tests=total_count,
            passed_tests=passed_count,
            failed_tests=failed_count,
            failures=failures,
            duration_sec=duration,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            timed_out=timed_out,
        )

    def _parse_summary_counts(self, stdout: str) -> tuple[int, int, int]:
        """Extract test counts from pytest summary line like '1 failed, 12 passed in 0.20s'."""
        passed = 0
        failed = 0
        summary_match = re.search(r"=+\s*(.+?)\s+in\s+[\d\.]+s\s*=+", stdout)
        if summary_match:
            parts = summary_match.group(1).split(",")
            for part in parts:
                part = part.strip()
                if "passed" in part:
                    m = re.search(r"(\d+)\s+passed", part)
                    if m:
                        passed = int(m.group(1))
                elif "failed" in part:
                    m = re.search(r"(\d+)\s+failed", part)
                    if m:
                        failed = int(m.group(1))
                elif "error" in part:
                    m = re.search(r"(\d+)\s+error", part)
                    if m:
                        failed += int(m.group(1))
        return passed, failed, passed + failed

    def _parse_failures(self, stdout: str, stderr: str, workspace: Path) -> List[TestFailure]:
        """Extract individual test failure details, exception types, and stack traces."""
        failures = []
        combined = stdout + "\n" + stderr

        # Match pytest FAILURES section (delimiters are at least 3 underscores or 5 equals signs)
        failure_blocks = re.findall(r"_{3,}\s*(test_[a-zA-Z0-9_]+)\s*_{3,}(.*?)(?=(?:_{3,}|\Z|={5,}))", combined, re.DOTALL)
        for test_name, block in failure_blocks:
            exc_match = re.search(r"([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception)):?\s*(.*)", block)
            if exc_match:
                exc_type = exc_match.group(1)
                exc_msg = exc_match.group(2).strip()
            elif "assert " in block or "\nassert" in block or "AssertionError" in block:
                exc_type = "AssertionError"
                assert_match = re.search(r"assert\s+(.*)", block)
                exc_msg = assert_match.group(0).strip() if assert_match else "Assertion failed"
            else:
                exc_type = "TestFailure"
                exc_msg = "Test assertion or runtime failure"

            # Locate relevant file and line from traceback
            file_path, line_no = None, None
            file_matches = re.findall(r"([a-zA-Z0-9_\-\\\/\.]+\.py):(\d+):", block)
            for f_match, l_match in reversed(file_matches):
                candidate_path = Path(f_match)
                if not candidate_path.is_absolute():
                    candidate_path = (workspace / candidate_path).resolve()
                if candidate_path.exists() and "test_" not in candidate_path.name:
                    file_path = str(candidate_path)
                    line_no = int(l_match)
                    break

            failures.append(
                TestFailure(
                    test_id=test_name,
                    exception_type=exc_type,
                    message=exc_msg,
                    stack_trace=block.strip(),
                    file_path=file_path,
                    line_number=line_no,
                )
            )

        return failures
