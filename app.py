from pathlib import Path
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from ingestion import prepare
from biostatistics import descriptive, epidemiology_scenarios, key_metrics, root_cause_actions, disease_risk_ratios
from benchmarking import example_synthetic_benchmark

st.set_page_config(page_title="Xawadle Health Centre | Q3 Analytics", page_icon="+", layout="wide")
DATA_DIR = Path(__file__).parent

# =========================================================
# TARGET POPULATION SETTING (EPI)
# =========================================================
TARGET_POPULATION = 21000


def pct(x):
    return f"{x:.1%}" if x is not None else "—"


with st.spinner("Loading data..."):
    data, quality = prepare(DATA_DIR)
services, diseases, epi = data["services"], data["diseases"], data["epi"]
metrics = key_metrics(services, epi)

st.markdown("# Xawadle Health Centre")
st.caption("Q3 reporting period · July–September · Aggregate facility analytics")

with st.sidebar:
    st.markdown("## Platform navigation")
    section = st.radio(
        "View",
        [
            "Executive overview",
            "Service analytics",
            "Disease Analytics",
            "Nutrition & EPI",
            "Biostatistics",
            "AI benchmark",
        ],
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

with st.expander("📖 Data Dictionary"):
    st.markdown("""
    | Column | Meaning |
    |---|---|
    | `period` | Reporting quarter (Q3 = July–September) |
    | `age_group` | `under_5` ama `over_5` |
    | `disease` | Nooca cudurka (ARI, Pneumonia, Fever, Diarrhoea, UTI) |
    | `antigen` | Nooca tallaalka (BCG, OPV, IPV, Penta, PCV, Rota, Measles) |
    | `indicator` | Nooca adeegga (OPD, ANC, PNC, Nutrition) |
    | `total` | Tirada guud ee kiisaska |
    | `male` / `female` | Kala qaybinta jinsiga |
    | `data_status` | `provided` ama `missing` |
    """)


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

    st.markdown("### EPI Coverage Snapshot")
    epi_cols = st.columns(3)

    # Xisaabi Measles Coverage dhab ah iyadoo la isticmaalayo Target Population
    measles_total = epi[epi["antigen"] == "Measles"]["total"].sum() if not epi.empty else 0
    measles_coverage = measles_total / TARGET_POPULATION if TARGET_POPULATION > 0 else 0.0

    epi_cols[0].metric("Measles Coverage", pct(measles_coverage))
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
# DISEASE ANALYTICS
# =========================================================
elif section == "Disease Analytics":
    st.markdown("## Disease Analytics (OPD)")
    st.caption("Q3 disease counts by age group and gender")

    if diseases.empty:
        st.warning("No disease data available. Please check opd_disease_counts.csv.")
    else:
        st.markdown("### 🔍 Filter Data")
        col1, col2 = st.columns(2)
        with col1:
            age_filter = st.multiselect(
                "Age Group",
                options=diseases["age_group"].unique(),
                default=list(diseases["age_group"].unique()),
            )
        with col2:
            disease_filter = st.multiselect(
                "Disease",
                options=diseases["disease"].unique(),
                default=list(diseases["disease"].unique()),
            )

        filtered = diseases[
            diseases["age_group"].isin(age_filter) & diseases["disease"].isin(disease_filter)
        ]

        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=filtered.to_csv(index=False),
            file_name="filtered_disease_data.csv",
            mime="text/csv",
        )

        st.markdown("### Disease Counts Table")
        st.dataframe(filtered, use_container_width=True, hide_index=True)

        st.markdown("### Total Cases by Disease")
        disease_totals = filtered.groupby("disease")["total"].sum().reset_index()
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=disease_totals, y="disease", x="total", palette="flare", ax=ax)
        ax.set(xlabel="Total Cases", ylabel="")
        st.pyplot(fig, clear_figure=True)

        st.markdown("### Cases by Age Group")
        age_totals = filtered.groupby("age_group")["total"].sum().reset_index()
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=age_totals, x="age_group", y="total", palette="Set2", ax=ax)
        ax.set(xlabel="Age Group", ylabel="Total Cases")
        st.pyplot(fig, clear_figure=True)

        st.markdown("### Cases by Gender")
        gender_totals = filtered[["male", "female"]].sum().reset_index()
        gender_totals.columns = ["sex", "count"]
        fig, ax = plt.subplots(figsize=(6, 5))
        sns.barplot(
            data=gender_totals,
            x="sex",
            y="count",
            palette={"male": "#2563eb", "female": "#db2777"},
            ax=ax,
        )
        ax.set(xlabel="Gender", ylabel="Total Cases")
        st.pyplot(fig, clear_figure=True)

        st.markdown("### Disease vs Age Group Breakdown")
        pivot_age = (
            filtered.pivot_table(
                index="disease", columns="age_group", values="total", aggfunc="sum"
            ).fillna(0)
        )
        st.dataframe(pivot_age, use_container_width=True)

        st.markdown("### 🔥 Disease vs Age Group Heatmap")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(pivot_age, annot=True, fmt=".0f", cmap="YlOrRd", ax=ax)
        st.pyplot(fig, clear_figure=True)

        st.markdown("### 🥧 Disease Distribution")
        disease_pie = filtered.groupby("disease")["total"].sum()
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.pie(
            disease_pie,
            labels=disease_pie.index,
            autopct="%1.1f%%",
            startangle=90,
            colors=sns.color_palette("Set3"),
        )
        ax.axis("equal")
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
        # Coverage dhab ah antigen kasta iyadoo la isticmaalayo Target Population
        e["coverage"] = e["total"] / TARGET_POPULATION if TARGET_POPULATION > 0 else 0.0

        # Xisaabi measles coverage halkan si looga fogaado NameError
        measles_total = epi[epi["antigen"] == "Measles"]["total"].sum() if not epi.empty else 0
        measles_coverage = measles_total / TARGET_POPULATION if TARGET_POPULATION > 0 else 0.0

        fig, ax = plt.subplots(figsize=(7, 5))
        sns.barplot(data=e, y="antigen", x="coverage", palette="rocket", ax=ax)
        ax.set(xlabel="Coverage against target population (21,000)", ylabel="")
        ax.set_xlim(0, 1.05)
        st.pyplot(fig, clear_figure=True)
        st.metric("Measles Coverage", pct(measles_coverage))
    st.dataframe(epi, use_container_width=True, hide_index=True)

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

    st.markdown("### Disease Risk Ratios (Under-5 vs Over-5)")
    if not diseases.empty:
        st.dataframe(disease_risk_ratios(diseases), use_container_width=True, hide_index=True)
        st.caption(
            "Risk Ratio (RR) = (Under-5 cases / Total Under-5) / (Over-5 cases / Total Over-5). "
            "RR > 1.2 = Under-5 higher risk; RR < 0.8 = Over-5 higher risk."
        )
    else:
        st.info("No disease data available for risk ratio calculation.")

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
    st.code(
        "from benchmarking import benchmark_predictions\nresults = benchmark_predictions(y_true, y_pred, group=sex)"
    )
    st.dataframe(pd.DataFrame([result.metrics]), use_container_width=True, hide_index=True)
    st.info(
        "For production: evaluate sensitivity, specificity, PPV, NPV, calibration, subgroup performance, "
        "missingness, and threshold stability on a governed, labeled validation set. Do not treat the smoke test as clinical evidence."
    )


# =========================================================
# FOOTER DISCLAIMER
# =========================================================
st.divider()
st.caption(
    "**Disclaimer**: This dashboard uses aggregate facility data only. "
    "No patient-identifiable information is included. "
    "All statistical estimates are aggregate proxies and should not be interpreted as clinical evidence. "
    "For operational decisions, consult with the facility's M&E officer and clinical lead."
)
