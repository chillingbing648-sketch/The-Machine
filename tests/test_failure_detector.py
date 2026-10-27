"""Unit tests for the Failure Detection Engine."""

import pytest
from pathlib import Path
from the_machine.engine.failure_detector import FailureDetector


def test_failure_detector_on_passing_target():
    detector = FailureDetector()
    workspace = Path("benchmarks/calculator").resolve()
    report = detector.run_tests(workspace, test_target="test_calculator.py::test_add")

    assert report.passed is True
    assert report.total_tests >= 1
    assert report.failed_tests == 0
    assert len(report.failures) == 0


def test_failure_detector_on_failing_target(tmp_path: Path):
    test_file = tmp_path / "test_dummy.py"
    test_file.write_text(
        """
def test_will_fail():
    assert 1 == 2
""",
        encoding="utf-8",
    )

    detector = FailureDetector()
    report = detector.run_tests(tmp_path, test_target="test_dummy.py")

    assert report.passed is False
    assert report.failed_tests == 1
    assert len(report.failures) == 1
    assert report.failures[0].test_id == "test_will_fail"
    assert "AssertionError" in report.failures[0].exception_type


def test_failure_detector_timeout(tmp_path: Path):
    test_file = tmp_path / "test_hang.py"
    test_file.write_text(
        """
import time
def test_sleep_forever():
    time.sleep(5)
""",
        encoding="utf-8",
    )

    detector = FailureDetector()
    report = detector.run_tests(tmp_path, test_target="test_hang.py", timeout_sec=0.5)

    assert report.passed is False
    assert report.timed_out is True
