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
    return {
        "n": int(len(x)),
        "mean": float(np.mean(x)),
        "median": float(np.median(x)),
        "std": float(np.std(x, ddof=1)) if len(x) > 1 else 0.0,
        "min": float(np.min(x)),
        "max": float(np.max(x)),
    }


def _continuity(a: float, b: float, c: float, d: float) -> tuple[float, float, float, float]:
    vals = [float(a), float(b), float(c), float(d)]
    return tuple(v + 0.5 if v == 0 else v for v in vals)


def risk_ratio(
    exposed_cases: float,
    exposed_total: float,
    unexposed_cases: float,
    unexposed_total: float,
) -> float | None:
    if exposed_total <= 0 or unexposed_total <= 0:
        return None
    return (
        (exposed_cases / exposed_total) / (unexposed_cases / unexposed_total)
        if unexposed_total > 0
        else math.inf
    )


def odds_ratio(
    exposed_cases: float,
    exposed_total: float,
    unexposed_cases: float,
    unexposed_total: float,
) -> float | None:
    a, b, c, d = _continuity(
        exposed_cases,
        exposed_total - exposed_cases,
        unexposed_cases,
        unexposed_total - unexposed_cases,
    )
    return (a / b) / (c / d) if b and c else None


def epidemiology_scenarios(services: pd.DataFrame, epi: pd.DataFrame) -> pd.DataFrame:
    def get_service(label):
        match = services.loc[services.indicator == label, "total"]
        return float(match.sum()) if not match.empty else 0.0

    def get_epi(antigen_name):
        match = epi.loc[epi.antigen == antigen_name, "total"]
        return float(match.sum()) if not match.empty else 0.0

    screening = get_service("Nutrition screening")
    mal = get_service("Malnutrition")

    epi_total = float(epi["total"].sum()) if not epi.empty else 0.0
    measles = get_epi("Measles")
    incomplete = max(0.0, epi_total - measles)

    rows = [
        {
            "scenario": "Malnutrition proxy: screened vs not screened",
            "exposure_definition": "Screened children; facility aggregate proxy only",
            "exposed_cases": mal,
            "exposed_total": screening,
            "unexposed_cases": 0.0,
            "unexposed_total": max(0.0, epi_total - screening),
            "risk_ratio": None,
            "odds_ratio": None,
            "interpretation": "Not estimable from aggregate data; no linked outcome denominator.",
        },
        {
            "scenario": "Incomplete measles dose proxy vs measles dose",
            "exposure_definition": "Children without recorded measles dose in EPI denominator; not infection status",
            "exposed_cases": incomplete,
            "exposed_total": epi_total,
            "unexposed_cases": measles,
            "unexposed_total": epi_total,
            "risk_ratio": risk_ratio(incomplete, epi_total, measles, epi_total),
            "odds_ratio": odds_ratio(incomplete, epi_total, measles, epi_total),
            "interpretation": "Coverage contrast, not a disease risk estimate; denominator is aggregate and may not be a cohort.",
        },
    ]
    return pd.DataFrame(rows)


def root_cause_actions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "driver": "Suboptimal breastfeeding",
                "pathway": "Lack of exclusive breastfeeding under six months may increase vulnerability to MAM/SAM.",
                "indicator": "Malnutrition: 150 / 600 = 25.0%",
                "action": "Strengthen breastfeeding counselling, early postnatal follow-up, and referral tracking.",
            },
            {
                "driver": "Incomplete immunization",
                "pathway": "Gaps in age-appropriate vaccination can increase susceptibility to vaccine-preventable infections.",
                "indicator": "Measles coverage review",
                "action": "Use defaulter tracing, outreach sessions, and antigen-specific register reconciliation.",
            },
            {
                "driver": "Sanitation and hygiene gaps",
                "pathway": "Unsafe water, sanitation, and hand hygiene can sustain diarrhoeal transmission.",
                "indicator": "Handwashing intervention coverage not provided",
                "action": "Add hygiene-promotion denominator and pre/post diarrhoea monitoring to the next reporting cycle.",
            },
        ]
    )


def key_metrics(services: pd.DataFrame, epi: pd.DataFrame) -> dict[str, float]:
    def safe_row(label):
        match = services.loc[services.indicator == label, "total"]
        return float(match.sum()) if not match.empty else 0.0

    def safe_epi(antigen_name):
        match = epi.loc[epi.antigen == antigen_name, "total"]
        return float(match.sum()) if not match.empty else 0.0

    opd_over = safe_row("OPD over 5 years")
    opd_under = safe_row("OPD under 5 years")
    mal = safe_row("Malnutrition")
    screening = safe_row("Nutrition screening")
    deliveries = safe_row("Deliveries")
    comp_deliveries = safe_row("Deliveries with complications")
    measles = safe_epi("Measles")

    epi_total = float(epi["total"].sum()) if not epi.empty else 0.0
    total_opd = opd_over + opd_under

    return {
        "opd_total": total_opd,
        "under5_share": (opd_under / total_opd) if total_opd > 0 else 0.0,
        "malnutrition_rate": (mal / screening) if screening > 0 else 0.0,
        "delivery_complication_rate": (comp_deliveries / deliveries)
        if deliveries > 0
        else 0.0,
        "measles_coverage": measles / epi_total if epi_total > 0 else 0.0,
    }


def disease_risk_ratios(diseases: pd.DataFrame) -> pd.DataFrame:
    """Xisaabi Risk Ratio ee cudur kasta: under_5 vs over_5."""
    if diseases.empty:
        return pd.DataFrame()

    rows = []
    total_under = diseases[diseases["age_group"] == "under_5"]["total"].sum()
    total_over = diseases[diseases["age_group"] == "over_5"]["total"].sum()

    for disease_name in sorted(diseases["disease"].dropna().unique()):
        d = diseases[diseases["disease"] == disease_name]
        under5 = d[d["age_group"] == "under_5"]["total"].sum()
        over5 = d[d["age_group"] == "over_5"]["total"].sum()

        if total_under > 0 and total_over > 0 and over5 > 0:
            rr = (under5 / total_under) / (over5 / total_over)
        else:
            rr = None

        if rr is None:
            interpretation = "Not estimable"
        elif rr > 1.2:
            interpretation = "Under-5 higher risk"
        elif rr < 0.8:
            interpretation = "Over-5 higher risk"
        else:
            interpretation = "Similar risk"

        rows.append(
            {
                "disease": disease_name,
                "under5_cases": int(under5),
                "over5_cases": int(over5),
                "risk_ratio_under5_vs_over5": round(rr, 2) if rr is not None else None,
                "interpretation": interpretation,
            }
        )

    return pd.DataFrame(rows)
