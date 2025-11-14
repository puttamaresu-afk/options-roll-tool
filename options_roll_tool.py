import streamlit as st
import pandas as pd
from datetime import date

st.title("Options Roll Calculator")

# --- Stock Ticker ---
stock = st.text_input("Stock Ticker")

# --- Option Type ---
option_type = st.selectbox("Option Type", ["Call", "Put"])

st.write("---")

# --- Initial Position ---
col1, col2, col3 = st.columns(3)

with col1:
    initial_strike = st.number_input("Initial Strike", value=100.0)

with col2:
    initial_expiry = st.date_input("Expiry Date", value=date.today())

with col3:
    initial_premium_received = st.number_input("Premium received", value=1.00)

st.write("---")

# --- Roll Details ---
st.subheader("Roll Details")

col4, col5, col6, col7 = st.columns(4)

with col4:
    new_strike = st.number_input("New Strike price", value=95.0)

with col5:
    new_premium_received = st.number_input("New premium received", value=1.20)

with col6:
    option_buy_price = st.number_input("Option buy price", value=0.50)

with col7:
    new_expiry_date = st.date_input("New Expiry date", value=date.today())

st.write("---")

# --- Profit / Loss ---
net_premium = new_premium_received - option_buy_price
strike_diff = new_strike - initial_strike
total_pl = net_premium + strike_diff

st.subheader("Profit/Loss")

if total_pl > 0:
    st.markdown(f"<h3 style='color: green;'>Profit: {total_pl:.2f}</h3>", unsafe_allow_html=True)
else:
    st.markdown(f"<h3 style='color: red;'>Loss: {total_pl:.2f}</h3>", unsafe_allow_html=True)

st.write("---")

# --- Tabulated Results ---
st.subheader("Tabulated column of the details")

data = {
    "Stock Ticker": [stock],
    "Option Type": [option_type],
    "Initial Strike": [initial_strike],
    "Expiry Date": [initial_expiry],
    "Premium Received": [initial_premium_received],
    "New Strike price": [new_strike],
    "New premium received": [new_premium_received],
    "Option buy price": [option_buy_price],
    "New Expiry date": [new_expiry_date],
    "Profit/Loss": [round(total_pl, 2)]
}

df = pd.DataFrame(data)

st.dataframe(df)
