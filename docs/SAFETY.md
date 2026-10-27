# Safety & Isolation Boundaries — THE MACHINE

## 1. Threat Model & Principles

In Automated Program Repair, synthesized code patches and target programs must be treated as **untrusted input**. An unconstrained repair agent could:
1. Introduce infinite recursion, blocking system calls, or memory exhaustion.
2. Silently tamper with test suites to make assertions vacuously true (`assert True`).
3. Delete, overwrite, or corrupt the user's primary repository source code.
4. Exfiltrate environment secrets or sensitive file paths.
5. In a self-improving regime, corrupt the repair engine's own runtime.

The Machine implements multi-layered defensive controls to mitigate these risks.

---

## 2. Workspace & File System Isolation

- **Non-Destructive Guarantee:** Canonical source code is never modified directly.
- **Disposable Workspaces:** Every experiment creates an isolated copy under `.machine_workspaces/<experiment_id>` or a temporary directory. All mutations, patch applications, and validations are confined to this ephemeral directory.
- **Path Confinement:** The validation engine verifies that any proposed patch file path resolves strictly within the configured target workspace subtree. Attempts to escape via relative paths (`../`) or absolute paths outside the sandbox are immediately rejected.
- **Automatic Rollback & Cleanup:** On test conclusion, failure, or process abort, workspaces are pruned or reset.

---

## 3. Subprocess Execution & Resource Limits

All test and validation executions run inside detached subprocesses:
- **Strict Wall-Clock Timeout:** Subprocesses are terminated with `SIGKILL` (or `taskkill /F` on Windows) if they exceed the configured execution budget (default: 10.0 seconds).
- **Environment Scrubbing:** Environment variables passed to target executions are stripped of sensitive tokens, AWS keys, API credentials, and administrative shell variables.
- **Shell Avoidance:** Commands are passed as structured argument lists (`sys.executable, "-m", "pytest", ...`) rather than evaluated through `shell=True`, eliminating shell injection risks.

---

## 4. Anti-Triviality & Anti-Overfitting Patch Filters

A candidate patch is rejected by the validation engine if it exhibits any of the following anti-patterns:
1. **Assertion Removal / Modification:** The patch alters any file matching `test_*.py` or containing test assertions. Patches may only alter designated application source files.
2. **Exception Silencing:** The patch introduces empty `except:` or `except Exception: pass` blocks around the failing logic without substantive remediation.
3. **Empty Function Stubbing:** The patch replaces function bodies with unconditional `return None`, `pass`, or dummy constants unless explicitly permitted by specification.
4. **Regression Introduction:** The patch resolves the target failing test but causes one or more existing tests in the suite to fail.

---

## 5. Self-Improvement & Meta-Repair Governance

When The Machine evaluates potential improvements to its own codebase (Loop 2):
1. **Isolated Branch Execution:** Changes must be generated on a dedicated `machine-candidate-*` git branch or separate worktree.
2. **Complete Self-Test Gate:** The entire regression test suite of The Machine itself must pass with 100% success.
3. **Hypothesis & Metric Verification:** The candidate revision must demonstrate measurable statistical superiority on the benchmark suite over the existing baseline.
4. **Mandatory Human Signoff:** Under no circumstances does The Machine merge, tag, or deploy its own modifications without explicit human operator confirmation.
