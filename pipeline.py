"""End-to-end Q3 pipeline orchestration."""
from __future__ import annotations
import json
from pathlib import Path
from .ingestion import prepare
from .biostatistics import descriptive, epidemiology_scenarios, key_metrics, root_cause_actions

def run(data_dir: str | Path) -> dict:
    data, quality = prepare(data_dir)
    services, epi = data["services"], data["epi"]
    metric_values = services.loc[services["total"].notna(), "total"]
    return {"period": "Q3 (July–September)", "facility": "Xawadle Health Centre", "quality": {"passed": quality.passed, "checks": quality.checks, "missing_fields": quality.missing_fields, "warnings": quality.warnings}, "key_metrics": key_metrics(services, epi), "descriptive_service_totals": descriptive(metric_values), "epidemiology_scenarios": epidemiology_scenarios(services, epi).to_dict(orient="records"), "root_cause_actions": root_cause_actions().to_dict(orient="records")}

def export(data_dir: str | Path, output: str | Path) -> None:
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(run(data_dir), indent=2), encoding="utf-8")
