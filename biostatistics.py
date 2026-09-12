"""Transparent statistical metrics for aggregate Q3 facility data."""
from __future__ import annotations
from typing import Any
import math
import numpy as np
import pandas as pd

def descriptive(values: pd.Series | list[float]) -> dict[str, float | None]:
    x = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    if len(x) == 0:
        return {"n": 0, "mean": None, "median": None, "std": None, "min": None, "max": None}
    return {"n": int(len(x)), "mean": float(np.mean(x)), "median": float(np.median(x)), "std": float(np.std(x, ddof=1)) if len(x) > 1 else 0.0, "min": float(np.min(x)), "max": float(np.max(x))}

def _continuity(a: float, b: float, c: float, d: float) -> tuple[float, float, float, float]:
    vals = [float(a), float(b), float(c), float(d)]
    return tuple(v + 0.5 if v == 0 else v for v in vals)

def risk_ratio(exposed_cases: float, exposed_total: float, unexposed_cases: float, unexposed_total: float) -> float | None:
    if exposed_total <= 0 or unexposed_total <= 0: return None
    return (exposed_cases / exposed_total) / (unexposed_cases / unexposed_total) if unexposed_cases > 0 else math.inf

def odds_ratio(exposed_cases: float, exposed_total: float, unexposed_cases: float, unexposed_total: float) -> float | None:
    a, b, c, d = _continuity(exposed_cases, exposed_total - exposed_cases, unexposed_cases, unexposed_total - unexposed_cases)
    return (a / b) / (c / d) if b and c else None

def epidemiology_scenarios(services: pd.DataFrame, epi: pd.DataFrame) -> pd.DataFrame:
    """Return clearly labeled proxy comparisons, not causal estimates."""
    screening = float(services.loc[services.indicator == "Nutrition screening", "total"].iloc[0])
    mal = float(services.loc[services.indicator == "Malnutrition", "total"].iloc[0])
    epi_total = 300.0
    measles = float(epi.loc[epi.antigen == "Measles", "total"].iloc[0])
    incomplete = epi_total - measles
    rows = [{
        "scenario": "Malnutrition proxy: screened vs not screened",
        "exposure_definition": "Screened children; facility aggregate proxy only",
        "exposed_cases": mal, "exposed_total": screening,
        "unexposed_cases": 0.0, "unexposed_total": max(0.0, epi_total-screening),
        "risk_ratio": None, "odds_ratio": None,
        "interpretation": "Not estimable from aggregate data; no linked outcome denominator."
    }, {
        "scenario": "Incomplete measles dose proxy vs measles dose",
        "exposure_definition": "Children without recorded measles dose in EPI denominator; not infection status",
        "exposed_cases": incomplete, "exposed_total": epi_total,
        "unexposed_cases": measles, "unexposed_total": epi_total,
        "risk_ratio": risk_ratio(incomplete, epi_total, measles, epi_total),
        "odds_ratio": odds_ratio(incomplete, epi_total, measles, epi_total),
        "interpretation": "Coverage contrast, not a disease risk estimate; denominator is aggregate and may not be a cohort."
    }]
    return pd.DataFrame(rows)

def root_cause_actions() -> pd.DataFrame:
    return pd.DataFrame([
        {"driver": "Suboptimal breastfeeding", "pathway": "Lack of exclusive breastfeeding under six months may increase vulnerability to MAM/SAM.", "indicator": "Malnutrition: 150 / 600 = 25.0%", "action": "Strengthen breastfeeding counselling, early postnatal follow-up, and referral tracking."},
        {"driver": "Incomplete immunization", "pathway": "Gaps in age-appropriate vaccination can increase susceptibility to vaccine-preventable infections.", "indicator": "Measles recorded dose: 158 / 300 = 52.7%", "action": "Use defaulter tracing, outreach sessions, and antigen-specific register reconciliation."},
        {"driver": "Sanitation and hygiene gaps", "pathway": "Unsafe water, sanitation, and hand hygiene can sustain diarrhoeal transmission.", "indicator": "Handwashing intervention coverage not provided", "action": "Add hygiene-promotion denominator and pre/post diarrhoea monitoring to the next reporting cycle."},
    ])

def key_metrics(services: pd.DataFrame, epi: pd.DataFrame) -> dict[str, float]:
    row = lambda label: float(services.loc[services.indicator == label, "total"].iloc[0])
    return {"opd_total": row("OPD over 5 years") + row("OPD under 5 years"), "under5_share": row("OPD under 5 years") / (row("OPD over 5 years") + row("OPD under 5 years")), "malnutrition_rate": row("Malnutrition") / row("Nutrition screening"), "delivery_complication_rate": row("Deliveries with complications") / row("Deliveries"), "measles_coverage": float(epi.loc[epi.antigen == "Measles", "total"].iloc[0]) / 300.0}
