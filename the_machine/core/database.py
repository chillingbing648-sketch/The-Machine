"""SQLite persistence layer for The Machine experiment tracking."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from .models import (
    ExperimentConfig,
    ExperimentStatus,
    ExperimentSummary,
    MutationRecord,
    PatchCandidate,
    SuspiciousLocation,
    TestExecutionReport,
    ValidationResult,
    ValidationStatus,
)


class ExperimentDatabase:
    """Relational SQLite database managing experiment telemetry and lineage."""

    def __init__(self, db_path: str = "experiments.db"):
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Initialize database schema if not present."""
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                target_name TEXT NOT NULL,
                status TEXT NOT NULL,
                config_json TEXT NOT NULL,
                total_duration_sec REAL DEFAULT 0.0,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mutations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                mutation_id TEXT NOT NULL,
                operator TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                original_code TEXT NOT NULL,
                mutated_code TEXT NOT NULL,
                applied_at REAL NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS diagnostic_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                passed INTEGER NOT NULL,
                total_tests INTEGER NOT NULL,
                failed_tests INTEGER NOT NULL,
                failures_json TEXT NOT NULL,
                duration_sec REAL NOT NULL,
                exit_code INTEGER NOT NULL,
                timed_out INTEGER NOT NULL,
                stdout TEXT,
                stderr TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS suspicious_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                score REAL NOT NULL,
                evidence TEXT NOT NULL,
                statement_code TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS patch_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT NOT NULL,
                experiment_id TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                original_code TEXT NOT NULL,
                replacement_code TEXT NOT NULL,
                diff TEXT NOT NULL,
                explanation TEXT NOT NULL,
                validation_status TEXT NOT NULL,
                failing_test_passed INTEGER NOT NULL,
                regression_tests_passed INTEGER NOT NULL,
                syntax_valid INTEGER NOT NULL,
                anti_pattern_detected INTEGER NOT NULL,
                validation_message TEXT NOT NULL,
                execution_time_sec REAL NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id) ON DELETE CASCADE
            );
            """)

    def record_experiment_start(self, experiment_id: str, config: ExperimentConfig) -> None:
        """Create initial record for a new experiment."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO experiments (id, target_name, status, config_json, total_duration_sec, created_at)
                VALUES (?, ?, ?, ?, 0.0, ?)
                """,
                (
                    experiment_id,
                    config.target_name,
                    ExperimentStatus.INITIALIZED.value,
                    json.dumps(config.to_dict()),
                    float(sqlite3.datetime.datetime.now().timestamp()),
                ),
            )

    def record_mutation(self, experiment_id: str, mutation: MutationRecord) -> None:
        """Record an injected mutation."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO mutations (
                    experiment_id, mutation_id, operator, file_path, line_number,
                    original_code, mutated_code, applied_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment_id,
                    mutation.mutation_id,
                    mutation.operator,
                    mutation.file_path,
                    mutation.line_number,
                    mutation.original_code,
                    mutation.mutated_code,
                    mutation.applied_at,
                ),
            )
            conn.execute(
                "UPDATE experiments SET status = ? WHERE id = ?",
                (ExperimentStatus.INJECTED.value, experiment_id),
            )

    def record_diagnostic(self, experiment_id: str, report: TestExecutionReport) -> None:
        """Record initial failure diagnosis report."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO diagnostic_reports (
                    experiment_id, passed, total_tests, failed_tests,
                    failures_json, duration_sec, exit_code, timed_out, stdout, stderr
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment_id,
                    1 if report.passed else 0,
                    report.total_tests,
                    report.failed_tests,
                    json.dumps([f.to_dict() for f in report.failures]),
                    report.duration_sec,
                    report.exit_code,
                    1 if report.timed_out else 0,
                    report.stdout,
                    report.stderr,
                ),
            )
            status = ExperimentStatus.FAILED_DETECTED.value if not report.passed else ExperimentStatus.INITIALIZED.value
            conn.execute(
                "UPDATE experiments SET status = ? WHERE id = ?",
                (status, experiment_id),
            )

    def record_locations(self, experiment_id: str, locations: List[SuspiciousLocation]) -> None:
        """Record localized suspicious locations."""
        with self._get_connection() as conn:
            for loc in locations:
                conn.execute(
                    """
                    INSERT INTO suspicious_locations (
                        experiment_id, file_path, line_number, score, evidence, statement_code
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        experiment_id,
                        loc.file_path,
                        loc.line_number,
                        loc.score,
                        loc.evidence,
                        loc.statement_code,
                    ),
                )
            conn.execute(
                "UPDATE experiments SET status = ? WHERE id = ?",
                (ExperimentStatus.LOCALIZED.value, experiment_id),
            )

    def record_patch_evaluation(
        self,
        experiment_id: str,
        candidate: PatchCandidate,
        validation: ValidationResult,
    ) -> None:
        """Record evaluation outcome of a single candidate patch."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO patch_evaluations (
                    candidate_id, experiment_id, strategy_name, file_path, line_number,
                    original_code, replacement_code, diff, explanation,
                    validation_status, failing_test_passed, regression_tests_passed,
                    syntax_valid, anti_pattern_detected, validation_message, execution_time_sec
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate.candidate_id,
                    experiment_id,
                    candidate.strategy_name,
                    candidate.file_path,
                    candidate.line_number,
                    candidate.original_code,
                    candidate.replacement_code,
                    candidate.diff,
                    candidate.explanation,
                    validation.status.value,
                    1 if validation.failing_test_passed else 0,
                    1 if validation.regression_tests_passed else 0,
                    1 if validation.syntax_valid else 0,
                    1 if validation.anti_pattern_detected else 0,
                    validation.message,
                    validation.execution_time_sec,
                ),
            )

    def finish_experiment(
        self,
        experiment_id: str,
        status: ExperimentStatus,
        total_duration_sec: float,
    ) -> None:
        """Mark experiment complete with final status and runtime."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE experiments SET status = ?, total_duration_sec = ? WHERE id = ?",
                (status.value, total_duration_sec, experiment_id),
            )

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full experiment details."""
        with self._get_connection() as conn:
            exp_row = conn.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,)).fetchone()
            if not exp_row:
                return None

            mutation_row = conn.execute("SELECT * FROM mutations WHERE experiment_id = ?", (experiment_id,)).fetchone()
            diag_row = conn.execute("SELECT * FROM diagnostic_reports WHERE experiment_id = ?", (experiment_id,)).fetchone()
            loc_rows = conn.execute("SELECT * FROM suspicious_locations WHERE experiment_id = ? ORDER BY score DESC", (experiment_id,)).fetchall()
            patch_rows = conn.execute("SELECT * FROM patch_evaluations WHERE experiment_id = ?", (experiment_id,)).fetchall()

            return {
                "experiment": dict(exp_row),
                "mutation": dict(mutation_row) if mutation_row else None,
                "diagnostic": dict(diag_row) if diag_row else None,
                "locations": [dict(r) for r in loc_rows],
                "patches": [dict(r) for r in patch_rows],
            }

    def list_experiments(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List summary of recent experiments."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM experiments ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
