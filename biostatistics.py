def key_metrics(services: pd.DataFrame, epi: pd.DataFrame) -> dict[str, float]:
    def safe_row(label):
        match = services.loc[services.indicator == label, "total"]
        return float(match.iloc[0]) if not match.empty else 0.0
        
    opd_over = safe_row("OPD over 5 years")
    opd_under = safe_row("OPD under 5 years")
    mal = safe_row("Malnutrition")
    screening = safe_row("Nutrition screening")
    deliveries = safe_row("Deliveries")
    comp_deliveries = safe_row("Deliveries with complications")
    
    measles_match = epi.loc[epi.antigen == "Measles", "total"]
    measles = float(measles_match.iloc[0]) if not measles_match.empty else 0.0
    
    total_opd = opd_over + opd_under
    
    return {
        "opd_total": total_opd,
        "under5_share": (opd_under / total_opd) if total_opd > 0 else 0.0,
        "malnutrition_rate": (mal / screening) if screening > 0 else 0.0,
        "delivery_complication_rate": (comp_deliveries / deliveries) if deliveries > 0 else 0.0,
        "measles_coverage": measles / 300.0
    }
