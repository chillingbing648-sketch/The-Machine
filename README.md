<div align="center">

```
 _____ _   _ _____   __  __    _    ____ _   _ ___ _   _ _____ 
|_   _| | | | ____| |  \/  |  / \  / ___| | | |_ _| \ | | ____|
  | | | |_| |  _|   | |\/| | / _ \| |   | |_| || ||  \| |  _|  
  | | |  _  | |___  | |  | |/ ___ \ |___|  _  || || |\  | |___ 
  |_| |_| |_|_____| |_|  |_/_/   \_\____|_| |_|___|_| \_|_____|
```

### An Autonomous Program Repair, Fault Localization, and Self-Improving Reliability Engine

[![CI](https://github.com/chillingbing648-sketch/The-Machine/actions/workflows/ci.yml/badge.svg)](https://github.com/chillingbing648-sketch/The-Machine/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Architecture](https://img.shields.io/badge/architecture-Dual--Loop%20APR-orange.svg)](docs/ARCHITECTURE.md)
[![Localization](https://img.shields.io/badge/SBFL-Ochiai%20%7C%20Tarantula%20%7C%20DStar-purple.svg)](docs/RESEARCH_PLAN.md)
[![Storage](https://img.shields.io/badge/storage-SQLite%20Append--Only%20Ledger-lightgrey.svg)](docs/EXPERIMENTS.md)

<p align="center">
  <b>Understand</b> &nbsp;&bull;&nbsp;
  <b>Diagnose</b> &nbsp;&bull;&nbsp;
  <b>Repair</b> &nbsp;&bull;&nbsp;
  <b>Verify</b> &nbsp;&bull;&nbsp;
  <b>Learn</b> &nbsp;&bull;&nbsp;
  <b>Repeat</b>
</p>

</div>

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. System Architecture](#2-system-architecture)
  - [The Dual-Loop Paradigm](#the-dual-loop-paradigm)
  - [Modular Topology](#modular-topology)
- [3. Scientific Fault Localization (SBFL)](#3-scientific-fault-localization-sbfl)
  - [Spectrum Contingency Formulation](#spectrum-contingency-formulation)
  - [Mathematical Metrics (Ochiai, Tarantula, DStar)](#mathematical-metrics-ochiai-tarantula-dstar)
  - [Hybrid Stack-Trace Slicing (STS)](#hybrid-stack-trace-slicing-sts)
- [4. Controlled Fault Injection Engine](#4-controlled-fault-injection-engine)
  - [AST Mutation Operators](#ast-mutation-operators)
  - [Mutation Cataloguing & Non-Equivalence](#mutation-cataloguing--non-equivalence)
- [5. Stratified Repair & Candidate Synthesis](#5-stratified-repair--candidate-synthesis)
- [6. Multi-Tier Validation & Overfitting Rejection](#6-multi-tier-validation--overfitting-rejection)
- [7. Benchmark Targets](#7-benchmark-targets)
- [8. Quickstart & Installation](#8-quickstart--installation)
- [9. Command-Line Interface & Demonstration](#9-command-line-interface--demonstration)
  - [Vertical Slice Demonstration](#vertical-slice-demonstration)
  - [Multi-Target Benchmark Evaluation](#multi-target-benchmark-evaluation)
  - [Telemetry Ledger Inspection](#telemetry-ledger-inspection)
- [10. Safety, Isolation & Trust Model](#10-safety-isolation--trust-model)
- [11. Engineering Roadmap](#11-engineering-roadmap)
- [12. Research Standard & Citation](#12-research-standard--citation)

---

## 1. Executive Summary

**The Machine** is an autonomous software reliability, fault localization, and automated program repair (APR) platform. Rather than relying on superficial heuristic generators or unconstrained LLM hallucinations, The Machine is engineered around rigorous program analysis, Spectrum-Based Fault Localization (SBFL), AST-level syntax transformations, and multi-tier regression invariants.

### Core Tenets

1. **Non-Destructive Execution:** Canonical application sources are treated as strictly immutable. All fault injections, coverage traces, candidate patch applications, and regression validations run within isolated, disposable workspaces (`.machine_workspaces/<exp_id>`).
2. **Mathematical Diagnosability:** Fault locations are prioritized through the empirical execution spectrum ($e_f, e_p, n_f, n_p$) blended with stack trace frame slicing, reporting normalized suspiciousness coefficients, Top-$k$ accuracy, and Mean Reciprocal Rank (MRR).
3. **Overfitting Elimination:** A candidate patch that passes only the target failing test is considered unverified. A patch is accepted only when it passes syntax compilation, passes the failing test, passes 100% of the regression suite, and passes AST anti-pattern filters (detecting assertion tampering, dummy stubs, and exception swallowing).
4. **Dual-Loop Self-Improvement:** The system distinguishes between repairing target software (Loop 1) and evaluating improvements to its own repair heuristics (Loop 2), enforcing human approval gates before promoting meta-policy changes.

---

## 2. System Architecture

### The Dual-Loop Paradigm

The Machine operates on two cleanly decoupled feedback loops:

```
[ LOOP 1: TARGET SOFTWARE REPAIR ]
========================================================================================
Fault Injection -> Failure Detection -> SBFL Diagnosis -> Patch Synthesis -> Validation
      ^                                                                         |
      |                                                                         v
      +--------------------- Outcome Logged in Ledger <-------------------------+
                                      |
                                      v
[ LOOP 2: META-LEARNING & SYSTEM EVOLUTION ]
========================================================================================
Empirical Calibration -> Weakness Mining -> Strategy Re-weighting -> Human Approval Gate
```

- **Loop 1 (Operational APR):** Operates at execution time on target codebases. Diagnoses defects, synthesizes bounded candidate modifications, verifies them against test invariants, and commits accepted repairs.
- **Loop 2 (Meta-Learning):** Operates on historical experiment ledgers (`experiments.db`). Evaluates strategy success rates conditioned on defect categories, calculates Bayesian posterior weights via Multi-Armed Bandit dispatch, and suggests heuristic updates under human governance.

### Modular Topology

```
+-----------------------------------------------------------------------------------------+
|                                      THE MACHINE                                        |
|                                                                                         |
|   +-----------------------+     +-----------------------+     +---------------------+   |
|   |  Experiment Manager   |---->|   Failure Detector    |---->|   Coverage Collector|   |
|   |  - Ephemeral copies   |     |   - Subprocess sandbox|     |   - Spectrum tracer |   |
|   |  - Monotonic UUIDs    |     |   - Trace & exit code |     |   - Line-hit matrix |   |
|   +-----------------------+     +-----------------------+     +---------------------+   |
|               |                             |                            |              |
|               v                             v                            v              |
|   +-----------------------+     +-----------------------+     +---------------------+   |
|   |  Fault Injector (AST) |     |   Fault Localizer     |<----+  SBFL Engine        |   |
|   |  - COM, BLI, OB1,     |     |   - Hybrid STS + SBFL |     |  - Ochiai / Tarant. |   |
|   |    CRS, NGR, SDR      |     |   - Top-k & MRR eval  |     |  - DStar (star=2)   |   |
|   +-----------------------+     +-----------------------+     +---------------------+   |
|                                             |                                           |
|                                             v                                           |
|   +-----------------------+     +-----------------------+                               |
|   |  Validation Engine    |<----+     Repair Engine     |                               |
|   |  - Regression suite   |     |  - Deterministic Temp.|                               |
|   |  - Anti-pattern check |     |  - Bounded AST Search |                               |
|   |  - Syntax & scope     |     |  - Multi-Strategy Hub |                               |
|   +-----------------------+     +-----------------------+                               |
|               |                             |                                           |
|               v                             v                                           |
|   +-----------------------------------------------------+                               |
|   |       SQLite Append-Only Ledger (experiments.db)    |                               |
|   |  - Full trial telemetry, diffs, timings, validation |                               |
|   +-----------------------------------------------------+                               |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Scientific Fault Localization (SBFL)

### Spectrum Contingency Formulation

During test execution, `CoverageCollector` instruments the target codebase using a detached `SpectrumTracerPlugin`, recording which program statements $s \in S$ are executed by passing vs. failing test cases.

For every statement $s$, The Machine constructs a $2 \times 2$ contingency table:

| Test Outcome | Executing Statement $s$ | Not Executing Statement $s$ | Total |
| :--- | :---: | :---: | :---: |
| **Failed Tests** | $e_f(s)$ | $n_f(s)$ | $T_{\text{fail}} = e_f + n_f$ |
| **Passed Tests** | $e_p(s)$ | $n_p(s)$ | $T_{\text{pass}} = e_p + n_p$ |
| **Total Tests** | $e(s) = e_f + e_p$ | $n(s) = n_f + n_p$ | $T_{\text{total}}$ |

### Mathematical Metrics

The Machine implements three foundational spectrum-based suspiciousness coefficients:

#### 1. Ochiai Suspiciousness Coefficient
The Ochiai metric (widely demonstrated to offer superior fault isolation in software engineering literature) computes the cosine similarity between the statement execution vector and the test failure vector:

$$\text{Ochiai}(s) = \frac{e_f(s)}{\sqrt{\left(e_f(s) + n_f(s)\right) \times \left(e_f(s) + e_p(s)\right)}}$$

#### 2. Tarantula Coefficient
Normalizes failure execution density against passing execution density:

$$\text{Tarantula}(s) = \frac{\frac{e_f(s)}{e_f(s) + n_f(s)}}{\frac{e_f(s)}{e_f(s) + n_f(s)} + \frac{e_p(s)}{e_p(s) + n_p(s)}}}$$

#### 3. $D^*$ Metric ($DStar$ with $\star = 2$)
Penalizes statements executed by passing tests while rewarding statements executed by failing tests:

$$D^*(s) = \frac{\left(e_f(s)\right)^2}{e_p(s) + n_f(s)}$$

### Hybrid Stack-Trace Slicing (STS)

When unhandled exceptions occur, execution frames directly pinpoint exception origins. The Machine normalizes Stack Trace Slicing ($\text{Score}_{\text{STS}}$) and blends it with Spectrum-Based Fault Localization ($\text{Score}_{\text{SBFL}}$) using a convex combination:

$$\text{Score}_{\text{hybrid}}(s) = \alpha \cdot \text{Score}_{\text{SBFL}}(s) + (1 - \alpha) \cdot \text{Score}_{\text{STS}}(s), \quad \alpha \in [0.0, 1.0] \quad (\text{default } \alpha = 0.6)$$

### Localization Quality Metrics

When evaluating against ground truth defects (line $L^*$), The Machine records:
- **$\text{Top-1 Hit}$:** $\mathbb{I}(\text{rank}(L^*) = 1)$
- **$\text{Top-3 Hit}$:** $\mathbb{I}(\text{rank}(L^*) \le 3)$
- **$\text{Top-5 Hit}$:** $\mathbb{I}(\text{rank}(L^*) \le 5)$
- **$\text{Mean Reciprocal Rank (MRR)}$:** $\frac{1}{\text{rank}(L^*)}$

---

## 4. Controlled Fault Injection Engine

To systematically measure repair performance without relying on synthetic mocks, `FaultInjector` injects deterministic, traceable mutations directly into the target code's Abstract Syntax Tree (AST).

### AST Mutation Operators

| Operator Key | Formal Operator Name | AST Transformation | Example |
| :---: | :--- | :--- | :--- |
| **`COM`** | Comparison Operator Mutation | $\text{op} \in \{<, \le, >, \ge, ==, \ne\} \to \text{op}'$ | `val <= min_val` $\to$ `val < min_val` |
| **`BLI`** | Boolean Logic Inversion | $\text{not } e \leftrightarrow e, \quad e_1 \text{ and } e_2 \leftrightarrow e_1 \text{ or } e_2$ | `if not valid:` $\to$ `if valid:` |
| **`OB1`** | Boundary Off-by-One | $c \in \mathbb{Z} \to c \pm 1$ | `offset = 0` $\to$ `offset = 1` |
| **`CRS`** | Constant & Return Substitution | $\text{return } e \to \text{return None}, \quad c \to c'$ | `return total` $\to$ `return None` |
| **`NGR`** | Null & Guard Removal | $e \text{ is None} \leftrightarrow e \text{ is not None}$ | `if x is None:` $\to$ `if x is not None:` |
| **`SDR`** | Statement Deletion | $\text{Assign} \mid \text{AugAssign} \to \text{Pass}$ | `self.stock -= qty` $\to$ `pass` |

### Mutation Cataloguing & Non-Equivalence

The engine provides an automated scanner that walks any target file's AST and catalogues every viable mutation point across all registered operators before applying faults:

```bash
python -c "from the_machine.engine.fault_injector import FaultInjector; from pathlib import Path; print(len(FaultInjector().catalogue_all_mutations(Path('benchmarks/calculator/calculator.py'))))"
# Returns: 28 feasible mutation points
```

---

## 5. Stratified Repair & Candidate Synthesis

The Machine approaches patch synthesis through a stratified hierarchy: deterministic transformations first, followed by bounded search spaces.

```
Suspicious Location Ranked by SBFL
              |
              v
[ Strategy 1: Deterministic Templates ] ──(Plausible?)──> [ Validation Engine ]
              | (No candidate)                                  | (Accepted?)
              v                                                 +──> SUCCESS
[ Strategy 2: Bounded AST Search ]      ──(Plausible?)──> [ Validation Engine ]
              | (Exhausted)                                     | (Accepted?)
              v                                                 +──> SUCCESS
[ Strategy 3: Neural / LLM Adapter ]    ──(Plausible?)──> [ Validation Engine ]
```

1. **`DeterministicTemplateStrategy`:** Targets localized syntax defect patterns with sub-millisecond execution. Evaluates operator reversals, off-by-one shifts, and guard inversions.
2. **`SearchBasedASTStrategy`:** Systematically enumerates legal replacement nodes within the AST neighborhood of suspicious lines.
3. **Pluggable Interface (`RepairStrategy`):** All repair strategies adhere to a common contract:
   ```python
   def generate_patches(
       location: SuspiciousLocation,
       report: TestExecutionReport,
       workspace_path: Path
   ) -> List[PatchCandidate]: ...
   ```

---

## 6. Multi-Tier Validation & Overfitting Rejection

A primary failure mode of automated program repair is **patch overfitting**: a synthesized patch passes the failing test by silencing errors, weakening assertions, or breaking unexercised functionality.

The Machine implements a 4-tier validation firewall:

```
Candidate Patch Generated
  |
  v
[ Tier 1: Scope & File Boundaries ] ───────> Rejects diffs touching tests or outside workspace
  |
  v
[ Tier 2: AST Anti-Pattern Analysis ] ─────> Rejects `except: pass`, empty `return None` stubs
  |
  v
[ Tier 3: Syntax Compilation ] ────────────> Rejects syntactically malformed AST transforms
  |
  v
[ Tier 4: Two-Stage Test Execution ]
  ├── 4A: Target Failing Test Check ───────> Failing test must transition FAIL -> PASS
  └── 4B: Full Regression Suite Check ────> Entire regression suite must pass with 0 errors
```

- **Line-Targeted Word-Boundary Application:** Patches are applied strictly to the target statement using token-boundary regex matching ($\backslash b\text{op}\backslash b$) within a localized line window ($[L - 4, L + 4]$), completely avoiding substring collisions (e.g. replacing `quantity` without corrupting `stock_quantity`).

---

## 7. Benchmark Targets

The repository includes two self-contained, deterministic target benchmarks used for reproducible evaluation:

### 1. `benchmarks/calculator`
- **Module:** [benchmarks/calculator/calculator.py](file:///benchmarks/calculator/calculator.py)
- **Suite:** 13 unit and boundary regression tests ([test_calculator.py](file:///benchmarks/calculator/test_calculator.py)).
- **Domain:** Boundary clamping (`clamp`), recursive input validation (`factorial`), and division guards (`divide`).

### 2. `benchmarks/inventory`
- **Module:** [benchmarks/inventory/inventory.py](file:///benchmarks/inventory/inventory.py)
- **Suite:** 16 unit and transactional regression tests ([test_inventory.py](file:///benchmarks/inventory/test_inventory.py)).
- **Domain:** Transactional stock deductibility, restock validation guards, atomic fulfillment, and capped VIP discount algorithms.

---

## 8. Quickstart & Installation

### Prerequisites

- Python 3.11, 3.12, 3.13, or 3.14
- Git 2.40+

### Setup

```bash
# Clone repository
git clone https://github.com/chillingbing648-sketch/The-Machine.git
cd The-Machine

# Create and activate virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

# Install in editable mode with development dependencies
pip install -e .
pip install pytest pytest-cov
```

### Running the Test Suite

Execute all 22 unit, integration, and benchmark tests:

```bash
pytest tests/ -v
```

---

## 9. Command-Line Interface & Demonstration

The Machine includes a CLI accessible via `the-machine` or `python -m the_machine.cli`.

```
usage: the-machine [-h] {demo,benchmark,history,inspect} ...

THE MACHINE Automated Program Repair CLI

commands:
  demo       Run Phase 1-3 end-to-end demonstration
  benchmark  Run multi-target research benchmark suite
  history    List past experiment records
  inspect    Inspect a specific experiment record
```

### Vertical Slice Demonstration

Run an end-to-end automated cycle (mutation injection $\to$ failure detection $\to$ SBFL localization $\to$ template repair $\to$ full regression verification $\to$ SQLite ledger):

```bash
python -m the_machine.cli demo
```

#### Terminal Output

```
================================================================================
                    THE MACHINE — RELIABILITY & REPAIR ENGINE
       Understand -> Diagnose -> Repair -> Verify -> Learn -> Repeat
================================================================================

[*] Starting Phase 1-3 End-to-End Vertical Slice Demonstration...

[Phase 1.1] Target Benchmark: calculator_benchmark
[*] Configuration: timeout=30.0s, max_candidates=5

[Phase 2.1] Generalized Mutation Engine Catalogued 28 Feasible Mutation Sites:
    - Operator 'COM': 8 available mutation points
    - Operator 'BLI': 1 available mutation points
    - Operator 'OB1': 8 available mutation points
    - Operator 'CRS': 10 available mutation points
    - Operator 'SDR': 1 available mutation points

[Phase 2.2] Injecting Traceable Fault into Ephemeral Workspace...
[*] Experiment ID: exp_1793131721_11903e
[*] Mutation Applied: COMPARISON_OPERATOR at line 25
    Original: b == 0
    Mutated:  b != 0

[Phase 1.2] Failure Detection & Evidence Collection:
    Passed: False
    Total Tests: 13
    Failed Tests: 2
    [-] Failing Test: test_divide_valid
        Exception: ValueError: ('Cannot divide by zero')
    [-] Failing Test: test_divide_by_zero
        Exception: ZeroDivisionError: division by zero

[Phase 3.1] Evidence-Based Fault Localization (Ochiai SBFL + Stack Trace Slicing):
    Rank #1: Line 21  (Score: 1.0000)
            Evidence:  SBFL(OCHIAI=0.707; ef=1, ep=0, nf=1, np=11) | Stack frame in test_divide_by_zero (line 21)
            Statement: return a / b
    Rank #2: Line 20  (Score: 1.0000)
            Evidence:  SBFL(OCHIAI=0.707; ef=1, ep=0, nf=1, np=11) | Stack frame in test_divide_valid (line 20)
            Statement: raise ValueError('Cannot divide by zero')
    Rank #3: Line 19  (Score: 0.7279)
            Evidence:  SBFL(OCHIAI=1.000; ef=2, ep=0, nf=0, np=11)
            Statement: if b != 0:

[Phase 1.3] Candidate Synthesis & Rigorous Invariant Validation:
    Candidates Evaluated: 1
    [+] ACCEPTED PATCH FOUND via strategy 'deterministic_template':
        Line 19: Invert comparison operator from NotEq to Eq
        Diff:
            --- a/calculator.py
            +++ b/calculator.py
            @@ -16,7 +16,7 @@
             def divide(a: Number, b: Number) -> float:
                 """Divide a by b with division by zero guard."""
            -    if b != 0:
            +    if b == 0:
                     raise ValueError('Cannot divide by zero')
                 return a / b

    [+] Validation: Patch successfully verified against target defect and full regression suite
        Failing Test Passed: True
        Regression Suite Passed: True
        Anti-Pattern Check: Passed (clean)

[Phase 1.4] Ledger & Restoration:
    Status: REPAIRED
    Total Pipeline Execution Time: 24.06s
    Persisted in: experiments.db
    Canonical source code preserved without modifications.
```

### Multi-Target Benchmark Evaluation

Execute automated repairs across multiple distinct targets and defect classes:

```bash
python -m the_machine.cli benchmark
```

```
================================================================================
                     RESEARCH BENCHMARK EVALUATION SUMMARY                      
================================================================================
Target                   Operator   Status         Top-1    MRR      Duration  
--------------------------------------------------------------------------------
calculator_benchmark     COM        REPAIRED       True     1.00     22.30s    
inventory_benchmark      COM        REPAIRED       True     1.00     33.96s    
================================================================================
```

### Telemetry Ledger Inspection

Inspect historical runs and examine patch diffs stored in `experiments.db`:

```bash
# List historical experiment runs
python -m the_machine.cli history

# Inspect detailed telemetry of a specific experiment
python -m the_machine.cli inspect exp_1793131721_11903e
```

---

## 10. Safety, Isolation & Trust Model

The Machine enforces strict security and trust boundaries when evaluating untrusted program code and synthesized candidates:

```
+-------------------------------------------------------------------------+
| TRUST BOUNDARY: CANONICAL REPOSITORY (IMMUTABLE)                        |
|   benchmarks/calculator/calculator.py (READ-ONLY)                       |
+-------------------------------------------------------------------------+
                               |
                               | (Copy on Provision)
                               v
+-------------------------------------------------------------------------+
| ISOLATION ENCLAVE: EPHEMERAL REPLICA WORKSPACE                          |
|   .machine_workspaces/<exp_id>/ (DISPOSABLE)                            |
|                                                                         |
|   [Subprocess Execution Sandbox]                                        |
|   - Wall-clock timeout enforcement (default 30.0s)                      |
|   - CPU / memory isolation                                              |
|   - Scrubbed environment variables (secrets, tokens, keys stripped)     |
|   - Explicit non-shell argument vectors (no shell=True injection)       |
|   - Workspace-bound path confinement (no ../ path traversal)            |
+-------------------------------------------------------------------------+
                               |
                               v (Automatic Pruning)
+-------------------------------------------------------------------------+
| TEARDOWN: Ephemeral workspace purged on experiment completion           |
+-------------------------------------------------------------------------+
```

---

## 11. Engineering Roadmap

| Phase | Milestone | Core Focus | Status |
| :---: | :--- | :--- | :---: |
| **0** | Discovery & Foundation | Baseline inspection, environment setup, architecture, research docs | **COMPLETED** |
| **1** | First Functioning Slice | End-to-end pipeline: mutation, detection, localization, repair, DB | **COMPLETED** |
| **2** | Generalized Fault Injection | 6 AST mutation operators (`COM`, `BLI`, `OB1`, `CRS`, `NGR`, `SDR`), cataloguer | **COMPLETED** |
| **3** | Evidence-Based SBFL | Ochiai coverage matrix, stack slicing, Top-1/Top-3/MRR metrics | **COMPLETED** |
| **4** | Multi-Strategy Repair Engine | Template library, AST bounded search, pluggable LLM adapter | *In Progress* |
| **5** | Robust Validation & Sandboxing | Invariant checking, anti-triviality heuristics, strict resource limits | *Planned* |
| **6** | Empirical Strategy Selection | Contextual bandit dispatch, historical repair learning | *Planned* |
| **7** | Self-Improvement & Meta-Repair | Machine self-evaluation, hypothesis-driven policy updates, human gate | *Planned* |
| **8** | Research-Grade Benchmarking | Held-out validation suites, empirical papers, comparative APR evaluation | *Planned* |
| **9** | Observability Dashboard | Interactive visualization of experiments, diffs, telemetry, and traces | *Planned* |

See [docs/ROADMAP.md](docs/ROADMAP.md) for full acceptance criteria across all phases.

---

## 12. Research Standard & Citation

The Machine is developed as an open scientific platform for Automated Program Repair and Software Reliability Research.

If you utilize The Machine in academic research, benchmark evaluations, or industrial experiments, please cite the framework as follows:

```bibtex
@software{the_machine_2026,
  author = {Dubey, Prateek and The Machine Contributors},
  title = {The Machine: An Autonomous Program Repair, Fault Localization, and Self-Improving Reliability Engine},
  year = {2026},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/chillingbing648-sketch/The-Machine}}
}
```

---

<div align="center">
  <sub>Engineered with rigor. Maintained by The Machine Research Team.</sub>
</div>
