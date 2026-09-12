# Xawadle-Health-Platform
Enterprise Healthcare Data Analytics &amp; AI Benchmarking Platform for Xawadle Health Centre
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
