"""End-to-End Integration Test for The Machine Repair Pipeline."""

from pathlib import Path
from the_machine.core.database import ExperimentDatabase
from the_machine.core.models import ExperimentConfig, ExperimentStatus
from the_machine.engine.experiment_manager import ExperimentManager


def test_end_to_end_repair_pipeline(tmp_path: Path):
    target_dir = Path("benchmarks/calculator").resolve()
    db_path = tmp_path / "e2e_experiments.db"
    db = ExperimentDatabase(str(db_path))

    workspace_base = tmp_path / "test_workspaces"
    manager = ExperimentManager(base_workspace_dir=workspace_base, db=db)

    config = ExperimentConfig(
        target_name="calculator_e2e",
        target_rel_path="calculator.py",
        test_rel_path="test_calculator.py",
        timeout_sec=10.0,
        random_seed=42,
        max_candidates=5,
        enabled_strategies=["deterministic_template", "search_ast"],
    )

    summary = manager.run_repair_cycle(
        target_dir=target_dir,
        config=config,
        operator_name="COM",
        mutation_line=25,
        cleanup_after=True,
    )

    # Invariants verification
    assert summary.status == ExperimentStatus.REPAIRED
    assert summary.mutation is not None
    assert summary.mutation.operator == "COMPARISON_OPERATOR"
    assert summary.baseline_report is not None
    assert summary.baseline_report.passed is False
    assert len(summary.suspicious_locations) > 0
    assert summary.accepted_patch is not None
    assert summary.accepted_validation is not None
    assert summary.accepted_validation.failing_test_passed is True
    assert summary.accepted_validation.regression_tests_passed is True

    # Database verification
    db_exp = db.get_experiment(summary.experiment_id)
    assert db_exp is not None
    assert db_exp["experiment"]["status"] == "REPAIRED"
    assert len(db_exp["patches"]) >= 1

    # Non-destructive guarantee: canonical target must be untouched
    canonical_calc = (target_dir / "calculator.py").read_text(encoding="utf-8")
    assert "b == 0" in canonical_calc
