"""Unit tests for the Validation Engine."""

from pathlib import Path
from the_machine.core.models import PatchCandidate, ValidationStatus
from the_machine.engine.validation_engine import ValidationEngine


def test_reject_patch_modifying_test_file(tmp_path: Path):
    engine = ValidationEngine()
    test_patch = PatchCandidate(
        candidate_id="cand_1",
        strategy_name="test_strat",
        file_path=str(tmp_path / "test_suite.py"),
        line_number=10,
        original_code="assert False",
        replacement_code="assert True",
        diff="--- a\n+++ b",
        explanation="Modify test",
    )

    result = engine.validate_patch(test_patch, tmp_path)
    assert result.status == ValidationStatus.ANTI_PATTERN
    assert result.anti_pattern_detected is True


def test_reject_anti_pattern_exception_silencing(tmp_path: Path):
    engine = ValidationEngine()
    dummy_file = tmp_path / "logic.py"
    dummy_file.write_text("x = 1\n", encoding="utf-8")

    patch = PatchCandidate(
        candidate_id="cand_2",
        strategy_name="test_strat",
        file_path=str(dummy_file),
        line_number=1,
        original_code="x = 1",
        replacement_code="try:\n    x = 1\nexcept Exception:\n    pass",
        diff="--- a\n+++ b",
        explanation="Silence error",
    )

    result = engine.validate_patch(patch, tmp_path)
    assert result.status == ValidationStatus.ANTI_PATTERN
    assert result.anti_pattern_detected is True


def test_reject_syntax_error_patch(tmp_path: Path):
    engine = ValidationEngine()
    logic_file = tmp_path / "app.py"
    logic_file.write_text("val = 10\n", encoding="utf-8")

    patch = PatchCandidate(
        candidate_id="cand_3",
        strategy_name="test_strat",
        file_path=str(logic_file),
        line_number=1,
        original_code="val = 10",
        replacement_code="val = def broken(",
        diff="--- a\n+++ b",
        explanation="Syntax error",
    )

    result = engine.validate_patch(patch, tmp_path)
    assert result.status == ValidationStatus.SYNTAX_ERROR
    assert result.syntax_valid is False
