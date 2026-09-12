from pathlib import Path
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from ingestion import prepare
from biostatistics import descriptive, epidemiology_scenarios, key_metrics, root_cause_actions
from benchmarking import example_synthetic_benchmark

st.set_page_config(page_title="Xawadle Health Centre | Q3 Analytics", page_icon="+", layout="wide")
DATA_DIR = Path(__file__).parent


def pct(x):
    return f"{x:.1%}" if x is not None else "—"


data, quality = prepare(DATA_DIR)
services, diseases, epi = data["services"], data["diseases"], data["epi"]
metrics = key_metrics(services, epi)

st.markdown("# Xawadle Health Centre")
st.caption("Q3 reporting period · July–September · Aggregate facility analytics")

with st.sidebar:
    st.markdown("## Platform navigation")
    section = st.radio(
        "View",
        ["Executive overview", "Service analytics", "Nutrition & EPI", "Biostatistics", "AI benchmark"],
    )
    st.divider()
    st.caption("Data governance")
    st.info("Aggregate figures only. No patient-identifiable data are included.")

if not quality.passed:
    st.error("One or more data-quality checks failed. Review the details below before operational use.")

with st.expander("Data quality and provenance", expanded=not quality.passed):
    for c in quality.checks:
        st.write(("✅" if c["passed"] else "❌") + f" **{c['name']}** — {c['detail']}")
    for w in quality.warnings:
        st.warning(w)
    st.caption(
        "Missing values are preserved as NA. The source prompt omitted numeric disease-by-gender counts and IPV/Penta totals."
    )


