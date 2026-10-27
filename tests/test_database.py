"""Unit tests for the SQLite Database layer."""

from pathlib import Path
from the_machine.core.database import ExperimentDatabase
from the_machine.core.models import (
    ExperimentConfig,
    ExperimentStatus,
    MutationRecord,
    PatchCandidate,
    SuspiciousLocation,
    TestExecutionReport,
    ValidationResult,
    ValidationStatus,
)


def test_database_lifecycle_and_retrieval(tmp_path: Path):
    db_file = tmp_path / "test_exp.db"
    db = ExperimentDatabase(str(db_file))

    config = ExperimentConfig(
        target_name="test_target",
        target_rel_path="src/main.py",
        test_rel_path="tests/test_main.py",
    )
    exp_id = "exp_test_001"
    db.record_experiment_start(exp_id, config)

    # Record mutation
    mutation = MutationRecord(
        mutation_id="mut_001",
        operator="COM",
        file_path="src/main.py",
        line_number=5,
        original_code="a < b",
        mutated_code="a <= b",
    )
    db.record_mutation(exp_id, mutation)

    # Record diagnostic
    report = TestExecutionReport(
        passed=False,
        total_tests=5,
        passed_tests=4,
        failed_tests=1,
        duration_sec=0.2,
        exit_code=1,
    )
    db.record_diagnostic(exp_id, report)

    # Record locations
    loc = SuspiciousLocation(
        file_path="src/main.py",
        line_number=5,
        score=1.0,
        evidence="Trace",
    )
    db.record_locations(exp_id, [loc])

    # Record patch evaluation
    candidate = PatchCandidate(
        candidate_id="cand_001",
        strategy_name="deterministic_template",
        file_path="src/main.py",
        line_number=5,
        original_code="a <= b",
        replacement_code="a < b",
        diff="--- a\n+++ b",
        explanation="Invert operator",
    )
    val = ValidationResult(
        status=ValidationStatus.ACCEPTED,
        failing_test_passed=True,
        regression_tests_passed=True,
        syntax_valid=True,
        anti_pattern_detected=False,
        message="All passed",
    )
    db.record_patch_evaluation(exp_id, candidate, val)
    db.finish_experiment(exp_id, ExperimentStatus.REPAIRED, total_duration_sec=1.5)

    data = db.get_experiment(exp_id)
    assert data is not None
    assert data["experiment"]["status"] == "REPAIRED"
    assert data["mutation"]["operator"] == "COM"
    assert len(data["locations"]) == 1
    assert len(data["patches"]) == 1
    assert data["patches"][0]["validation_status"] == "ACCEPTED"
