"""Unit tests and regression suite for the Calculator benchmark target."""

import pytest
try:
    from calculator import (
        add,
        subtract,
        multiply,
        divide,
        is_even,
        factorial,
        clamp,
    )
except ModuleNotFoundError:
    from benchmarks.calculator.calculator import (
        add,
        subtract,
        multiply,
        divide,
        is_even,
        factorial,
        clamp,
    )


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5
    assert subtract(4, 4) == 0


def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6
    assert multiply(0, 100) == 0


def test_divide_valid():
    assert divide(10, 2) == 5.0
    assert divide(7, 2) == 3.5


def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)


def test_is_even():
    assert is_even(4) is True
    assert is_even(7) is False
    assert is_even(0) is True
    assert is_even(-2) is True
    assert is_even(-3) is False


def test_factorial_base_cases():
    assert factorial(0) == 1
    assert factorial(1) == 1


def test_factorial_positive():
    assert factorial(3) == 6
    assert factorial(5) == 120


def test_factorial_negative():
    with pytest.raises(ValueError, match="not defined for negative"):
        factorial(-1)


def test_clamp_within_bounds():
    assert clamp(5, 0, 10) == 5
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10


def test_clamp_below_min():
    assert clamp(-5, 0, 10) == 0


def test_clamp_above_max():
    assert clamp(15, 0, 10) == 10


def test_clamp_invalid_bounds():
    with pytest.raises(ValueError, match="cannot be greater"):
        clamp(5, 10, 0)
