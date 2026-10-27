"""Comprehensive tests for Phase 4: Multi-Strategy Repair Engine & Neural Adapters."""

import ast
from pathlib import Path
from the_machine.core.models import (
    PatchCandidate,
    SuspiciousLocation,
    TestExecutionReport,
    TestFailure,
)
from the_machine.engine.repair_engine import (
    DeterministicTemplateStrategy,
    SearchBasedASTStrategy,
    NeuralRepairStrategy,
    MockLLMProvider,
    OpenAILikeProvider,
    RepairEngine,
)


def test_deterministic_template_arithmetic_substitution(tmp_path: Path):
    source_file = tmp_path / "calc.py"
    source_file.write_text(
        "def subtract(a, b):\n    return a + b\n",
        encoding="utf-8",
    )
    strategy = DeterministicTemplateStrategy()
    location = SuspiciousLocation(
        file_path=str(source_file),
        line_number=2,
        score=1.0,
        evidence="Test failure in subtraction",
    )
    report = TestExecutionReport(passed=False, total_tests=1, passed_tests=0, failed_tests=1)

    patches = strategy.generate_patches(location, report, tmp_path)
    assert len(patches) > 0
    # One patch should substitute + with -
    has_sub = any("a - b" in p.diff for p in patches)
    assert has_sub, "Expected arithmetic template to propose 'a - b'"


def test_deterministic_template_boolean_inversion(tmp_path: Path):
    source_file = tmp_path / "auth.py"
    source_file.write_text(
        "def is_admin(user):\n    return False\n",
        encoding="utf-8",
    )
    strategy = DeterministicTemplateStrategy()
    location = SuspiciousLocation(
        file_path=str(source_file),
        line_number=2,
        score=1.0,
        evidence="Admin auth check failed",
    )
    report = TestExecutionReport(passed=False, total_tests=1, passed_tests=0, failed_tests=1)

    patches = strategy.generate_patches(location, report, tmp_path)
    assert len(patches) > 0
    has_true = any("True" in p.replacement_code for p in patches)
    assert has_true


def test_deterministic_template_off_by_one(tmp_path: Path):
    source_file = tmp_path / "bounds.py"
    source_file.write_text(
        "def get_index(offset):\n    return offset + 1\n",
        encoding="utf-8",
    )
    strategy = DeterministicTemplateStrategy()
    location = SuspiciousLocation(
        file_path=str(source_file),
        line_number=2,
        score=1.0,
        evidence="Index out of bounds",
    )
    report = TestExecutionReport(passed=False, total_tests=1, passed_tests=0, failed_tests=1)

    patches = strategy.generate_patches(location, report, tmp_path)
    assert len(patches) > 0
    has_zero_or_two = any("offset + 0" in p.diff or "offset + 2" in p.diff for p in patches)
    assert has_zero_or_two


def test_search_based_ast_strategy_explores_comparators(tmp_path: Path):
    source_file = tmp_path / "guard.py"
    source_file.write_text(
        "def check(x):\n    if x > 10:\n        return True\n    return False\n",
        encoding="utf-8",
    )
    strategy = SearchBasedASTStrategy()
    location = SuspiciousLocation(
        file_path=str(source_file),
        line_number=2,
        score=1.0,
        evidence="Boundary condition error",
    )
    report = TestExecutionReport(passed=False, total_tests=1, passed_tests=0, failed_tests=1)

    patches = strategy.generate_patches(location, report, tmp_path)
    assert len(patches) > 0
    # Must propose multiple comparator variations (>=, ==, <, etc.)
    comp_ops = [p.explanation for p in patches if "AST Search" in p.explanation]
    assert len(comp_ops) >= 3


def test_neural_repair_strategy_with_mock_provider(tmp_path: Path):
    source_file = tmp_path / "math_ops.py"
    source_file.write_text(
        "def divide(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    mock_provider = MockLLMProvider({
        "divide": "return a / b",
    })
    strategy = NeuralRepairStrategy(provider=mock_provider)
    location = SuspiciousLocation(
        file_path=str(source_file),
        line_number=2,
        score=0.9,
        evidence="ZeroDivision or wrong result",
    )
    report = TestExecutionReport(
        passed=False,
        total_tests=1,
        passed_tests=0,
        failed_tests=1,
        failures=[TestFailure(test_id="test_divide", exception_type="AssertionError", message="10 != 5", stack_trace="")],
    )

    patches = strategy.generate_patches(location, report, tmp_path)
    assert len(patches) == 1
    assert patches[0].strategy_name == "neural_llm"
    assert "return a / b" in patches[0].replacement_code
    assert "a / b" in patches[0].diff


def test_neural_repair_strategy_rejects_malformed_syntax(tmp_path: Path):
    source_file = tmp_path / "bad.py"
    source_file.write_text(
        "def broken():\n    return 1\n",
        encoding="utf-8",
    )
    mock_provider = MockLLMProvider({
        "broken": "def def def syntax error",
    })
    strategy = NeuralRepairStrategy(provider=mock_provider)
    location = SuspiciousLocation(
        file_path=str(source_file),
        line_number=2,
        score=0.9,
        evidence="Failure",
    )
    report = TestExecutionReport(passed=False, total_tests=1, passed_tests=0, failed_tests=1)

    patches = strategy.generate_patches(location, report, tmp_path)
    assert len(patches) == 0, "Syntactically invalid neural output must be rejected"


def test_repair_engine_coordinates_and_deduplicates(tmp_path: Path):
    source_file = tmp_path / "service.py"
    source_file.write_text(
        "def validate_age(age):\n    if age < 18:\n        return False\n    return True\n",
        encoding="utf-8",
    )
    engine = RepairEngine()
    location = SuspiciousLocation(
        file_path=str(source_file),
        line_number=2,
        score=1.0,
        evidence="Age validation off-by-one",
    )
    report = TestExecutionReport(passed=False, total_tests=1, passed_tests=0, failed_tests=1)

    candidates = engine.synthesize_candidates(
        locations=[location],
        report=report,
        workspace_path=tmp_path,
        max_candidates=8,
    )

    assert len(candidates) > 0
    assert len(candidates) <= 8

    # Ensure all diffs in candidate set are unique
    diffs = [c.diff for c in candidates]
    assert len(diffs) == len(set(diffs)), "Engine must de-duplicate identical diffs"
