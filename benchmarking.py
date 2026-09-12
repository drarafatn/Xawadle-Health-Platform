"""AI benchmark interfaces that work with predictions or approved clinical rules."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Iterable
import numpy as np
import pandas as pd

@dataclass
class BenchmarkResult:
    name: str
    metrics: dict[str, float | None]
    notes: str

def classification_metrics(y_true: Iterable[int], y_pred: Iterable[int]) -> dict[str, float | None]:
    y, p = np.asarray(list(y_true), dtype=int), np.asarray(list(y_pred), dtype=int)
    if len(y) != len(p) or len(y) == 0: raise ValueError("y_true and y_pred must be non-empty and equal length")
    tp, tn = int(((y==1)&(p==1)).sum()), int(((y==0)&(p==0)).sum())
    fp, fn = int(((y==0)&(p==1)).sum()), int(((y==1)&(p==0)).sum())
    return {"n": float(len(y)), "accuracy": (tp+tn)/len(y), "sensitivity": tp/(tp+fn) if tp+fn else None, "specificity": tn/(tn+fp) if tn+fp else None, "ppv": tp/(tp+fp) if tp+fp else None, "npv": tn/(tn+fn) if tn+fn else None}

def fairness_metrics(y_true: Iterable[int], y_pred: Iterable[int], group: Iterable[str]) -> pd.DataFrame:
    frame = pd.DataFrame({"y": list(y_true), "p": list(y_pred), "group": list(group)})
    rows=[]
    for g, d in frame.groupby("group", dropna=False):
        m=classification_metrics(d.y, d.p)
        rows.append({"group":g, "selection_rate":float(d.p.mean()), "tpr":m["sensitivity"], "tnr":m["specificity"], "n":len(d)})
    return pd.DataFrame(rows)

def demographic_parity_gap(fairness: pd.DataFrame) -> float | None:
    if len(fairness) < 2: return None
    return float(fairness.selection_rate.max() - fairness.selection_rate.min())

def benchmark_predictions(y_true: Iterable[int], y_pred: Iterable[int], group: Iterable[str] | None = None) -> dict:
    metrics = classification_metrics(y_true, y_pred)
    out = {"diagnostic_metrics": metrics}
    if group is not None:
        fair = fairness_metrics(y_true, y_pred, group)
        out["fairness_by_group"] = fair.to_dict(orient="records")
        out["demographic_parity_gap"] = demographic_parity_gap(fair)
    return out

def run_cds_rule(frame: pd.DataFrame, rule: Callable[[pd.Series], int]) -> pd.Series:
    """Run a clinician-approved row-wise rule; no rule is enabled by default."""
    return frame.apply(rule, axis=1).astype(int)

def example_synthetic_benchmark() -> BenchmarkResult:
    """A deterministic software smoke-test only; not a clinical performance claim."""
    y=np.array([1,1,1,0,0,0,1,0]); p=np.array([1,0,1,0,0,1,1,0]); g=np.array(["F","F","M","M","F","M","F","M"])
    result=benchmark_predictions(y,p,g)
    return BenchmarkResult("deterministic smoke test", {"accuracy": result["diagnostic_metrics"]["accuracy"], "demographic_parity_gap": result["demographic_parity_gap"]}, "Synthetic test vectors validate metric plumbing only.")
