import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import datetime
import matplotlib.pyplot as plt
import joblib

# --- Utility: Normalize and map column names ---
def normalize_and_map(df):
    rename_dict = {
        "Year": "year",
        "Age": "age",
        "Kms_Driven": "km_driven",
        "Kms": "km_driven",
        "Kilometers_Driven": "km_driven",
        "Fuel": "fuel_type",
        "Fuel_Type": "fuel_type",
        "Engine": "engine_cc",
        "Engine_CC": "engine_cc",
        "Selling_Price": "resale_price",
        "Price": "resale_price",
        "Resale_Price": "resale_price"
    }
    df = df.rename(columns=rename_dict)

    if "year" in df.columns:
        current_year = datetime.datetime.now().year
        df["age"] = current_year - df["year"]

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df

# --- Load Bike model ---
@st.cache_data
def load_bike_model():
    used_bike_df = pd.read_csv("data/used_bikes.csv")
    used_bike_df = normalize_and_map(used_bike_df)
    X_bike = pd.get_dummies(
        used_bike_df[['km_driven','age','fuel_type','engine_cc']], 
        columns=['fuel_type'], drop_first=True
    )
    y_bike = used_bike_df['resale_price']
    model = RandomForestRegressor(random_state=42)
    model.fit(X_bike, y_bike)
    return model, X_bike.columns

# --- Load Car model ---
@st.cache_data
def load_car_model():
    used_car_df = pd.read_csv("data/used_cars.csv")
    used_car_df = normalize_and_map(used_car_df)
    X_car = pd.get_dummies(
        used_car_df[['km_driven','age','fuel_type','engine_cc','transmission']], 
        columns=['fuel_type','transmission'], drop_first=True
    )
    y_car = used_car_df['resale_price']
    model = RandomForestRegressor(random_state=42)
    model.fit(X_car, y_car)
    return model, X_car.columns

# --- Load models ---
bike_model, bike_columns = load_bike_model()
car_model, car_columns = load_car_model()

# --- Prediction function (no caching, avoids unhashable errors) ---
def predict_used_price(model, input_df):
    return model.predict(input_df)[0]

# --- Streamlit Layout ---
st.set_page_config(page_title="Resale & GST Predictor", layout="centered")
st.title("🚗🏍 Resale & GST Predictor")
st.markdown(
    "Predict the resale price of your **used vehicle** or the GST-adjusted price for a **new vehicle**."
)

vehicle_type = st.radio("Select vehicle type:", ["Car", "Bike"], horizontal=True)
vehicle_condition = st.radio("Select vehicle condition:", ["Used", "New"])

# --- Conditional Inputs ---
if vehicle_condition == "Used":
    st.subheader(f"Enter details for your {vehicle_type} (Used)")
    km = st.number_input("Kilometers driven", min_value=0, value=10000)
    age = st.number_input("Vehicle age (years)", min_value=0, value=3)
    engine_cc = st.number_input(
        "Engine CC", 
        min_value=50 if vehicle_type=="Bike" else 500,
        value=150 if vehicle_type=="Bike" else 1200
    )
    if vehicle_type == "Bike":
        fuel = st.selectbox("Fuel Type", options=["Petrol", "Electric", "Petrol+CNG"])
    else:
        fuel = st.selectbox("Fuel Type", options=["Petrol", "Diesel", "Electric", "Petrol+CNG"])

    model, columns = (bike_model, bike_columns) if vehicle_type=="Bike" else (car_model, car_columns)

    input_dict = {col: 0 for col in columns}
    input_dict['km_driven'] = km
    input_dict['age'] = age
    input_dict['engine_cc'] = engine_cc

    if fuel != "Petrol":
        fuel_col = f"fuel_type_{fuel}"
        if fuel_col in input_dict:
            input_dict[fuel_col] = 1

    if vehicle_type == "Car":
        transmission = st.selectbox("Transmission", options=["Manual", "Automatic"])
        trans_col = f"transmission_{transmission.lower()}"
        if trans_col in input_dict:
            input_dict[trans_col] = 1

    input_df = pd.DataFrame([input_dict])

else:  # New vehicle
    st.subheader(f"Enter details for your {vehicle_type} (New)")
    if vehicle_type == "Bike":
        fuel = st.selectbox("Fuel Type", options=["Petrol", "Electric", "Petrol+CNG"])
    else:
        fuel = st.selectbox("Fuel Type", options=["Petrol", "Diesel", "Electric", "Petrol+CNG"])

    engine_cc = st.number_input(
        "Engine CC", 
        min_value=50 if vehicle_type=="Bike" else 500,
        value=150 if vehicle_type=="Bike" else 1200
    )

    base_price = st.number_input("Enter ex-showroom/base price of the vehicle (includes old 28% GST)", min_value=10000)

# --- Prediction Button ---
if st.button("🔮 Predict Price"):
    if vehicle_condition == "Used":
        pred_price = predict_used_price(model, input_df)
        st.success(f"💰 Estimated resale price: ₹{pred_price:,.0f}")
    else:  # New vehicle GST calculation
        gst_price = base_price
        message = ""
        diff_text = ""

        if fuel == "Electric":
            gst_price = base_price
            message = "⚡ Electric vehicle GST is standard 5%."
            st.success(f"💰 GST-adjusted price: ₹{gst_price:,.0f}")
            st.info(message)
        else:
            pre_gst_price = base_price / 1.28
            if vehicle_type == "Bike" and fuel in ["Petrol", "Petrol+CNG"]:
                new_slab = 0.18 if engine_cc < 350 else 0.40
            elif vehicle_type == "Car":
                if fuel == "Petrol":
                    new_slab = 0.18 if engine_cc < 1200 else 0.40
                elif fuel == "Diesel":
                    new_slab = 0.18 if engine_cc < 1500 else 0.40
                elif fuel == "Petrol+CNG":
                    new_slab = 0.18 if engine_cc < 1200 else 0.40
            gst_price = pre_gst_price * (1 + new_slab)

            if new_slab == 0.18:
                savings = base_price - gst_price
                message = "🎉 Hurray! GST reduced! You saved on your new price."
                diff_text = f"💰 Savings: ₹{savings:,.0f}"
            else:
                extra = gst_price - base_price
                message = "💸 Oops! Higher GST applied! Need to stretch your budget."
                diff_text = f"📈 Extra Amount: ₹{extra:,.0f}"

            st.success(f"💰 GST-adjusted price: ₹{gst_price:,.0f}")
            st.info(message)
            st.warning(diff_text)

            # --- Price comparison graph ---
            plt.figure(figsize=(6,4))
            categories = ['Old Price', 'New Price']
            values = [base_price, gst_price]
            colors = ['skyblue', 'lightgreen' if gst_price < base_price else 'red']
            bars = plt.bar(categories, values, color=colors)

            for bar in bars:
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, yval + 2000, f"₹{yval:,.0f}", ha='center')

            plt.title("GST Impact on Vehicle Price")
            plt.figtext(0.95, 0.01, "*Note: This is the Ex-Showroom Price", 
                        horizontalalignment='right', fontsize=8, style='italic')
            st.pyplot(plt)
