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


def validate_gender_consistency(df: pd.DataFrame, name: str) -> str | None:
    """Hubi in male + female = total. Soo celi digniin haddii aanay is waafaqsanayn."""
    if all(col in df.columns for col in ["male", "female", "total"]):
        complete = df[["male", "female", "total"]].dropna()
        if not complete.empty:
            mismatch = complete[complete["male"] + complete["female"] != complete["total"]]
            if not mismatch.empty:
                return f"{name}: {len(mismatch)} saf ayaa male + female ≠ total"
    return None


def validate_duplicates(df: pd.DataFrame, name: str, subset: list[str]) -> str | None:
    """Hubi in aanay jirin safafka isku midka ah."""
    existing = [c for c in subset if c in df.columns]
    if existing:
        dupes = df.duplicated(subset=existing, keep=False)
        if dupes.any():
            return f"{name}: {dupes.sum()} saf ayaa isku mid ah ({', '.join(existing)})"
    return None


def validate_outliers(df: pd.DataFrame, name: str, threshold: float = 3.0) -> str | None:
    """Hubi in aanay jirin qiimaha aad uga fog (outliers) ee tirada."""
    if "total" in df.columns:
        x = pd.to_numeric(df["total"], errors="coerce").dropna()
        if len(x) > 3:
            mean, std = x.mean(), x.std()
            if std > 0:
                outliers = x[(x - mean).abs() > threshold * std]
                if not outliers.empty:
                    return f"{name}: {len(outliers)} qiime ayaa ka fog (>{threshold}σ)"
    return None


def validate(data: dict[str, pd.DataFrame]) -> QualityReport:
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    missing: list[str] = []

    svc, dis, epi = data["services"], data["diseases"], data["epi"]

    def check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    # 1. Required tables present
    check(
        "Required tables present",
        set(data) == {"services", "diseases", "epi"},
        "services, diseases, epi",
    )

    # 2. No negative counts
    nonnegative = all(
        pd.to_numeric(df["total"], errors="coerce").dropna().ge(0).all()
        for df in data.values()
    )
    check("No negative counts", nonnegative, "Negative counts are invalid")

    # 3. Missing value detection
    for label, df in [("services", svc), ("diseases", dis), ("epi", epi)]:
        for col in ["total", "male", "female"]:
            if col in df and df[col].isna().any():
                missing.append(f"{label}.{col}")

    # 4. Gender reconciliation ee services
    complete_gender = svc[["total", "male", "female"]].dropna()
    gender_reconciles = bool(
        (
            complete_gender["male"].astype(float)
            + complete_gender["female"].astype(float)
            == complete_gender["total"].astype(float)
        ).all()
    )
    check(
        "Provided gender totals reconcile",
        gender_reconciles,
        "OPD and nutrition rows with supplied sex counts",
    )

    # 5. Nutrition sex counts reconcile
    nutrition = svc[svc["indicator"] == "Nutrition screening"]
    nutrition_reconciles = bool(
        (
            nutrition["male"].astype(float) + nutrition["female"].astype(float)
            == nutrition["total"].astype(float)
        ).all()
    )
    check("Nutrition sex counts reconcile", nutrition_reconciles, "235 + 265 = 600")

    # =========================================================
    # CHECKS CUSUB (oo lagu daray)
    # =========================================================

    # 6. Gender consistency ee diseases iyo epi
    for name, df in [("diseases", dis), ("epi", epi)]:
        w = validate_gender_consistency(df, name)
        if w:
            warnings.append(w)

    # 7. Duplicate check
    w = validate_duplicates(dis, "diseases", ["period", "age_group", "disease"])
    if w:
        warnings.append(w)
    w = validate_duplicates(epi, "epi", ["period", "antigen"])
    if w:
        warnings.append(w)
    w = validate_duplicates(svc, "services", ["period", "domain", "indicator"])
    if w:
        warnings.append(w)

    # 8. Outlier check
    for name, df in [("services", svc), ("diseases", dis), ("epi", epi)]:
        w = validate_outliers(df, name, threshold=3.0)
        if w:
            warnings.append(w)

    # 9. Digniino ku saabsan xogta maqan (hadda la beddelay)
    if dis["total"].isna().any() if "total" in dis else False:
        warnings.append(
            "Disease-level totals and sex breakdowns were not supplied; retained as missing rather than imputed."
        )
    if epi["total"].isna().any() if "total" in epi else False:
        warnings.append(
            "IPV 1-3 and Penta 1-3 counts were not supplied; coverage cannot be computed for these antigens."
        )
    if missing:
        warnings.append(f"Missing-value fields detected: {', '.join(sorted(set(missing)))}")

    return QualityReport(checks=checks, missing_fields=sorted(set(missing)), warnings=warnings)


def prepare(data_dir: str | Path) -> tuple[dict[str, pd.DataFrame], QualityReport]:
    cleaned = clean_data(load_data(data_dir))
    return cleaned, validate(cleaned)
