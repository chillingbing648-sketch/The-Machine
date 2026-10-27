"""Unit tests for Spectrum-Based Fault Localization formulas and metric evaluations."""

from pathlib import Path
from the_machine.core.models import SuspiciousLocation, TestExecutionReport
from the_machine.engine.coverage_collector import CoverageMatrix
from the_machine.engine.fault_localizer import FaultLocalizer


def test_sbfl_formulas():
    localizer = FaultLocalizer()

    # Case 1: Line executed by all 2 failing tests, 0 passing tests
    # ef=2, ep=0, nf=0, np=10
    ochiai = localizer.compute_ochiai(ef=2, ep=0, nf=0, np=10)
    assert round(ochiai, 4) == 1.0

    tarantula = localizer.compute_tarantula(ef=2, ep=0, nf=0, np=10)
    assert round(tarantula, 4) == 1.0

    dstar = localizer.compute_dstar(ef=2, ep=0, nf=0, np=10)
    assert dstar == 4.0

    # Case 2: Line executed by 0 failing tests, 10 passing tests
    # ef=0, ep=10, nf=2, np=0
    assert localizer.compute_ochiai(ef=0, ep=10, nf=2, np=0) == 0.0
    assert localizer.compute_tarantula(ef=0, ep=10, nf=2, np=0) == 0.0
    assert localizer.compute_dstar(ef=0, ep=10, nf=2, np=0) == 0.0


def test_localization_accuracy_metrics():
    locations = [
        SuspiciousLocation(file_path="app.py", line_number=25, score=1.0, evidence="Ochiai"),
        SuspiciousLocation(file_path="app.py", line_number=30, score=0.8, evidence="Ochiai"),
        SuspiciousLocation(file_path="app.py", line_number=35, score=0.6, evidence="Ochiai"),
    ]

    metrics = FaultLocalizer.evaluate_localization(locations, ground_truth_line=25, window=0)
    assert metrics.ground_truth_line == 25
    assert metrics.predicted_rank == 1
    assert metrics.top_1 is True
    assert metrics.top_3 is True
    assert metrics.reciprocal_rank == 1.0

    # Line ranked #2
    metrics_rank2 = FaultLocalizer.evaluate_localization(locations, ground_truth_line=30, window=0)
    assert metrics_rank2.predicted_rank == 2
    assert metrics_rank2.top_1 is False
    assert metrics_rank2.top_3 is True
    assert metrics_rank2.reciprocal_rank == 0.5


def test_hybrid_localization_merges_matrix_and_stack(tmp_path: Path):
    source_file = tmp_path / "math_ops.py"
    source_file.write_text("x = 1\ny = 2\nz = 3\n", encoding="utf-8")

    matrix = CoverageMatrix(
        target_file=str(source_file),
        total_passing_tests=5,
        total_failing_tests=1,
        spectrum={
            1: (0, 5, 1, 0),
            2: (1, 1, 0, 4),  # High suspiciousness
            3: (0, 2, 1, 3),
        },
    )

    report = TestExecutionReport(passed=False, total_tests=6, passed_tests=5, failed_tests=1)
    localizer = FaultLocalizer(workspace_path=tmp_path)
    ranked = localizer.localize_fault(report, workspace_path=tmp_path, matrix=matrix, metric_name="ochiai")

    assert len(ranked) > 0
    # Line 2 should be ranked top
    assert ranked[0].line_number == 2
    assert "SBFL(OCHIAI" in ranked[0].evidence
