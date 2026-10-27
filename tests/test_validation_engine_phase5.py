"""Comprehensive tests for Phase 5: Robust Validation, Anti-Triviality, and Flakiness Sandboxing."""

from pathlib import Path
from the_machine.core.models import (
    PatchCandidate,
    TestExecutionReport,
    TestFailure,
    ValidationStatus,
)
from the_machine.engine.validation_engine import (
    AntiTrivialityChecker,
    FlakinessDetector,
    ValidationEngine,
)


def test_anti_triviality_scope_checking():
    checker = AntiTrivialityChecker()
    valid_path = Path("src/services/billing.py")
    test_path_1 = Path("tests/test_billing.py")
    test_path_2 = Path("unit_tests/billing_test.py")

    ok, _ = checker.check_scope(valid_path)
    assert ok is True

    ok1, msg1 = checker.check_scope(test_path_1)
    assert ok1 is False
    assert "test suite" in msg1

    ok2, msg2 = checker.check_scope(test_path_2)
    assert ok2 is False


def test_anti_triviality_assertion_deletion():
    checker = AntiTrivialityChecker()
    orig = "assert account.balance >= 0"
    rep = "account.balance >= 0"  # assert stripped!

    ok, msg = checker.check_code_invariants(orig, rep)
    assert ok is False
    assert "assertion" in msg.lower()


def test_anti_triviality_exception_silencing():
    checker = AntiTrivialityChecker()
    orig = "result = query_db()"
    rep = "try:\n    result = query_db()\nexcept Exception:\n    pass"

    ok, msg = checker.check_code_invariants(orig, rep)
    assert ok is False
    assert "suppresses exceptions" in msg.lower()


def test_anti_triviality_function_stubbing():
    checker = AntiTrivialityChecker()
    orig = "def compute_tax(amount):\n    return amount * 0.18"
    rep = "def compute_tax(amount):\n    pass"

    ok, msg = checker.check_code_invariants(orig, rep)
    assert ok is False
    assert "empty 'pass' stub" in msg.lower()


def test_flakiness_detector_stable_behavior():
    class MockStableDetector:
        def run_tests(self, workspace, test_target=None, timeout_sec=60.0):
            return TestExecutionReport(passed=True, total_tests=5, passed_tests=5, failed_tests=0)

    detector = FlakinessDetector(MockStableDetector())
    is_stable, passed_runs, total_runs = detector.verify_stability(Path("."), runs=3)
    assert is_stable is True
    assert passed_runs == 3
    assert total_runs == 3


def test_flakiness_detector_catches_non_deterministic_failure():
    class MockFlakyDetector:
        def __init__(self):
            self.calls = 0

        def run_tests(self, workspace, test_target=None, timeout_sec=60.0):
            self.calls += 1
            # First run passes, second run fails
            passed = self.calls == 1
            return TestExecutionReport(
                passed=passed,
                total_tests=5,
                passed_tests=5 if passed else 4,
                failed_tests=0 if passed else 1,
            )

    detector = FlakinessDetector(MockFlakyDetector())
    is_stable, passed_runs, total_runs = detector.verify_stability(Path("."), runs=2)
    assert is_stable is False
    assert passed_runs == 1
    assert total_runs == 2


def test_validation_engine_rejects_flaky_patch(tmp_path: Path):
    target_file = tmp_path / "flaky_worker.py"
    target_file.write_text("def run_job(x):\n    return x + 1\n", encoding="utf-8")

    class SemiFlakyDetector:
        def __init__(self):
            self.count = 0

        def run_tests(self, workspace, test_target=None, timeout_sec=60.0):
            self.count += 1
            # Passes initial test target and first regression run, but fails second regression run
            passed = (self.count <= 2)
            return TestExecutionReport(
                passed=passed,
                total_tests=3,
                passed_tests=3 if passed else 2,
                failed_tests=0 if passed else 1,
            )

    engine = ValidationEngine(failure_detector=SemiFlakyDetector())
    candidate = PatchCandidate(
        candidate_id="cand_flaky",
        strategy_name="deterministic_template",
        file_path=str(target_file),
        line_number=2,
        original_code="return x + 1",
        replacement_code="return x + 2",
        diff="--- a\n+++ b\n",
        explanation="Test candidate",
    )

    result = engine.validate_patch(
        candidate=candidate,
        workspace_path=tmp_path,
        failing_test_id="test_job",
        verify_flakiness=True,
        flakiness_runs=2,
    )

    assert result.status == ValidationStatus.REGRESSED
    assert result.is_flaky is True
    assert "Flaky patch detected" in result.message
