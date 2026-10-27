"""Experiment Manager: Orchestrates end-to-end repair experiments with full isolation."""

import shutil
import time
import uuid
from pathlib import Path
from typing import Optional
from the_machine.core.database import ExperimentDatabase
from the_machine.core.models import (
    ExperimentConfig,
    ExperimentStatus,
    ExperimentSummary,
    MutationRecord,
    PatchCandidate,
    TestExecutionReport,
    ValidationResult,
    ValidationStatus,
)
from the_machine.engine.failure_detector import FailureDetector
from the_machine.engine.fault_injector import FaultInjector
from the_machine.engine.fault_localizer import FaultLocalizer
from the_machine.engine.repair_engine import RepairEngine
from the_machine.engine.strategy_selector import StrategySelector
from the_machine.engine.validation_engine import ValidationEngine
from the_machine.engine.coverage_collector import CoverageCollector


class ExperimentManager:
    """Coordinates isolated workspaces, lifecycle telemetry, and repair execution."""

    def __init__(
        self,
        base_workspace_dir: Optional[Path] = None,
        db: Optional[ExperimentDatabase] = None,
    ):
        self.base_workspace_dir = Path(base_workspace_dir or ".machine_workspaces").resolve()
        self.base_workspace_dir.mkdir(parents=True, exist_ok=True)
        self.db = db or ExperimentDatabase()
        self.failure_detector = FailureDetector()
        self.fault_localizer = FaultLocalizer()
        self.repair_engine = RepairEngine()
        self.validation_engine = ValidationEngine(self.failure_detector)
        self.strategy_selector = StrategySelector(self.db)
        self.coverage_collector = CoverageCollector()

    def provision_workspace(self, experiment_id: str, source_target_dir: Path) -> Path:
        """Create an isolated, disposable replica of the target project directory."""
        workspace_path = self.base_workspace_dir / experiment_id
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
        shutil.copytree(source_target_dir, workspace_path)
        return workspace_path

    def cleanup_workspace(self, experiment_id: str) -> None:
        """Purge disposable workspace to conserve disk space."""
        workspace_path = self.base_workspace_dir / experiment_id
        if workspace_path.exists():
            shutil.rmtree(workspace_path, ignore_errors=True)

    def run_repair_cycle(
        self,
        target_dir: Path,
        config: ExperimentConfig,
        operator_name: str = "COM",
        mutation_line: Optional[int] = None,
        cleanup_after: bool = True,
    ) -> ExperimentSummary:
        """
        Execute a complete, reproducible Phase 1 repair cycle:
        1. Provision isolated workspace.
        2. Inject controlled mutation.
        3. Detect failure and collect stack trace.
        4. Localize suspicious statements.
        5. Select repair strategies.
        6. Synthesize candidate patches.
        7. Validate candidates against test & regression suite.
        8. Record all telemetry in SQLite.
        9. Safely restore and clean up workspace.
        """
        start_time = time.time()
        experiment_id = f"exp_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        self.db.record_experiment_start(experiment_id, config)

        summary = ExperimentSummary(
            experiment_id=experiment_id,
            status=ExperimentStatus.INITIALIZED,
            target_name=config.target_name,
            config=config,
            created_at=start_time,
        )

        workspace_path = self.provision_workspace(experiment_id, target_dir)
        target_code_file = workspace_path / config.target_rel_path

        try:
            # Step 1: Fault Injection
            injector = FaultInjector(allowed_paths=[str(workspace_path)])
            mutation = injector.inject_mutation(
                target_code_file,
                operator_name=operator_name,
                target_line=mutation_line,
            )
            summary.mutation = mutation
            self.db.record_mutation(experiment_id, mutation)

            # Step 2: Failure Detection
            detection_report = self.failure_detector.run_tests(
                workspace_path,
                test_target=config.test_rel_path,
                timeout_sec=config.timeout_sec,
            )
            summary.baseline_report = detection_report
            self.db.record_diagnostic(experiment_id, detection_report)

            if detection_report.passed:
                # Mutation did not produce a detectable failure
                summary.status = ExperimentStatus.UNRESOLVED
                self.db.finish_experiment(experiment_id, summary.status, time.time() - start_time)
                return summary

            summary.status = ExperimentStatus.FAILED_DETECTED

            # Step 3: Fault Localization (SBFL + Stack Trace Slicing)
            failing_test_ids = {f.test_id for f in detection_report.failures}
            matrix = self.coverage_collector.collect_matrix(
                workspace_path=workspace_path,
                target_rel_path=config.target_rel_path,
                test_rel_path=config.test_rel_path,
                failing_tests=failing_test_ids,
            )

            locations = self.fault_localizer.localize_fault(
                report=detection_report,
                workspace_path=workspace_path,
                matrix=matrix,
                metric_name="ochiai",
            )
            summary.suspicious_locations = locations
            self.db.record_locations(experiment_id, locations)

            # Evaluate localization accuracy against ground truth mutation
            if summary.mutation:
                loc_metrics = self.fault_localizer.evaluate_localization(
                    ranked_locations=locations,
                    ground_truth_line=summary.mutation.line_number,
                    window=2,
                )
                summary.localization_metrics = loc_metrics
                self.db.record_localization_metrics(experiment_id, loc_metrics)

            summary.status = ExperimentStatus.LOCALIZED

            # Step 4: Strategy Selection
            ordered_strategies = self.strategy_selector.select_strategies(
                detection_report, config.enabled_strategies
            )

            # Step 5: Candidate Patch Synthesis
            candidates = self.repair_engine.synthesize_candidates(
                locations=locations,
                report=detection_report,
                workspace_path=workspace_path,
                enabled_strategies=ordered_strategies,
                max_candidates=config.max_candidates,
            )

            # Step 6: Patch Validation
            failing_test_name = detection_report.failures[0].test_id if detection_report.failures else None

            for candidate in candidates:
                summary.candidates_evaluated += 1
                validation = self.validation_engine.validate_patch(
                    candidate=candidate,
                    workspace_path=workspace_path,
                    failing_test_id=failing_test_name,
                    timeout_sec=config.timeout_sec,
                    verify_flakiness=config.verify_flakiness,
                    flakiness_runs=config.flakiness_runs,
                )
                self.db.record_patch_evaluation(experiment_id, candidate, validation)

                if validation.status == ValidationStatus.ACCEPTED:
                    summary.accepted_patch = candidate
                    summary.accepted_validation = validation
                    summary.status = ExperimentStatus.REPAIRED
                    break

            if summary.status != ExperimentStatus.REPAIRED:
                summary.status = ExperimentStatus.UNRESOLVED

        except Exception as exc:
            summary.status = ExperimentStatus.ERROR
            raise exc

        finally:
            total_duration = time.time() - start_time
            summary.total_duration_sec = total_duration
            self.db.finish_experiment(experiment_id, summary.status, total_duration)

            if cleanup_after:
                self.cleanup_workspace(experiment_id)

        return summary
