"""Unit tests for the CoverageCollector engine."""

from pathlib import Path
from the_machine.engine.coverage_collector import CoverageCollector


def test_coverage_collector_builds_matrix():
    collector = CoverageCollector()
    workspace = Path("benchmarks/calculator").resolve()
    matrix = collector.collect_matrix(
        workspace_path=workspace,
        target_rel_path="calculator.py",
        test_rel_path="test_calculator.py",
        failing_tests=set(),
    )

    assert matrix.total_passing_tests > 0
    assert matrix.total_failing_tests == 0
    assert len(matrix.spectrum) > 0
    # Every line has (ef, ep, nf, np)
    for line, (ef, ep, nf, np) in matrix.spectrum.items():
        assert ef >= 0
        assert ep >= 0
        assert nf >= 0
        assert np >= 0
        assert ef + nf == matrix.total_failing_tests
        assert ep + np == matrix.total_passing_tests
