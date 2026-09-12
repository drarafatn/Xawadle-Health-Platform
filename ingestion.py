"""Data ingestion and quality controls for Xawadle Q3 aggregate data."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

@dataclass
class QualityReport:
    checks: list[dict[str, Any]]
    missing_fields: list[str]
    warnings: list[str]
    @property
    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks)

def _numericize(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col in out:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out

def load_data(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    services = pd.read_csv(data_dir / "service_totals.csv")
    diseases = pd.read_csv(data_dir / "opd_disease_counts.csv")
    epi = pd.read_csv(data_dir / "epi_coverage.csv")
    services = _numericize(services, ["total", "male", "female"])
    diseases = _numericize(diseases, ["total", "male", "female"])
    epi = _numericize(epi, ["total", "male", "female"])
    return {"services": services, "diseases": diseases, "epi": epi}

def clean_data(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    cleaned = {}
    for name, frame in data.items():
        df = frame.copy()
        df.columns = [c.strip().lower() for c in df.columns]
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].astype("string").str.strip().replace({"": pd.NA, "nan": pd.NA})
        for col in ["total", "male", "female"]:
            if col in df:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        cleaned[name] = df
    return cleaned

def validate(data: dict[str, pd.DataFrame]) -> QualityReport:
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    missing: list[str] = []
    svc, dis, epi = data["services"], data["diseases"], data["epi"]
    def check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
    check("Required tables present", set(data) == {"services", "diseases", "epi"}, "services, diseases, epi")
    nonnegative = all(pd.to_numeric(df["total"], errors="coerce").dropna().ge(0).all() for df in data.values())
    check("No negative counts", nonnegative, "Negative counts are invalid")
    for label, df in [("services", svc), ("diseases", dis), ("epi", epi)]:
        for col in ["total", "male", "female"]:
            if col in df and df[col].isna().any():
                missing.append(f"{label}.{col}")
    complete_gender = svc[["total", "male", "female"]].dropna()
    gender_reconciles = bool((complete_gender["male"].astype(float) + complete_gender["female"].astype(float) == complete_gender["total"].astype(float)).all())
    check("Provided gender totals reconcile", gender_reconciles, "OPD and nutrition rows with supplied sex counts")
    nutrition = svc[svc["indicator"] == "Nutrition screening"]
    nutrition_reconciles = bool((nutrition["male"].astype(float) + nutrition["female"].astype(float) == nutrition["total"].astype(float)).all())
    check("Nutrition sex counts reconcile", nutrition_reconciles, "235 + 265 = 600")
    warnings.append("Disease-level totals and sex breakdowns were not supplied; retained as missing rather than imputed.")
    warnings.append("IPV 1-3 and Penta 1-3 counts were not supplied; coverage cannot be computed for these antigens.")
    if missing:
        warnings.append(f"Missing-value fields detected: {', '.join(sorted(set(missing)))}")
    return QualityReport(checks=checks, missing_fields=sorted(set(missing)), warnings=warnings)

def prepare(data_dir: str | Path) -> tuple[dict[str, pd.DataFrame], QualityReport]:
    cleaned = clean_data(load_data(data_dir))
    return cleaned, validate(cleaned)
