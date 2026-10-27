"""Strategy Selector: Rule-based and historical feedback strategy selection."""

from typing import Dict, List, Optional
from the_machine.core.database import ExperimentDatabase
from the_machine.core.models import TestExecutionReport


class StrategySelector:
    """Selects and orders repair strategies based on diagnostic indicators and historical evidence."""

    def __init__(self, db: Optional[ExperimentDatabase] = None):
        self.db = db

    def select_strategies(
        self,
        report: TestExecutionReport,
        available_strategies: List[str],
    ) -> List[str]:
        """
        Rank available repair strategies.
        If historical evaluations exist, weights strategies by empirical acceptance rate.
        Otherwise, applies rule-based heuristic prioritization.
        """
        if not available_strategies:
            return []

        # Heuristic default ranking: deterministic templates first, followed by bounded search and neural synthesis
        default_order = ["deterministic_template", "search_ast", "neural_llm"]

        # If DB is available, compute historical success rate
        historical_scores = self._compute_historical_weights(available_strategies)
        if historical_scores:
            ranked = sorted(
                available_strategies,
                key=lambda s: historical_scores.get(s, 0.0),
                reverse=True,
            )
            return ranked

        # Rule-based fallback: sort by default order
        return sorted(
            available_strategies,
            key=lambda s: default_order.index(s) if s in default_order else 99,
        )

    def _compute_historical_weights(self, strategies: List[str]) -> Dict[str, float]:
        """Compute accepted/evaluated ratio from database for each strategy."""
        if not self.db:
            return {}

        weights = {}
        try:
            with self.db._get_connection() as conn:
                for strat in strategies:
                    row = conn.execute(
                        """
                        SELECT
                            COUNT(*) as total,
                            SUM(CASE WHEN validation_status = 'ACCEPTED' THEN 1 ELSE 0 END) as accepted
                        FROM patch_evaluations
                        WHERE strategy_name = ?
                        """,
                        (strat,),
                    ).fetchone()
                    if row and row["total"] > 0:
                        total = row["total"]
                        acc = row["accepted"] or 0
                        # Empirical Bayesian posterior mean with Beta(1, 1) prior
                        score = (acc + 1.0) / (total + 2.0)
                        weights[strat] = score
        except Exception:
            return {}

        return weights
