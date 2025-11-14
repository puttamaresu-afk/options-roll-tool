import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(layout="wide")

st.title("Options Roll Tool — Stable Version (No Rerun)")

# -----------------------------
# Ensure Data Folder Exists
# -----------------------------
DATA_DIR = "data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# -----------------------------
# Helper functions
# -----------------------------
def file_path(ticker):
    return os.path.join(DATA_DIR, f"{ticker.upper()}.csv")

def load_table(ticker):
    path = file_path(ticker)
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except:
            return pd.DataFrame()
    else:
        return pd.DataFrame()

def save_table(ticker, df):
    df.to_csv(file_path(ticker), index=False)

# -----------------------------
# Step 1 — Ticker Input
# -----------------------------
ticker = st.text_input("Stock Ticker (e.g. QQQ, AAPL)").upper().strip()

if ticker == "":
    st.info("Please enter a ticker to continue.")
    st.stop()

# Load table safely
df = load_table(ticker)

st.success(f"Loaded data for **{ticker}** (rows: {len(df)})")

# -----------------------------
# Step 2 — Initial Trade Section
# -----------------------------
st.subheader("Initial Trade")

col1, col2, col3, col4 = st.columns(4)

with col1:
    option_type = st.selectbox("Option Type", ["Put", "Call"])

with col2:
    strike = st.number_input("Initial Strike", min_value=0.0, step=1.0)

with col3:
    expiry = st.date_input("Expiry Date", value=date.today())

with col4:
    premium = st.number_input("Premium Received", min_value=0.0, step=1.0)

if st.button("Save Initial"):
    df = pd.DataFrame([{
        "type": option_type,
        "strike": strike,
        "expiry": expiry,
        "premium": premium
    }])
    save_table(ticker, df)
    st.success("Initial trade saved!")

# -----------------------------
# Step 3 — Display Table
# -----------------------------
st.subheader("Saved Data")

if len(df) == 0:
    st.info("No data saved yet.")
else:
    st.dataframe(df)
