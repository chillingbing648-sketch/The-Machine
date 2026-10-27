# Engineering Roadmap — THE MACHINE

This roadmap outlines the systematic, phased implementation of The Machine from initial foundation to an autonomous, self-improving software reliability platform.

---

## Phase Overview & Progress Status

| Phase | Title | Focus Area | Status |
| :---: | :--- | :--- | :---: |
| **0** | Discovery & Foundation | Baseline inspection, environment setup, architecture, research docs | **COMPLETED** |
| **1** | First Functioning Slice | End-to-end pipeline: mutation, detection, localization, repair, validation, DB | **COMPLETED** |
| **2** | Generalized Fault Injection | 6 AST mutation operators, multi-target benchmarks, mutation catalog | **COMPLETED** |
| **3** | Evidence-Based SBFL | Ochiai coverage matrix, stack slicing, Top-1/Top-3/MRR metrics | **COMPLETED** |
| **4** | Multi-Strategy Repair Engine | Template library, AST bounded search, pluggable LLM adapter | Planned |
| **5** | Robust Validation & Sandboxing | Invariant checking, anti-triviality heuristics, strict resource limits | Planned |
| **6** | Empirical Strategy Selection | Contextual bandit dispatch, historical repair learning | Planned |
| **7** | Self-Improvement & Meta-Repair | Machine self-evaluation, hypothesis-driven policy updates, human approval gate | Planned |
| **8** | Research-Grade Benchmarking | Held-out validation suites, empirical papers, comparative APR evaluation | Planned |
| **9** | Observability Dashboard | Interactive visualization of experiments, diffs, telemetry, and repair traces | Planned |

---

## Milestone Acceptance Criteria

### Phase 0 — Foundation & Architecture
- [x] Environment inspected (Windows, Python 3.14.2, Git 2.54, pytest, virtualenv).
- [x] Clean repository foundation and project directory structure established.
- [x] System architecture, research plan, roadmap, safety guidelines, and experiment protocol documented.
- [x] Dependency manifests (`pyproject.toml`, `requirements.txt`) configured.

### Phase 1 — First Functioning Vertical Slice
- [x] Working deterministic target module with comprehensive test suite (`benchmarks/calculator`).
- [x] Fault injection module capable of applying a traceable mutation and recording restoration data.
- [x] Failure detector executing tests via subprocess, capturing structured failure reports.
- [x] Fault localizer ranking failure locations based on stack traces and code analysis.
- [x] Repair engine synthesizing at least one candidate patch addressing the defect.
- [x] Validation engine executing tests against the patch in an isolated workspace, verifying fix and preventing regressions.
- [x] Experiment storage recording the complete trial in SQLite (`experiments.db`).
- [x] Non-destructive restoration guaranteeing the target workspace is cleanly recovered.
- [x] Comprehensive unit and integration test suite passing locally via `pytest`.
- [x] Automated end-to-end demonstration runnable via CLI (`python -m the_machine.cli demo`).

### Phase 2 — Generalized Fault Injection
- [x] Standardized mutation operators: Comparison Operators (COM), Boolean Logic Inversion (BLI), Off-by-One (OB1), Constant/Return Substitution (CRS), Null/Guard Removal (NGR), Statement Deletion (SDR).
- [x] Mutation safety filter preventing changes outside designated targets or inside test code.
- [x] Batch mutation catalogue generator walking AST to discover all feasible mutation sites.
- [x] Multi-target benchmark suite added (`benchmarks/inventory`).

### Phase 3 — Spectrum-Based Fault Localization (SBFL)
- [x] Code coverage collection tracking per-test line execution (passing vs. failing) via `CoverageCollector` and `SpectrumTracerPlugin`.
- [x] Ochiai, Tarantula, and DStar metric implementations with contingency spectrum matrix ($e_f, e_p, n_f, n_p$).
- [x] Hybrid ranking combining SBFL with Stack Trace Slicing (STS).
- [x] Evaluation harness calculating Top-1, Top-3, Top-5, and Mean Reciprocal Rank (MRR) accuracy against ground truth.

### Phase 4 — Multi-Strategy Repair Engine
- [ ] Strategy interface `RepairStrategy` with uniform candidate patch schema.
- [ ] Deterministic pattern templates for common syntax faults.
- [ ] Search-based AST mutation engine exploring permitted transformations within budget.
- [ ] Pluggable external LLM adapter interface with prompt guardrails and AST sanitization.

### Phase 5 — Robust Validation & Sandboxing
- [ ] AST diff analysis detecting assertion tampering, test modification, or dummy returns.
- [ ] Subprocess resource enforcement (memory limit, CPU affinity where supported, execution timeout).
- [ ] Test flakiness detector running candidate patches multiple times under varied seed/order.

### Phase 6 — Learning & Strategy Selection
- [ ] Contextual multi-armed bandit selector (Thompson Sampling / Upper Confidence Bound).
- [ ] Feature extraction from diagnostic evidence (exception type, operator type, code size).
- [ ] Comparative benchmark: Bandit selection vs. Fixed-order baseline.

### Phase 7 — Self-Improvement Experiments
- [ ] Machine meta-repair module targeting The Machine's own heuristics on an isolated branch.
- [ ] Automated test gate requiring 100% regression suite pass on The Machine itself.
- [ ] Human-in-the-loop signoff CLI for promoting proposed improvements.

### Phase 8 — Research-Grade Benchmarking
- [ ] Public micro-benchmark evaluation suite (50+ deterministic reproducible bugs).
- [ ] Comparative performance evaluation against published baseline metrics.
- [ ] Exportable experiment reports in JSON, CSV, and LaTeX table formats.

### Phase 9 — Observability & Interface
- [ ] Local REST / WebSocket telemetry server.
- [ ] Modern lightweight dashboard displaying real-time repair trials, AST diffs, and bandit weights.
