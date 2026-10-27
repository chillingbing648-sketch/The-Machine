"""Unit tests for Fault Localization Engine."""

from pathlib import Path
from the_machine.core.models import TestExecutionReport, TestFailure
from the_machine.engine.fault_localizer import FaultLocalizer


def test_fault_localizer_extracts_stack_frames(tmp_path: Path):
    source_file = tmp_path / "module.py"
    source_file.write_text(
        """
def compute(x):
    if x > 10:
        raise ValueError("Invalid")
    return x
""".strip(),
        encoding="utf-8",
    )

    report = TestExecutionReport(
        passed=False,
        total_tests=1,
        passed_tests=0,
        failed_tests=1,
        failures=[
            TestFailure(
                test_id="test_compute",
                exception_type="ValueError",
                message="Invalid",
                stack_trace=f"File {source_file}:3: in compute\n> raise ValueError",
                file_path=str(source_file),
                line_number=3,
            )
        ],
    )

    localizer = FaultLocalizer(workspace_path=tmp_path)
    locations = localizer.localize_fault(report, workspace_path=tmp_path)

    assert len(locations) >= 1
    top = locations[0]
    assert top.line_number == 3
    assert top.score == 1.0
    assert "Direct target" in top.evidence or "Stack frame" in top.evidence
