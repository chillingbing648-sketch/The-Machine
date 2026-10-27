"""Validation Engine: enforces test passage, regression safety, and anti-triviality invariants."""

import ast
import re
import time
from pathlib import Path
from typing import Optional
from the_machine.core.models import (
    PatchCandidate,
    TestExecutionReport,
    ValidationResult,
    ValidationStatus,
)
from the_machine.engine.failure_detector import FailureDetector


class ValidationEngine:
    """Evaluates candidate patches against regression suites and anti-overfitting rules."""

    def __init__(self, failure_detector: Optional[FailureDetector] = None):
        self.failure_detector = failure_detector or FailureDetector()

    def validate_patch(
        self,
        candidate: PatchCandidate,
        workspace_path: Path,
        failing_test_id: Optional[str] = None,
        timeout_sec: float = 10.0,
    ) -> ValidationResult:
        """
        Validate patch in workspace:
        1. Scope & anti-pattern verification.
        2. Syntax & AST compilation check.
        3. Application of patch to workspace.
        4. Re-run failing test.
        5. Full regression suite verification.
        6. Guaranteed workspace restoration.
        """
        start_time = time.time()
        workspace = Path(workspace_path).resolve()
        target_file = Path(candidate.file_path)

        # 1. Scope check: forbidden to touch test files
        if "test_" in target_file.name or "tests" in target_file.parts:
            return ValidationResult(
                status=ValidationStatus.ANTI_PATTERN,
                failing_test_passed=False,
                regression_tests_passed=False,
                syntax_valid=False,
                anti_pattern_detected=True,
                message="Candidate patch modifies test files, violating safety boundary",
                execution_time_sec=time.time() - start_time,
            )

        # 2. Anti-pattern detection on replacement code
        anti_pattern, reason = self._detect_anti_patterns(candidate.replacement_code)
        if anti_pattern:
            return ValidationResult(
                status=ValidationStatus.ANTI_PATTERN,
                failing_test_passed=False,
                regression_tests_passed=False,
                syntax_valid=True,
                anti_pattern_detected=True,
                message=f"Anti-pattern detected: {reason}",
                execution_time_sec=time.time() - start_time,
            )

        # 3. Syntax check
        original_content = target_file.read_text(encoding="utf-8")
        # Line-targeted replacement with word boundary protection
        lines = original_content.splitlines(keepends=True)
        target_idx = candidate.line_number - 1
        replaced = False

        search_indices = [target_idx] + [target_idx + d for d in [1, -1, 2, -2, 3, -3, 4, -4]]
        for idx in search_indices:
            if 0 <= idx < len(lines) and candidate.original_code in lines[idx]:
                pattern = r"\b" + re.escape(candidate.original_code) + r"\b"
                if re.search(pattern, lines[idx]):
                    lines[idx] = re.sub(pattern, candidate.replacement_code, lines[idx], count=1)
                    replaced = True
                    break
                else:
                    lines[idx] = lines[idx].replace(candidate.original_code, candidate.replacement_code, 1)
                    replaced = True
                    break

        if replaced:
            patched_content = "".join(lines)
        else:
            pattern = r"\b" + re.escape(candidate.original_code) + r"\b"
            if re.search(pattern, original_content):
                patched_content = re.sub(pattern, candidate.replacement_code, original_content, count=1)
            elif candidate.original_code in original_content:
                patched_content = original_content.replace(candidate.original_code, candidate.replacement_code, 1)
            else:
                return ValidationResult(
                    status=ValidationStatus.REJECTED,
                    failing_test_passed=False,
                    regression_tests_passed=False,
                    syntax_valid=False,
                    anti_pattern_detected=False,
                    message="Original code snippet not found in target file",
                    execution_time_sec=time.time() - start_time,
                )
        try:
            compile(patched_content, str(target_file), "exec")
        except SyntaxError as exc:
            return ValidationResult(
                status=ValidationStatus.SYNTAX_ERROR,
                failing_test_passed=False,
                regression_tests_passed=False,
                syntax_valid=False,
                anti_pattern_detected=False,
                message=f"Syntactically invalid patch: {exc}",
                execution_time_sec=time.time() - start_time,
            )

        # Apply patch and execute test validations
        try:
            target_file.write_text(patched_content, encoding="utf-8")

            # 4. Run failing test target (if specified)
            failing_report = None
            if failing_test_id:
                failing_report = self.failure_detector.run_tests(
                    workspace, test_target=failing_test_id, timeout_sec=timeout_sec
                )
                if not failing_report.passed:
                    return ValidationResult(
                        status=ValidationStatus.REJECTED,
                        failing_test_passed=False,
                        regression_tests_passed=False,
                        syntax_valid=True,
                        anti_pattern_detected=False,
                        message=f"Candidate patch failed to resolve target test '{failing_test_id}'",
                        failing_test_report=failing_report,
                        execution_time_sec=time.time() - start_time,
                    )

            # 5. Run full regression suite
            regression_report = self.failure_detector.run_tests(
                workspace, test_target=None, timeout_sec=timeout_sec
            )

            if regression_report.passed:
                return ValidationResult(
                    status=ValidationStatus.ACCEPTED,
                    failing_test_passed=True,
                    regression_tests_passed=True,
                    syntax_valid=True,
                    anti_pattern_detected=False,
                    message="Patch successfully verified against target defect and full regression suite",
                    failing_test_report=failing_report,
                    regression_test_report=regression_report,
                    execution_time_sec=time.time() - start_time,
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.REGRESSED,
                    failing_test_passed=True if failing_report and failing_report.passed else False,
                    regression_tests_passed=False,
                    syntax_valid=True,
                    anti_pattern_detected=False,
                    message=f"Patch introduced regressions ({regression_report.failed_tests} tests failed)",
                    failing_test_report=failing_report,
                    regression_test_report=regression_report,
                    execution_time_sec=time.time() - start_time,
                )

        finally:
            # 6. Guaranteed rollback of candidate
            target_file.write_text(original_content, encoding="utf-8")

    def _detect_anti_patterns(self, replacement_code: str) -> tuple[bool, str]:
        """Detect trivial/vacuous repair patterns."""
        try:
            tree = ast.parse(replacement_code)
        except SyntaxError:
            # Syntax errors will be caught separately
            return False, ""

        for node in ast.walk(tree):
            # Check for empty exception silencing: except ...: pass
            if isinstance(node, ast.ExceptHandler):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    return True, "Suppresses exceptions with empty 'except: pass' block"
            # Check for dummy empty function pass
            if isinstance(node, ast.FunctionDef):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    return True, "Replaces function body with empty 'pass' stub"

        return False, ""
