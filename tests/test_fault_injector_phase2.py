"""Unit tests for Phase 2 generalized fault injection operators and mutation cataloguing."""

import pytest
from pathlib import Path
from the_machine.engine.failure_detector import FailureDetector
from the_machine.engine.fault_injector import FaultInjector


@pytest.fixture
def target_file(tmp_path: Path) -> Path:
    code = """
def check_item(item):
    if item is None:
        return 0
    item.stock -= 1
    return item.stock
"""
    p = tmp_path / "target.py"
    p.write_text(code.strip(), encoding="utf-8")
    return p


def test_null_guard_removal_mutation(target_file: Path):
    injector = FaultInjector(allowed_paths=[str(target_file.parent)])
    record = injector.inject_mutation(target_file, operator_name="NGR", target_line=2)

    assert record.operator == "NULL_GUARD_REMOVAL"
    content = target_file.read_text(encoding="utf-8")
    assert "is not None" in content


def test_statement_deletion_mutation(target_file: Path):
    injector = FaultInjector(allowed_paths=[str(target_file.parent)])
    record = injector.inject_mutation(target_file, operator_name="SDR", target_line=4)

    assert record.operator == "STATEMENT_DELETION"
    content = target_file.read_text(encoding="utf-8")
    assert "pass" in content


def test_catalogue_all_mutations(target_file: Path):
    injector = FaultInjector(allowed_paths=[str(target_file.parent)])
    catalog = injector.catalogue_all_mutations(target_file)

    assert len(catalog) >= 2
    op_keys = [c["operator_key"] for c in catalog]
    assert "NGR" in op_keys
    assert "SDR" in op_keys
