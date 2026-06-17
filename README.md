# 🏎️ F1 Race Predictor V3

A machine learning project that predicts Formula 1 race outcomes and upcoming Grand Prix results using historical race data, qualifying performance, driver form, team form, championship standings, and circuit-specific insights.

---

## 🚀 Project Overview

The project evolved from a simple race outcome classifier into a race position prediction system capable of forecasting upcoming Formula 1 races using real qualifying data and championship standings.

The model uses data collected through FastF1, enhanced with multiple engineered features, and trained using CatBoost Regression to predict a driver's finishing position.

---

## ✨ Features

### Data Collection

* Historical Formula 1 race data (2022–2026)
* Real qualifying session data via FastF1
* Driver standings from Jolpi API
* Constructor standings from Jolpi API
* Weather and circuit information

### Feature Engineering

* Qualifying lap time
* Grid position
* Pole gap
* Driver championship points
* Constructor championship points
* Driver form (last 3 races)
* Team form (last 3 races)
* Driver track history
* Circuit type
* Starting tyre compound
* Weather conditions

### Prediction Capabilities

* Exact finishing position prediction
* Upcoming race prediction
* Automatic qualifying data integration
* Championship standings integration
* Full race grid forecasting

---

## 📊 Dataset

| Metric          | Value     |
| --------------- | --------- |
| Total Rows      | 1,954     |
| Total Races     | 98        |
| Features        | 19        |
| Seasons Covered | 2022–2026 |

---

## 🤖 Model

### CatBoostRegressor

The current version uses CatBoost Regression to predict a driver's finishing position rather than classifying outcomes into broad categories.

### Performance

| Metric                    | Score     |
| ------------------------- | --------- |
| MAE (Mean Absolute Error) | **3.070** |
| Top-3 Accuracy            | **89.3%** |
| Top-10 Accuracy           | **81.2%** |

### Previous Version Comparison

| Version | Model                                 | Performance     |
| ------- | ------------------------------------- | --------------- |
| V1      | Random Forest Classifier              | 65.78% Accuracy |
| V2      | CatBoostRegressor                     | 3.112 MAE       |
| V3      | CatBoostRegressor + Advanced Features | **3.070 MAE**   |

---

## 🛠️ Technologies Used

* Python
* FastF1
* Pandas
* NumPy
* CatBoost
* Scikit-Learn
* Streamlit
* Requests
* Jolpi API
  
---

## 🔮 Example Prediction Workflow

1. Fetch latest qualifying data
2. Retrieve driver standings
3. Retrieve constructor standings
4. Generate driver-specific features
5. Predict finishing positions
6. Rank drivers by predicted finish
7. Generate projected race results

---

## 🏁 Current Capabilities

✅ Historical race prediction

✅ Upcoming race prediction

✅ Real qualifying pace integration

✅ Driver form tracking

✅ Team form tracking

✅ Championship standings integration

✅ Circuit history analysis

✅ Pole gap analysis

✅ Automated race forecasting

---

## 📈 Future Improvements

* Streamlit App V3
* Driver profile photos
* Interactive podium visualization
* Monte Carlo race simulations
* DNF probability prediction
* Weather-aware forecasting
* Head-to-head driver comparisons

---

## ▶️ How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the dashboard:

```bash
python -m streamlit run app_v1.py
```

---

## 👨‍💻 Author

**Moksh Solanki**

First-year Computer Science Engineering student at DY Patil International University, Pune.

Interested in Machine Learning, Data Science, Cybersecurity, and Motorsport Analytics.
