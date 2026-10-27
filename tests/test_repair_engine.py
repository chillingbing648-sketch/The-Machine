"""Unit tests for the Repair Engine."""

from pathlib import Path
from the_machine.core.models import SuspiciousLocation, TestExecutionReport
from the_machine.engine.repair_engine import DeterministicTemplateStrategy, RepairEngine


def test_deterministic_template_inverts_comparison(tmp_path: Path):
    source_file = tmp_path / "calc.py"
    source_file.write_text(
        """
def check(val, bound):
    if val <= bound:
        return True
    return False
""".strip(),
        encoding="utf-8",
    )

    location = SuspiciousLocation(
        file_path=str(source_file),
        line_number=2,
        score=1.0,
        evidence="Stack frame",
    )

    report = TestExecutionReport(passed=False, total_tests=1, passed_tests=0, failed_tests=1)
    strategy = DeterministicTemplateStrategy()
    candidates = strategy.generate_patches(location, report, tmp_path)

    assert len(candidates) > 0
    # Should contain < replacement
    replacements = [c.replacement_code for c in candidates]
    assert any("<" in rep for rep in replacements)


def test_repair_engine_synthesizes_unique_candidates(tmp_path: Path):
    source_file = tmp_path / "ops.py"
    source_file.write_text(
        """
def boundary(a, b):
    if a < b:
        return 0
    return 1
""".strip(),
        encoding="utf-8",
    )

    location = SuspiciousLocation(
        file_path=str(source_file),
        line_number=2,
        score=1.0,
        evidence="Direct",
    )

    engine = RepairEngine()
    report = TestExecutionReport(passed=False, total_tests=1, passed_tests=0, failed_tests=1)
    patches = engine.synthesize_candidates([location], report, tmp_path, max_candidates=5)

    assert len(patches) > 0
    diffs = [p.diff for p in patches]
    assert len(diffs) == len(set(diffs))  # No duplicate patches
