import streamlit as st
import pandas as pd
from datetime import date

st.title("Options Roll Calculator")

# --- Inputs ---
st.subheader("Initial Position")

option_type = st.selectbox("Option Type", ["Call", "Put"])
initial_strike = st.number_input("Initial Strike Price", value=100.0)
initial_expiry = st.date_input("Initial Expiry Date", value=date.today())
initial_premium = st.number_input("Initial Premium Received", value=1.00)

st.write("---")

st.subheader("Roll Details")

roll_direction = st.selectbox("Roll Direction", ["Roll Down", "Roll Up"])
new_strike = st.number_input("New Strike Price", value=95.0)
new_expiry = st.date_input("New Expiry Date", value=date.today())
new_premium = st.number_input("New Premium Received", value=1.25)

st.write("---")

# --- Calculations ---
strike_diff = new_strike - initial_strike
net_premium = new_premium - initial_premium
total_pl = strike_diff + net_premium

# --- Display Results ---
st.subheader("Result")

if total_pl > 0:
    st.markdown(f"<h3 style='color: green;'>Profit: {total_pl:.2f}</h3>", unsafe_allow_html=True)
else:
    st.markdown(f"<h3 style='color: red;'>Loss: {total_pl:.2f}</h3>", unsafe_allow_html=True)

# --- Summary Table ---
data = {
    "Field": [
        "Option Type",
        "Initial Strike",
        "Initial Expiry",
        "Initial Premium",
        "Roll Direction",
        "New Strike",
        "New Expiry",
        "New Premium",
        "Strike Difference",
        "Net Premium",
        "Total P/L"
    ],
    "Value": [
        option_type,
        initial_strike,
        initial_expiry,
        initial_premium,
        roll_direction,
        new_strike,
        new_expiry,
        new_premium,
        round(strike_diff, 2),
        round(net_premium, 2),
        round(total_pl, 2)
    ]
}

df = pd.DataFrame(data)

st.write("---")
st.subheader("Summary")
st.dataframe(df)
