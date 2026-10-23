"""AI benchmark testing and evaluation utilities."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class BenchmarkResult:
    metrics: dict[str, float]


def example_synthetic_benchmark() -> BenchmarkResult:
    """Returns deterministic synthetic benchmark metrics for demonstration."""
    return BenchmarkResult(
        metrics={
            "accuracy": 0.854,
            "demographic_parity_gap": 0.032,
        }
    )


def benchmark_predictions(y_true, y_pred, group=None) -> dict[str, float]:
    """Evaluate predictions against true labels with optional group fairness metrics."""
    y_t = np.array(y_true)
    y_p = np.array(y_pred)
    accuracy = float(np.mean(y_t == y_p)) if len(y_t) > 0 else 0.0
    
    parity_gap = 0.0
    if group is not None:
        g = np.array(group)
        df_eval = pd.DataFrame({"y_true": y_t, "y_pred": y_p, "group": g})
        groups = df_eval["group"].unique()
        if len(groups) == 2:
            accs = [
                float(np.mean(df_eval[df_eval["group"] == grp]["y_true"] == df_eval[df_eval["group"] == grp]["y_pred"]))
                for grp in groups
            ]
            parity_gap = float(abs(accs[0] - accs[1]))

    return {
        "accuracy": accuracy,
        "demographic_parity_gap": parity_gap,
    }
