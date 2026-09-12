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
    
    # Halkan ayaa lagu hagaajiyay
    measles = safe_epi("Measles")
    epi_total = float(epi["total"].sum())  # Wadarta guud ee dhammaan antigens-ka EPI
    
    total_opd = opd_over + opd_under
    
    return {
        "opd_total": total_opd,
        "under5_share": (opd_under / total_opd) if total_opd > 0 else 0.0,
        "malnutrition_rate": (mal / screening) if screening > 0 else 0.0,
        "delivery_complication_rate": (comp_deliveries / deliveries) if deliveries > 0 else 0.0,
        # Halkan ayaa lagu hagaajiyay: 300.0 waa laga saaray
        "measles_coverage": measles / epi_total if epi_total > 0 else 0.0 
    }
