# 🏎️ Formula 1 Race Outcome Predictor V3

An elite, production-grade F1 Race Outcome Predictor and Telemetry Dashboard. Powered by a **CatBoost Machine Learning core** and dynamic rolling form analytics, this application delivers grid standing predictions via a premium, dark-mode immersive user interface mimicking real-world team paddock consoles.

🚀 **Live Deployment:** https://f1-race-outcome-predictor-iwuzuknhwa7nkkgnms4pvu.streamlit.app/

---

## 🌟 Key Features

* **Advanced Predictive Engine:** CatBoost Regressor utilizing multi-season historical data, dynamic driver forms, and circuit-specific metrics.
* **Premium Paddock UI:** High-end dark telemetry dashboard layout featuring minimalist 3D podium cards, interactive hover glows, and precise grid layouts built using custom CSS overrides.
* **Optimized Asset Pipeline:** Smart-routed driver portrait streams and sandboxed inline **Base64 binary team logo streams** to completely bypass cross-origin network hotlinking blocks.
* **Dynamic Form Factors:** Multi-year support with robust fallback mapping mechanisms for missing data points or sudden driver changes.

---

## 📊 System Architecture & Data Pipeline

The system is engineered as a decoupled, multi-stage data processing and machine learning pipeline:

1. **Ingestion Layer:** Pulls historical and real-time session telemetry, qualifying results, and driver/constructor metrics using the `FastF1` API and historical data matrices.
2. **Feature Engineering Engine:** Computes dynamic rolling form metrics (e.g., driver's average finish position over the last $N$ races, team constructor velocity).
3. **Inference Pipeline:** Loads the optimized CatBoost model bundle (`f1_model_v3.pkl`), validates structural schema inputs, and outputs full predicted race standings.
4. **Presentation Layer:** Renders a sandboxed high-performance layout on Streamlit Cloud utilizing low-latency base64 graphics injection.

---

## 🛠️ Tech Stack & Architecture Components

* **Frontend Framework:** Streamlit (Custom CSS injected via unsafe HTML scopes)
* **Machine Learning Core:** CatBoost (Gradient Boosting on Decision Trees)
* **Data Pipelines & Manipulation:** Pandas, NumPy
* **Data Serialization:** Pickle Protocol
* **Domain Telemetry Provider:** FastF1 API

---

## 📦 Installation & Local Setup

# 1. To clone and spin up this elite F1 telemetry instance locally, run the following sequence in your terminal:

```bash
git clone https://github.com/mokshsolankii/F1-Race-Outcome-Predictor.git
cd F1-Race-Outcome-Predictor
```
# 2. Install pristine package dependencies
```bash
pip install -r requirements.txt
```
# 3. Launch the local Streamlit sandbox instance
```bash
streamlit run app_v3.py
```
