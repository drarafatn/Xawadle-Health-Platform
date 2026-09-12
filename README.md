# Xawadle Health Centre — Q3 Analytics Platform

Enterprise Healthcare Data Analytics & AI Benchmarking Platform for Xawadle Health Centre.

## 📋 Overview

This platform provides aggregate facility analytics for the Q3 (July–September) reporting period. It ingests, validates, and visualizes service delivery, disease surveillance, nutrition, and immunization (EPI) data from Xawadle Health Centre.

The dashboard is built with **Streamlit** and provides interactive analytics for facility management, M&E officers, and clinical leads.

## 🎯 Key Features

- **Data Quality Checks** — Automated validation of required tables, negative counts, and gender reconciliation.
- **Executive Overview** — High-level KPIs (OPD encounters, malnutrition rate, delivery complications, EPI coverage).
- **Service Analytics** — Volume and gender-disaggregated analysis of OPD, Maternal, and Nutrition services.
- **Disease Analytics** — Interactive filtering, heatmaps, and distribution charts for OPD diseases.
- **Nutrition & EPI Coverage** — Antigen-level coverage against a target population of 21,000.
- **Biostatistics** — Descriptive statistics by domain, proxy risk/odds ratios, and disease risk ratios.
- **AI Benchmarking** — Framework for testing approved models or clinician-approved rules (synthetic smoke-test only).

## 📁 Project Structure

| File | Purpose |
|---|---|
| `app.py` | Main Streamlit dashboard application |
| `ingestion.py` | Data loading and quality validation |
| `biostatistics.py` | Statistical functions (descriptive, risk ratios) |
| `benchmarking.py` | AI model benchmarking interfaces |
| `service_totals.csv` | Service delivery data (OPD, Maternal, Nutrition) |
| `opd_disease_counts.csv` | Disease surveillance data by age and gender |
| `epi_coverage.csv` | Immunization coverage data by antigen |
| `requirements.txt` | Python dependencies |

## 🚀 Installation & Usage

### Prerequisites

- Python 3.9+
- pip

### Local Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/drarafatn/Xawadle-Health-Platform.git
   cd Xawadle-Health-Platform
   
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:

   ```bash
   streamlit run app.py
   ```

4. Open your browser at `http://localhost:8501`.

### Streamlit Cloud

The app is deployed at: [https://lapp6f.streamlit.app](https://lapp6f.streamlit.app)

## 📊 Data Sources

All data is **aggregate facility data only**. No patient-identifiable information is included. Missing values are preserved as NA.

## ⚠️ Disclaimer

This dashboard uses aggregate facility data only. All statistical estimates are aggregate proxies and should not be interpreted as clinical evidence. For operational decisions, consult with the facility's M&E officer and clinical lead.

## 👤 Author

**Dr. Arafat** — Xawadle Health Centre

## 📄 License

This project is for internal use at Xawadle Health Centre.
