"""Data ingestion and quality checks for the Xawadle Health Platform."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd


# =========================================================
# DATA QUALITY CONTAINER
# =========================================================
@dataclass
class QualityReport:
    checks: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passed: bool = True


def check(name: str, condition: bool, detail: str, report: QualityReport) -> None:
    """Add a quality check result to the report."""
    report.checks.append({"name": name, "passed": bool(condition), "detail": detail})
    if not condition:
        report.passed = False


# =========================================================
# DATA LOADING
# =========================================================
def _load_csv(path: Path, required_cols: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path.name}")
    df = pd.read_csv(path)
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name} missing columns: {missing}")
    return df


# =========================================================
# MAIN PREPARE FUNCTION
# =========================================================
def prepare(data_dir: Path) -> tuple[dict[str, pd.DataFrame], QualityReport]:
    """Load and validate all source CSV files, returning data and a quality report."""
    report = QualityReport()

    # ---- Load files ----
    try:
        services = _load_csv(
            data_dir / "service_totals.csv",
            ["period", "domain", "indicator", "total", "male", "female"],
        )
    except Exception as e:
        services = pd.DataFrame()
        report.warnings.append(f"service_totals.csv: {e}")

    try:
        diseases = _load_csv(
            data_dir / "opd_disease_counts.csv",
            ["period", "disease", "age_group", "total", "male", "female"],
        )
    except Exception as e:
        diseases = pd.DataFrame()
        report.warnings.append(f"opd_disease_counts.csv: {e}")

    try:
        epi = _load_csv(
            data_dir / "epi_coverage.csv",
            ["period", "antigen", "total", "male", "female"],
        )
    except Exception as e:
        epi = pd.DataFrame()
        report.warnings.append(f"epi_coverage.csv: {e}")

    # ---- Data quality checks ----

    # 1. Required tables present
    tables_present = all(
        not df.empty for df in [services, diseases, epi]
    )
    check(
        "Required tables present",
        tables_present,
        "services, diseases, epi",
        report,
    )

    # 2. No negative counts
    negative_found = False
    for df, name in [(services, "services"), (diseases, "diseases"), (epi, "epi")]:
        if df.empty:
            continue
        numeric_cols = df.select_dtypes(include="number").columns
        if (df[numeric_cols] < 0).any().any():
            negative_found = True
            report.warnings.append(f"Negative counts found in {name}")
    check(
        "No negative counts",
        not negative_found,
        "Negative counts are invalid",
        report,
    )

    # 3. Provided gender totals reconcile
    gender_reconciles = True
    if not services.empty:
        mask = services["male"].notna() & services["female"].notna() & services["total"].notna()
        if mask.any():
            gender_reconciles = bool(
                (
                    services.loc[mask, "male"].astype(float)
                    + services.loc[mask, "female"].astype(float)
                    == services.loc[mask, "total"].astype(float)
                ).all()
            )
    check(
        "Provided gender totals reconcile",
        gender_reconciles,
        "OPD and nutrition rows with supplied sex counts",
        report,
    )

    # 4. Nutrition sex counts reconcile
    if not services.empty:
        nutrition = services[services["indicator"] == "Nutrition screening"]
        total_male = int(nutrition["male"].sum())
        total_female = int(nutrition["female"].sum())
        total_all = int(nutrition["total"].sum())

        nutrition_reconciles = bool(
            (
                nutrition["male"].astype(float)
                + nutrition["female"].astype(float)
                == nutrition["total"].astype(float)
            ).all()
        )
        check(
            "Nutrition sex counts reconcile",
            nutrition_reconciles,
            f"{total_male} + {total_female} = {total_all}",
            report,
        )

    # 5. EPI sex counts reconcile
    if not epi.empty:
        epi_male = int(epi["male"].sum())
        epi_female = int(epi["female"].sum())
        epi_total = int(epi["total"].sum())

        epi_reconciles = bool(
            (
                epi["male"].astype(float) + epi["female"].astype(float)
                == epi["total"].astype(float)
            ).all()
        )
        check(
            "EPI sex counts reconcile",
            epi_reconciles,
            f"{epi_male} + {epi_female} = {epi_total}",
            report,
        )

    # ---- Return ----
    return {"services": services, "diseases": diseases, "epi": epi}, report
