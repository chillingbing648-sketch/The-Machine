"""Integration test verifying end-to-end repair cycle on the Inventory benchmark."""

from pathlib import Path
from the_machine.core.database import ExperimentDatabase
from the_machine.core.models import ExperimentConfig, ExperimentStatus
from the_machine.engine.experiment_manager import ExperimentManager


def test_inventory_benchmark_e2e(tmp_path: Path):
    target_dir = Path("benchmarks/inventory").resolve()
    db_path = tmp_path / "inventory_test.db"
    db = ExperimentDatabase(str(db_path))

    workspace_base = tmp_path / "workspaces"
    manager = ExperimentManager(base_workspace_dir=workspace_base, db=db)

    config = ExperimentConfig(
        target_name="inventory_benchmark",
        target_rel_path="inventory.py",
        test_rel_path="test_inventory.py",
        timeout_sec=60.0,
        max_candidates=15,
        enabled_strategies=["deterministic_template", "search_ast"],
    )

    summary = manager.run_repair_cycle(
        target_dir=target_dir,
        config=config,
        operator_name="COM",
        mutation_line=51,  # quantity <= 0 guard in restock()
        cleanup_after=True,
    )

    assert summary.status == ExperimentStatus.REPAIRED
    assert summary.mutation is not None
    assert summary.baseline_report is not None
    assert summary.baseline_report.passed is False
    assert len(summary.suspicious_locations) > 0

    # Localization accuracy evaluation
    if summary.localization_metrics:
        assert summary.localization_metrics.top_5 is True
        assert summary.localization_metrics.reciprocal_rank > 0.0

    assert summary.accepted_patch is not None
    assert summary.accepted_validation is not None
    assert summary.accepted_validation.failing_test_passed is True
    assert summary.accepted_validation.regression_tests_passed is True

    # Canonical source preservation check
    canonical_code = (target_dir / "inventory.py").read_text(encoding="utf-8")
    assert "quantity <= 0" in canonical_code
