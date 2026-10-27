# Research Plan — THE MACHINE

## 1. Problem Statement

Automated Program Repair (APR) systems aim to locate, diagnose, and fix software defects automatically. However, existing APR paradigms face three persistent failure modes:
1. **The Overfitting Problem:** A significant fraction of candidate patches pass the failing test suite by gaming assertions, weakening preconditions, or suppressing exceptions, but break unstated specifications or introduce severe regressions (Smith et al., 2015; Le et al., 2019).
2. **High Search Space & Inefficient Localization:** Without high-precision fault localization, search-based APR engines waste exponential computational budget exploring non-faulty code regions.
3. **Static, Non-Adaptive Policies:** Most repair systems apply static, hardcoded heuristics or unordered strategy pipelines without learning from historical successes and failures across defect types.

**The Machine** addresses these challenges through a unified scientific framework combining:
- Spectrum-Based Fault Localization (Ochiai) and dynamic execution trace slicing.
- Stratified repair synthesis (deterministic templates $\to$ bounded AST search $\to$ neural adapters).
- Multi-tier validation invariants designed to reject non-generalizing and trivial patches.
- Contextual multi-armed bandit strategy selection that updates empirical repair likelihoods across defect classes.

---

## 2. Research Questions (RQs)

- **RQ1 (Localization Accuracy):** How does Ochiai-based spectrum fault localization combined with AST trace analysis compare to naive random or recency-based location selection in terms of Top-1 and Top-5 fault localization accuracy?
- **RQ2 (Strategy Efficacy):** What is the repair efficiency (time-to-patch, candidate count) and repair plausibility rate of deterministic syntax transformation templates versus search-based AST mutations across standard mutation categories?
- **RQ3 (Overfitting Mitigation):** What percentage of candidate patches that pass the targeted failing test fail full regression validation, and how effectively do anti-triviality checks prevent false-positive patch acceptance?
- **RQ4 (Empirical Policy Adaptation):** Does historical strategy selection via contextual weighting achieve higher repair success rates and lower total compute cost compared to a fixed sequential strategy order on held-out defect suites?

---

## 3. Testable Hypotheses

- **$H_1$:** Combining execution stack trace slicing with Ochiai spectrum analysis reduces the number of candidate locations evaluated before finding the true fault by at least 60% compared to uniform random selection.
- **$H_2$:** Stratified repair prioritization (evaluating deterministic template repairs before exhaustive AST search) reduces mean time-to-first-valid-patch by over 50% without reducing overall repair recall.
- **$H_3$:** Anti-triviality validation rules (assertion preservation, non-empty block requirement, forbidden exception swallowing) reject $\ge 95\%$ of degenerate patches that would otherwise pass naive single-test validation.
- **$H_4$:** A Thompson Sampling or $\epsilon$-greedy bandit strategy selector achieves statistically significant reduction in candidate evaluations on unseen mutation benchmarks compared to round-robin allocation.

---

## 4. Evaluation Metrics & Definitions

To prevent conflation of repair outcomes, The Machine formally evaluates:

| Metric | Definition | Mathematical Formulation |
| :--- | :--- | :--- |
| **Top-$k$ Localization** | Proportion of experiments where true fault line is within top $k$ ranked suspicious lines | $\frac{1}{|E|} \sum_{e \in E} \mathbb{I}(\text{rank}(loc_e^*) \le k)$ |
| **Plausible Patch Rate** | Proportion of repairs that compile and pass the failing test | $\frac{|E_{\text{plausible}}|}{|E|}$ |
| **Valid Patch Rate** | Proportion of repairs passing failing test AND all regression tests AND anti-triviality checks | $\frac{|E_{\text{valid}}|}{|E|}$ |
| **Overfitting Rate** | Proportion of plausible patches rejected by regression or anti-triviality checks | $\frac{|E_{\text{plausible}} \setminus E_{\text{valid}}|}{|E_{\text{plausible}}|}$ |
| **Compute Efficiency** | Mean wall-clock time and mean number of candidate patch evaluations per valid repair | $\overline{T}_{\text{repair}}, \overline{N}_{\text{candidates}}$ |

---

## 5. Benchmarking & Experimental Protocol

1. **Benchmark Suite:**
   - Synthetic and real-world micro-benchmarks containing deterministic logic: arithmetic algorithms, parser utilities, data structure operations, financial calculators, and state machine transitions.
2. **Defect Generation:**
   - Systematic fault injection using standardized mutation operators (COM, BLI, OB1, CRS, NGR).
   - Traceability: every injected fault records exact file, AST node, pre-state, post-state, and targeted test.
3. **Partitioning:**
   - 70% Training / Policy calibration split.
   - 30% Held-out evaluation split (unseen during bandit parameter tuning).
4. **Reproducibility:**
   - Fixed random seeds for all stochastic elements.
   - Monotonic experiment IDs, captured unified diffs, environment telemetry, and database records stored for each trial.

---

## 6. Threats to Validity

- **Internal Validity:** Flaky tests, execution timeouts caused by OS CPU scheduling, or non-deterministic test ordering. *Mitigation:* Subprocess isolation, explicit test ordering, environment variable pinning, and three repeated trials for timing metrics.
- **External Validity:** Synthetic AST mutations may not perfectly represent complex multi-line human programmer bugs. *Mitigation:* Phased progression from single-token mutations to multi-line semantic errors and real open-source GitHub issues.
- **Construct Validity:** A patch passing all regression tests may still diverge on unexercised edge cases. *Mitigation:* Expanded test generation and property-based test suites in later phases.
