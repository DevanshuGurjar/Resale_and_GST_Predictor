#  Resale & GST Predictor

This project predicts:

1. Resale price of **used cars and bikes** using RandomForestRegressor.
2. GST-adjusted price for **new vehicles** based on engine capacity and fuel type.

---

## Features

- Predict resale price for used vehicles
- GST price calculation for new vehicles
- Interactive Streamlit app
- Models trained on real datasets

---

## Folder Structure

- `data/` → Contains CSV datasets
- `models/` → Saved `.pkl` models and column info
- `notebooks/` → Jupyter notebook with full pipeline
- `app.py` → Streamlit app
- `requirements.txt` → Python dependencies

---

# How to Run

1. Clone the repository:
git clone https://github.com/<your-username>/Resale-GST-Predictor.git

2. Install dependencies:
pip install -r requirements.txt

3. Run Streamlit:
streamlit run app.py
