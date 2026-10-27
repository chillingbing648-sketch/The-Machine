"""Standalone SBFL execution tracer invoked as a subprocess."""

import json
import os
import sys
from pathlib import Path
import pytest


class SpectrumTracerPlugin:
    """Pytest plugin hooking test execution and tracing statement hits."""

    def __init__(self, target_file_path: Path):
        self.target_file_path = target_file_path.resolve()
        self.lines_by_test = {}
        self.outcomes_by_test = {}
        self.current_test_name = None

    def pytest_runtest_call(self, item):
        self.current_test_name = item.name
        self.lines_by_test[item.name] = set()

        def trace_lines(frame, event, arg):
            if event == "line":
                try:
                    f = Path(frame.f_code.co_filename).resolve()
                    if f == self.target_file_path:
                        self.lines_by_test[item.name].add(frame.f_lineno)
                except Exception:
                    pass
            return trace_lines

        sys.settrace(trace_lines)

    def pytest_runtest_teardown(self, item, nextitem):
        sys.settrace(None)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        rep = outcome.get_result()
        if rep.when == "call":
            self.outcomes_by_test[item.name] = (rep.outcome == "passed")


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python -m the_machine.engine.sbfl_tracer <target_file> <test_file>")
        sys.exit(1)

    target_file = Path(sys.argv[1]).resolve()
    test_file = Path(sys.argv[2]).resolve()
    workspace = test_file.parent.resolve()

    if str(workspace) not in sys.path:
        sys.path.insert(0, str(workspace))

    plugin = SpectrumTracerPlugin(target_file)
    pytest.main(["-v", "--tb=no", str(test_file)], plugins=[plugin])

    results = []
    for test_name, lines in plugin.lines_by_test.items():
        passed = plugin.outcomes_by_test.get(test_name, True)
        results.append({
            "test_id": test_name,
            "passed": passed,
            "executed_lines": sorted(list(lines)),
        })

    print("\n===SBFL_SPECTRUM_BEGIN===")
    print(json.dumps(results))
    print("===SBFL_SPECTRUM_END===")


if __name__ == "__main__":
    main()
