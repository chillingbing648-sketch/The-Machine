<div align="center">

# T H E &nbsp; M A C H I N E

### Autonomous Program Repair &bull; Spectrum-Based Fault Localization &bull; Adaptive Reliability Framework

[![CI](https://github.com/chillingbing648-sketch/The-Machine/actions/workflows/ci.yml/badge.svg)](https://github.com/chillingbing648-sketch/The-Machine/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-007ACC.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-44CC11.svg?style=flat-square)](LICENSE)
[![Engine](https://img.shields.io/badge/architecture-Dual--Loop%20APR-FF6600.svg?style=flat-square)](docs/ARCHITECTURE.md)
[![Localization](https://img.shields.io/badge/SBFL-Ochiai%20%7C%20Tarantula%20%7C%20DStar-8A2BE2.svg?style=flat-square)](docs/RESEARCH_PLAN.md)
[![Persistence](https://img.shields.io/badge/ledger-SQLite%20Append--Only-555555.svg?style=flat-square&logo=sqlite&logoColor=white)](docs/EXPERIMENTS.md)

<p align="center">
  <b>A rigorous, research-grade software engineering system designed to understand failure dynamics, localize root causes via mathematical execution spectrums, synthesize regression-free AST patches, and self-improve strategy dispatch through empirical Bayesian calibration.</b>
</p>

<p align="center">
  <code>Understand</code> &nbsp;&rarr;&nbsp;
  <code>Diagnose</code> &nbsp;&rarr;&nbsp;
  <code>Repair</code> &nbsp;&rarr;&nbsp;
  <code>Verify</code> &nbsp;&rarr;&nbsp;
  <code>Learn</code> &nbsp;&rarr;&nbsp;
  <code>Repeat</code>
</p>

</div>

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. System Architecture](#2-system-architecture)
  - [The Dual-Loop Paradigm](#the-dual-loop-paradigm)
  - [Modular Topology](#modular-topology)
- [3. Repository File Structure & Architecture Map](#3-repository-file-structure--architecture-map)
- [4. Scientific Fault Localization (SBFL)](#4-scientific-fault-localization-sbfl)
  - [Spectrum Contingency Formulation](#spectrum-contingency-formulation)
  - [Mathematical Metrics (Ochiai, Tarantula, DStar)](#mathematical-metrics-ochiai-tarantula-dstar)
  - [Hybrid Stack-Trace Slicing (STS)](#hybrid-stack-trace-slicing-sts)
- [5. Controlled Fault Injection Engine](#5-controlled-fault-injection-engine)
  - [AST Mutation Operators](#ast-mutation-operators)
  - [Mutation Cataloguing & Non-Equivalence](#mutation-cataloguing--non-equivalence)
- [6. Stratified Repair & Candidate Synthesis](#6-stratified-repair--candidate-synthesis)
- [7. Multi-Tier Validation & Overfitting Rejection](#7-multi-tier-validation--overfitting-rejection)
- [8. Benchmark Targets](#8-benchmark-targets)
- [9. Quickstart & Installation](#9-quickstart--installation)
- [10. Command-Line Interface & Demonstration](#10-command-line-interface--demonstration)
  - [Vertical Slice Demonstration](#vertical-slice-demonstration)
  - [Multi-Target Benchmark Evaluation](#multi-target-benchmark-evaluation)
  - [Telemetry Ledger Inspection](#telemetry-ledger-inspection)
- [11. Safety, Isolation & Trust Model](#11-safety-isolation--trust-model)
- [12. Engineering Roadmap](#12-engineering-roadmap)
- [13. Research Standard & Citation](#13-research-standard--citation)

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

## 3. Repository File Structure & Architecture Map

The project is structured as a modular research monolith with clear separation between core algorithms, persistence models, executable targets, and verification suites:

```
.
├── .github/
│   └── workflows/
│       └── ci.yml                     # Multi-OS matrix CI pipeline (Ubuntu, Windows)
├── benchmarks/                        # Deterministic target benchmark suites
│   ├── calculator/                    # Benchmark 1: Arithmetic & boundary constraints
│   │   ├── __init__.py                # Target package initialization
│   │   ├── calculator.py              # Implementation under test (clamp, factorial, divide)
│   │   └── test_calculator.py         # 13-test regression suite
│   └── inventory/                     # Benchmark 2: Transactional order fulfillment
│       ├── __init__.py                # Target package initialization
│       ├── inventory.py               # Inventory management, restock & discount algorithms
│       └── test_inventory.py          # 16-test transactional regression suite
├── docs/                              # Research plans & engineering specifications
│   ├── ARCHITECTURE.md                # System topology, module contracts, and data flow
│   ├── EXPERIMENTS.md                 # Relational SQLite schema & reproduction protocols
│   ├── RESEARCH_PLAN.md               # Formal research questions (RQ1-4), hypotheses & SBFL
│   ├── ROADMAP.md                     # Phased milestone matrix (Phases 0 through 9)
│   └── SAFETY.md                      # Subprocess sandboxing, trust boundaries & governance
├── tests/                             # Comprehensive test suite (36 tests, 100% pass)
│   ├── test_coverage_collector.py     # Statement execution tracing & spectrum verification
│   ├── test_database.py               # SQLite telemetry, mutations & candidate queries
│   ├── test_e2e_pipeline.py           # End-to-end repair cycle integration
│   ├── test_failure_detector.py       # Subprocess timeouts & exception trace extraction
│   ├── test_fault_injector.py         # COM & OB1 mutation operators & path authorization
│   ├── test_fault_injector_phase2.py  # NGR & SDR operators & AST cataloguer verification
│   ├── test_fault_localizer.py        # Stack-trace slicing & score normalization
│   ├── test_inventory_benchmark.py    # Multi-target transactional APR verification
│   ├── test_repair_engine.py          # Candidate patch synthesis & AST templates
│   ├── test_repair_engine_phase4.py   # Multi-strategy arithmetic, boolean, neural LLM adapter
│   ├── test_sbfl.py                   # Ochiai, Tarantula, DStar & MRR metric calculations
│   ├── test_validation_engine.py      # Anti-pattern filters & 4-tier validation firewall
│   └── test_validation_engine_phase5.py # Anti-triviality invariants, scope guard & flakiness detector
├── the_machine/                       # Core engine package
│   ├── __init__.py                    # Version specification & package exports
│   ├── cli.py                         # Command-line interface (demo, benchmark, inspect)
│   ├── core/                          # Data structures and storage
│   │   ├── __init__.py                # Core exports
│   │   ├── database.py                # SQLite append-only ledger implementation
│   │   └── models.py                  # Strongly typed dataclasses & telemetry schemas
│   └── engine/                        # Analytical and repair sub-engines
│       ├── __init__.py                # Engine module exports
│       ├── coverage_collector.py      # Per-test statement execution spectrum collector
│       ├── experiment_manager.py      # Ephemeral workspace orchestrator & rollback
│       ├── failure_detector.py        # Sandboxed subprocess runner & traceback parser
│       ├── fault_injector.py          # AST mutation engine & mutation cataloguer
│       ├── fault_localizer.py         # Hybrid SBFL (Ochiai/Tarantula/DStar) + STS ranker
│       ├── repair_engine.py           # Stratified candidate patch synthesis
│       ├── sbfl_tracer.py             # Subprocess pytest hook plugin for tracing
│       ├── strategy_selector.py       # Multi-armed bandit Bayesian dispatch
│       └── validation_engine.py       # Multi-tier firewall & token-boundary patcher
├── pyproject.toml                     # Modern PEP 621 build specification
├── requirements.txt                   # Dependency manifests
├── .gitignore                         # Build, database, and workspace exclusion rules
└── README.md                          # Primary research & systems documentation
```

---

## 4. Scientific Fault Localization (SBFL)

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
The Ochiai metric computes the cosine similarity between the statement execution vector and the test failure vector:

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

## 5. Controlled Fault Injection Engine

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
# Returns: 28 feasible mutation points in the baseline target
```

---

## 6. Stratified Multi-Strategy Repair (Phase 4)

The Machine approaches patch synthesis through a stratified hierarchy: deterministic transformations first, followed by bounded search spaces, and pluggable neural patch synthesis.

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

1. **`DeterministicTemplateStrategy`:** Targets localized syntax defect patterns with sub-millisecond execution:
   - **Comparison Operator Inversion:** `<` $\leftrightarrow$ `<=`, `>` $\leftrightarrow$ `>=`, `==` $\leftrightarrow$ `!=`, `in` $\leftrightarrow$ `not in`, `is` $\leftrightarrow$ `is not`.
   - **Arithmetic Operator Substitution:** `+` $\leftrightarrow$ `-`, `*` $\leftrightarrow$ `/`, `//`, `%`.
   - **Off-by-One Boundary Adjustments:** $c \to c \pm 1$ on integer literals and boundary conditions.
   - **Boolean Logic Negation:** `not expr` $\to$ `expr`, `True` $\leftrightarrow$ `False`, `and` $\leftrightarrow$ `or`.
   - **Null / None Guard Insertion:** Generates guarded returns and fallback ternaries on `AttributeError` or `NoneType` faults.
   - **Return Fallbacks:** Edge-case default value substitutions (`None`, `False`, `True`, `0`, `[]`).
2. **`SearchBasedASTStrategy`:** Systematically enumerates legal replacement nodes within the AST neighborhood ($[L-2, L+2]$) of suspicious statements, scoring candidates by tree edit distance.
3. **`NeuralRepairStrategy` (Pluggable LLM Adapter):**
   - Decoupled `LLMProvider` abstraction supporting `MockLLMProvider` (offline deterministic benchmarks and unit tests) and `OpenAILikeProvider` (HTTP client for OpenAI, Gemini, and local vLLM/Ollama endpoints).
   - Strict prompt guardrails requiring code-only fenced blocks.
   - AST pre-compilation check before submitting to the validation firewall.
4. **Fair Budget Allocation:** Candidate generation distributes budget evenly across top suspicious lines (`max_per_location`), ensuring lower-ranked root causes receive search iterations.

---

## 7. Multi-Tier Validation & Sandboxing (Phase 5)

A primary failure mode of automated program repair is **patch overfitting**: a synthesized patch passes the failing test by silencing errors, weakening assertions, or breaking unexercised functionality.

The Machine implements a 5-tier validation firewall:

```
Candidate Patch Generated
  |
  v
[ Tier 1: Scope & File Confinement ] ──────> Rejects diffs touching tests or outside workspace
  |
  v
[ Tier 2: Anti-Triviality Invariants ] ────> Rejects assertion deletion, `except: pass`, empty stubs
  |
  v
[ Tier 3: Syntax AST Compilation ] ────────> Rejects syntactically malformed AST transforms
  |
  v
[ Tier 4: Two-Stage Test Execution ]
  ├── 4A: Target Failing Test Check ───────> Failing test must transition FAIL -> PASS
  └── 4B: Full Regression Suite Check ────> Entire regression suite must pass with 0 errors
  |
  v
[ Tier 5: Flakiness Stability Sandbox ] ───> Repeated verification (N runs) to reject order-dependent fixes
```

- **`AntiTrivialityChecker`:**
  - Scope guard: Rejects any patch targeting test files (`test_*.py`, `*_test.py`, `tests/`).
  - Assertion tampering: Detects and rejects patches that delete `assert` statements.
  - Exception swallowing: Flags `except: pass` or `except Exception: return ...` blocks.
  - Function stubbing: Rejects replacing function bodies with vacuous `pass` statements.
- **`FlakinessDetector`:**
  - Evaluates passing patches across multiple test runs ($N \ge 2$) with varied seeds/orders to guarantee the fix is deterministic and reproducible.
- **Subprocess Sandboxing:**
  - Configurable timeouts (scaled from 30s to 60s+ to prevent CPU starvation on heavy workloads).
  - Sanitized environment stripping API keys, tokens, and credentials.
  - Guaranteed workspace rollback in `finally` blocks.
- **Line-Targeted Word-Boundary Application:** Patches are applied strictly to the target statement using token-boundary regex matching ($\backslash b\text{op}\backslash b$) within a localized line window ($[L - 4, L + 4]$), completely avoiding substring collisions (e.g. replacing `quantity` without corrupting `stock_quantity`).

---

## 8. Benchmark Targets

The repository includes two self-contained, deterministic target benchmarks used for reproducible evaluation:

### 1. `benchmarks/calculator`
- **Module:** [benchmarks/calculator/calculator.py](benchmarks/calculator/calculator.py)
- **Suite:** 13 unit and boundary regression tests ([test_calculator.py](benchmarks/calculator/test_calculator.py)).
- **Domain:** Boundary clamping (`clamp`), recursive input validation (`factorial`), and division guards (`divide`).

### 2. `benchmarks/inventory`
- **Module:** [benchmarks/inventory/inventory.py](benchmarks/inventory/inventory.py)
- **Suite:** 16 unit and transactional regression tests ([test_inventory.py](benchmarks/inventory/test_inventory.py)).
- **Domain:** Transactional stock deductibility, restock validation guards, atomic fulfillment, and capped VIP discount algorithms.

---

## 9. Quickstart & Installation

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

## 10. Command-Line Interface & Demonstration

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

## 11. Safety, Isolation & Trust Model

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

## 12. Engineering Roadmap

| Phase | Milestone | Core Focus | Status |
| :---: | :--- | :--- | :---: |
| **0** | Discovery & Foundation | Baseline inspection, environment setup, architecture, research docs | **COMPLETED** |
| **1** | First Functioning Slice | End-to-end pipeline: mutation, detection, localization, repair, DB | **COMPLETED** |
| **2** | Generalized Fault Injection | 6 AST mutation operators (`COM`, `BLI`, `OB1`, `CRS`, `NGR`, `SDR`), cataloguer | **COMPLETED** |
| **3** | Evidence-Based SBFL | Ochiai coverage matrix, stack slicing, Top-1/Top-3/MRR metrics | **COMPLETED** |
| **4** | Multi-Strategy Repair Engine | Template library, AST bounded search, pluggable LLM adapter | **COMPLETED** |
| **5** | Robust Validation & Sandboxing | Invariant checking, anti-triviality heuristics, flakiness sandbox | **COMPLETED** |
| **6** | Empirical Strategy Selection | Contextual bandit dispatch, historical repair learning | *Planned* |
| **7** | Self-Improvement & Meta-Repair | Machine self-evaluation, hypothesis-driven policy updates, human gate | *Planned* |
| **8** | Research-Grade Benchmarking | Held-out validation suites, empirical papers, comparative APR evaluation | *Planned* |
| **9** | Observability Dashboard | Interactive visualization of experiments, diffs, telemetry, and traces | *Planned* |

See [docs/ROADMAP.md](docs/ROADMAP.md) for full acceptance criteria across all phases.

---

## 13. Research Standard & Citation

The Machine is developed as an open scientific platform for Automated Program Repair and Software Reliability Research.

If you utilize The Machine in academic research, benchmark evaluations, or industrial experiments, please cite the framework as follows:

```bibtex
@software{the_machine_2026,
  author = {Dubey, Harsh and The Machine Contributors},
  title = {The Machine: An Autonomous Program Repair, Fault Localization, and Self-Improving Reliability Engine},
  year = {2026},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/chillingbing648-sketch/The-Machine}}
}
```

---

<div align="center">
  <sub>Engineered with rigor. Authored by <b>Harsh Dubey</b> &bull; Maintained by The Machine Research Contributors.</sub>
</div>
