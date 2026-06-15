# F1 Race Predictor

A machine learning project that predicts Formula 1 race outcomes using historical race data, qualifying position, constructor performance and circuit information.

## Features

* Historical Formula 1 data collection using FastF1
* Data preprocessing and feature engineering
* Random Forest classification model
* Streamlit dashboard for predictions
* Probability based race outcome forecasting

## Prediction Classes

* Top 3 (Podium)
* Top 10 (Points Finish)
* Outside Top 10

## Model Performance

* Test Accuracy: 65.78%
* Dataset Size: 2,095 race entries

## Technologies Used

* Python
* FastF1
* Pandas
* NumPy
* Scikit-Learn
* Streamlit

## How to Run

Install dependencies:

pip install -r requirements.txt

Run the dashboard:

streamlit run app_v1.py