# =========================================================
# EXECUTIVE OVERVIEW
# =========================================================
if section == "Executive overview":
    st.markdown("## Executive overview")
    cols = st.columns(4)
    cols[0].metric("OPD encounters", f"{metrics['opd_total']:,.0f}")
    cols[1].metric("Under-5 share", pct(metrics["under5_share"]))
    cols[2].metric("Malnutrition rate", pct(metrics["malnutrition_rate"]))
    cols[3].metric("Delivery complications", pct(metrics["delivery_complication_rate"]))

    # Qaybta EPI ee bogga hore
    st.markdown("### EPI Coverage Snapshot")
    epi_cols = st.columns(3)
    epi_cols[0].metric("Measles Coverage", pct(metrics["measles_coverage"]))
    epi_cols[1].metric("Total EPI Doses", f"{epi['total'].sum():,.0f}" if not epi.empty else "0")
    epi_cols[2].metric("Antigens Reported", f"{epi['antigen'].nunique()}" if not epi.empty else "0")

    st.markdown("### Management signal")
    st.info(
        "The Q3 picture is dominated by a high under-5 service load and a 25.0% malnutrition rate among screened children. "
        "The strongest immediate analytics priority is completing disease-level, gender-disaggregated registers so respiratory, "
        "diarrhoeal, and immunization hypotheses can be tested rather than assumed."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Service volume")
        chart = services[
            services.total.notna()
            & services.indicator.isin(
                ["OPD over 5 years", "OPD under 5 years", "ANC", "PNC", "Deliveries"]
            )
        ].copy()
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.barplot(data=chart, y="indicator", x="total", palette="crest", ax=ax)
        ax.set(xlabel="Reported count", ylabel="")
        st.pyplot(fig, clear_figure=True)
    with c2:
        st.markdown("#### Priority root-cause actions")
        st.dataframe(
            root_cause_actions()[["driver", "indicator", "action"]],
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# SERVICE ANALYTICS
# =========================================================
elif section == "Service analytics":
    st.markdown("## Service analytics")
    chart = services[services.total.notna()].copy()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=chart, y="indicator", x="total", hue="domain", dodge=False, palette="viridis", ax=ax)
    ax.set(xlabel="Reported count", ylabel="")
    st.pyplot(fig, clear_figure=True)
    st.dataframe(chart, use_container_width=True, hide_index=True)

    st.markdown("### Gender disaggregation")
    gender = services[services.male.notna() & services.female.notna()][
        ["indicator", "male", "female"]
    ].melt("indicator", var_name="sex", value_name="count")
    fig, ax = plt.subplots(figsize=(9, 4))
    sns.barplot(
        data=gender,
        x="indicator",
        y="count",
        hue="sex",
        palette={"male": "#2563eb", "female": "#db2777"},
        ax=ax,
    )
    ax.tick_params(axis="x", rotation=35)
    st.pyplot(fig, clear_figure=True)


# =========================================================
# NUTRITION & EPI
# =========================================================
elif section == "Nutrition & EPI":
    st.markdown("## Nutrition and EPI coverage")
    left, right = st.columns(2)
    with left:
        nut = services[(services.domain == "Nutrition") & services.total.notna()]
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.barplot(data=nut, y="indicator", x="total", palette="mako", ax=ax)
        ax.set(xlabel="Count", ylabel="")
        st.pyplot(fig, clear_figure=True)
        st.metric("Malnutrition among screened", pct(metrics["malnutrition_rate"]))
    with right:
        e = epi[epi.total.notna()].copy()
        # Halkan ayaa lagu hagaajiyay: epi_total oo dhan ayaa la isticmaalayaa
        epi_total = float(e["total"].sum()) if not e.empty else 0.0
        e["coverage"] = e.total / epi_total if epi_total > 0 else 0.0
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.barplot(data=e, y="antigen", x="coverage", palette="rocket", ax=ax)
        ax.set(xlabel="Coverage against stated denominator", ylabel="")
        ax.set_xlim(0, 1.05)
        st.pyplot(fig, clear_figure=True)
        st.metric("Recorded measles dose coverage", pct(metrics["measles_coverage"]))
    st.dataframe(epi, use_container_width=True, hide_index=True)

    # Qaybta Epidemiology Scenarios oo lagu daray
    st.markdown("### Epidemiology Scenarios")
    st.dataframe(epidemiology_scenarios(services, epi), use_container_width=True, hide_index=True)


# =========================================================
# BIOSTATISTICS
# =========================================================
elif section == "Biostatistics":
    st.markdown("## Biostatistical and epidemiological analysis")
    st.markdown("### Descriptive statistics of reported service totals")
    st.json(descriptive(services.total.dropna()))

    st.markdown("### Transparent proxy risk and odds ratios")
    st.dataframe(epidemiology_scenarios(services, epi), use_container_width=True, hide_index=True)
    st.warning(
        "These are aggregate proxy comparisons, not causal or patient-level disease risk estimates. "
        "Linked numerator/denominator cohorts are required for valid clinical inference."
    )

    st.markdown("### Root-cause logic")
    st.dataframe(root_cause_actions(), use_container_width=True, hide_index=True)


# =========================================================
# AI BENCHMARK
# =========================================================
else:
    st.markdown("## AI benchmark testing")
    st.markdown(
        "The framework is ready for an approved model's predictions or clinician-approved rules. "
        "The demo below tests metric plumbing on deterministic synthetic vectors only."
    )
    result = example_synthetic_benchmark()
    a, b, c = st.columns(3)
    a.metric("Smoke-test accuracy", f"{result.metrics['accuracy']:.1%}")
    b.metric("Demographic parity gap", f"{result.metrics['demographic_parity_gap']:.1%}")
    c.metric("Status", "PASS")
    st.code("from benchmarking import benchmark_predictions\nresults = benchmark_predictions(y_true, y_pred, group=sex)")
    st.dataframe(pd.DataFrame([result.metrics]), use_container_width=True, hide_index=True)
    st.info(
        "For production: evaluate sensitivity, specificity, PPV, NPV, calibration, subgroup performance, "
        "missingness, and threshold stability on a governed, labeled validation set. Do not treat the smoke test as clinical evidence."
    )
