"""Unit tests for the Fault Injection Engine."""

import pytest
from pathlib import Path
from the_machine.engine.fault_injector import FaultInjector


@pytest.fixture
def sample_code_file(tmp_path: Path) -> Path:
    code = """
def check_boundary(x: int) -> bool:
    if x < 10:
        return True
    return False
"""
    file_path = tmp_path / "sample.py"
    file_path.write_text(code.strip(), encoding="utf-8")
    return file_path


def test_comparison_operator_mutation(sample_code_file: Path):
    injector = FaultInjector(allowed_paths=[str(sample_code_file.parent)])
    record = injector.inject_mutation(sample_code_file, operator_name="COM")

    assert record.operator == "COMPARISON_OPERATOR"
    assert "x <= 10" in sample_code_file.read_text(encoding="utf-8") or "<=" in record.mutated_code


def test_boundary_off_by_one_mutation(sample_code_file: Path):
    injector = FaultInjector(allowed_paths=[str(sample_code_file.parent)])
    record = injector.inject_mutation(sample_code_file, operator_name="OB1", target_line=2)

    assert record.operator == "BOUNDARY_OFF_BY_ONE"
    mutated = sample_code_file.read_text(encoding="utf-8")
    assert "11" in mutated


def test_unauthorized_path_rejected(tmp_path: Path):
    disallowed_file = tmp_path / "unauthorized.py"
    disallowed_file.write_text("x = 1", encoding="utf-8")

    injector = FaultInjector(allowed_paths=["/some/other/path"])
    with pytest.raises(PermissionError):
        injector.inject_mutation(disallowed_file, operator_name="COM")
