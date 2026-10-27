"""Deterministic Calculator target module for automated program repair benchmarking."""

from typing import Union

Number = Union[int, float]


def add(a: Number, b: Number) -> Number:
    """Add two numbers."""
    return a + b


def subtract(a: Number, b: Number) -> Number:
    """Subtract b from a."""
    return a - b


def multiply(a: Number, b: Number) -> Number:
    """Multiply two numbers."""
    return a * b


def divide(a: Number, b: Number) -> float:
    """Divide a by b with division by zero guard."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def is_even(n: int) -> bool:
    """Return True if n is an even integer."""
    return n % 2 == 0


def factorial(n: int) -> int:
    """Compute factorial for non-negative integers."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative integers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)


def clamp(value: Number, min_val: Number, max_val: Number) -> Number:
    """
    Constrain value within [min_val, max_val].
    Raises ValueError if min_val > max_val.
    """
    if min_val > max_val:
        raise ValueError("min_val cannot be greater than max_val")
    if value < min_val:
        return min_val
    elif value > max_val:
        return max_val
    return value
