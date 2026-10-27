# Experiment Methodology & Reproducibility — THE MACHINE

## 1. Experiment Life Cycle

Every repair trial in The Machine follows a standardized lifecycle governed by the `ExperimentManager`:

```
[INIT] -> Generate UUIDv4 -> Record Configuration in SQLite
  |
  v
[PROVISION] -> Create Ephemeral Workspace Copy
  |
  v
[INJECT] -> Apply Traceable AST Mutation -> Record Mutation Metadata
  |
  v
[DETECT] -> Run Subprocess Pytest -> Collect Output, Trace, Exit Code
  |
  v
[LOCALIZE] -> Parse Stack Traces & Spectrum -> Rank Suspicious Locations
  |
  v
[SYNTHESIZE] -> Dispatch Repair Strategy -> Generate Ranked Patch Candidates
  |
  v
[VALIDATE] -> Apply Patch to Workspace -> Verify Target Test + Regressions
  |
  v
[RECORD] -> Store Candidate Outlines & Validation Outcomes in SQLite
  |
  v
[CLEANUP] -> Purge / Restore Workspace -> Export Experiment Summary
```

---

## 2. Relational Schema (`experiments.db`)

All experiments are tracked in an append-only SQLite database with the following primary entities:

### `experiments`
- `id` (TEXT, PK): Unique experiment identifier (e.g. `exp_20261028_...`).
- `timestamp` (TEXT): ISO 8601 UTC timestamp.
- `target_name` (TEXT): Name of benchmark target.
- `status` (TEXT): `RUNNING`, `SUCCESS`, `FAILED`, `TIMEOUT`, `ERROR`.
- `config_json` (TEXT): Serialized configuration (timeout, strategies, seed).
- `created_at` (TEXT): Creation timestamp.

### `mutations`
- `id` (INTEGER, PK AUTOINCREMENT): Mutation record ID.
- `experiment_id` (TEXT, FK): Reference to parent experiment.
- `file_path` (TEXT): Target file path.
- `operator` (TEXT): Operator identifier (e.g. `COM`, `BLI`, `OB1`).
- `line_number` (INTEGER): Line modified.
- `original_source` (TEXT): AST statement pre-mutation.
- `mutated_source` (TEXT): AST statement post-mutation.

### `diagnostic_reports`
- `id` (INTEGER, PK AUTOINCREMENT): Diagnostic record ID.
- `experiment_id` (TEXT, FK): Parent experiment.
- `outcome` (TEXT): `PASS`, `FAIL`, `ERROR`, `TIMEOUT`.
- `failing_tests` (TEXT): JSON array of failing test names.
- `exception_type` (TEXT): Top-level unhandled exception class name.
- `stack_trace` (TEXT): Captured raw stack trace.
- `duration_ms` (REAL): Test execution duration in milliseconds.

### `suspicious_locations`
- `id` (INTEGER, PK AUTOINCREMENT): Location ID.
- `experiment_id` (TEXT, FK): Parent experiment.
- `file_path` (TEXT): Suspicious file path.
- `line_number` (INTEGER): Suspicious line.
- `score` (REAL): Normalized suspiciousness score $[0.0, 1.0]$.
- `evidence` (TEXT): Description of rationale (e.g., Ochiai rank, Stack frame).

### `patch_candidates`
- `id` (TEXT, PK): Candidate identifier (`cand_...`).
- `experiment_id` (TEXT, FK): Parent experiment.
- `strategy_name` (TEXT): Name of generating strategy.
- `file_path` (TEXT): Patched file.
- `diff_content` (TEXT): Unified diff format.
- `validation_status` (TEXT): `ACCEPTED`, `REJECTED`, `REGRESSED`, `SYNTAX_ERROR`, `TIMEOUT`.
- `validation_details` (TEXT): JSON telemetry from validation run.
- `execution_time_ms` (REAL): Synthesis + validation runtime.

---

## 3. Reproducibility Protocol

To reproduce any historical experiment:
1. Load configuration from `experiments` table using `id`.
2. Target project source is reset to initial commit state.
3. Injected mutation is reapplied using stored AST operator and coordinates.
4. Repair strategy is invoked using the recorded seed and parameters.
5. Produced candidate patch diff is compared bitwise against recorded `diff_content`.
6. Validation outcome is verified against recorded `validation_status`.
