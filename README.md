# THE MACHINE

> **An Autonomous Program Repair, Fault Localization, and Self-Improving Reliability Engine**

The Machine is a research-driven software engineering system designed to automatically understand software failures, localize root causes, synthesize candidate repairs, rigorously validate candidate patches against regressions and anti-patterns, and improve its repair policies through historical outcomes.

```
       +-------------+
       | Understand  |
       +------+------+
              |
              v
       +-------------+
       |  Diagnose   |
       +------+------+
              |
              v
       +-------------+
       |   Repair    |
       +------+------+
              |
              v
       +-------------+
       |   Verify    |
       +------+------+
              |
              v
       +-------------+
       |    Learn    |
       +------+------+
              |
              v
       +-------------+
       |   Repeat    |
       +-------------+
```

---

## Capabilities & Architecture

- **Controlled Fault Injection:** Systematic AST-level mutation operators (Comparison Operators, Boolean Inversion, Boundary Off-by-One, Constant Substitutions, Null-Handling Guards).
- **Execution Sandboxing & Failure Detection:** Subprocess test execution isolating target code with strict timeouts and output sanitization.
- **Spectrum-Based Fault Localization (SBFL):** Diagnostic ranking leveraging stack-trace slicing and the Ochiai suspiciousness coefficient.
- **Stratified Repair Engine:** Deterministic transformation templates and AST-search repair strategies behind a unified repair interface.
- **Non-Overfitting Validation Engine:** Rigorous invariant checking verifying target test resolution, 100% regression suite pass, AST syntactic soundness, and anti-triviality heuristics (rejects dummy stubs, deleted assertions, and silenced exceptions).
- **Relational Experiment Storage:** Append-only SQLite experiment ledger capturing mutations, diagnostics, candidate diffs, and validation outcomes.
- **Dual-Loop Self-Improvement:**
  - *Loop 1:* Target software repair.
  - *Loop 2:* Empirical meta-learning and heuristic calibration governed by human sign-off gates.

---

## Quickstart

### 1. Prerequisites
- Python 3.11+ (Python 3.14 compatible)
- Git 2.40+

### 2. Setup
Create a virtual environment and install dependencies:

```bash
# Using the local environment
.\.venv\Scripts\python.exe -m pip install -e .
```

### 3. Run Core Test Suite
Verify that all unit and integration tests pass:

```bash
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### 4. Run the Phase 1 End-to-End Demonstration
Execute a complete automated repair cycle against the built-in deterministic benchmark:

```bash
.\.venv\Scripts\python.exe -m the_machine.cli demo
```

The CLI will:
1. Spin up an isolated disposable workspace.
2. Inject a controlled boundary condition fault into `benchmarks/calculator`.
3. Detect the failing test via sandboxed subprocess execution.
4. Localize the suspicious statement via execution trace analysis.
5. Generate candidate repair patches using deterministic repair strategies.
6. Validate the candidate against the target failure and regression test suite.
7. Record the trial in SQLite (`experiments.db`).
8. Safely restore the workspace to a pristine state.

---

## Documentation

- [System Architecture](file:///docs/ARCHITECTURE.md): Detailed module specifications, contracts, and data flow.
- [Research Plan](file:///docs/RESEARCH_PLAN.md): Research questions, hypotheses, formal metrics, and validity threats.
- [Engineering Roadmap](file:///docs/ROADMAP.md): Phased development milestones from Phase 0 to Phase 9.
- [Safety & Isolation Boundaries](file:///docs/SAFETY.md): Sandboxing rules, trust models, and self-modification governance.
- [Experiment Methodology](file:///docs/EXPERIMENTS.md): Relational schema and reproducibility protocol.

---

## Limitations

- The initial implementation focuses on deterministic Python micro-benchmarks.
- Subprocess execution enforces timeouts and clean environments, but full kernel containerization (e.g., Docker/Podman) is planned for Phase 5.
- Loop 2 self-improvement currently operates in recommendation and calibration mode; automated code promotion is restricted by human approval gates.
