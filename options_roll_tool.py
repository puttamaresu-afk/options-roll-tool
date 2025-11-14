import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(layout="wide")

st.title("Options Roll Tool — Stable Version (With Rolls)")

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# -----------------------------
# Helper Functions
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

df = load_table(ticker)
st.success(f"Loaded data for {ticker} (rows: {len(df)})")

# -----------------------------------------------------------
# STEP 2 — INITIAL TRADE
# -----------------------------------------------------------
st.subheader("Initial Trade")

c1, c2, c3, c4 = st.columns(4)

with c1:
    init_type = st.selectbox("Option Type", ["Put", "Call"])

with c2:
    init_strike = st.number_input("Initial Strike", min_value=0.0, step=1.0)

with c3:
    init_expiry = st.date_input("Expiry Date", value=date.today())

with c4:
    init_premium = st.number_input("Premium Received", min_value=0.0, step=1.0)

if st.button("Save Initial"):
    new_row = pd.DataFrame([{
        "roll": 0,
        "buyback": 0.0,
        "new_strike": init_strike,
        "new_expiry": init_expiry,
        "new_premium": init_premium,
        "pl": init_premium   # initial P/L is premium received
    }])
    save_table(ticker, new_row)
    df = new_row
    st.success("Initial trade saved!")

# -----------------------------------------------------------
# STEP 3 — ROLLING SECTION
# -----------------------------------------------------------
st.subheader("Roll Your Option")

if len(df) == 0:
    st.warning("Please save an initial trade first.")
    st.stop()

last_roll_number = df["roll"].max()
next_roll_number = last_roll_number + 1

st.write(f"### Roll #{next_roll_number}")

r1, r2, r3, r4 = st.columns(4)

with r1:
    buyback = st.number_input("Buy-back (closing) price", min_value=0.0, step=1.0)

with r2:
    new_strike = st.number_input("New Strike", min_value=0.0, step=1.0)

with r3:
    new_expiry = st.date_input("New Expiry", value=date.today())

with r4:
    new_premium = st.number_input("New Premium Received", min_value=0.0, step=1.0)

# Auto P/L
roll_pl = new_premium - buyback
color = "green" if roll_pl >= 0 else "red"
st.markdown(f"### Roll P/L: <span style='color:{color}; font-size:24px;'>${roll_pl:.2f}</span>", unsafe_allow_html=True)

# Save roll
if st.button("Save Roll"):
    new_row = pd.DataFrame([{
        "roll": next_roll_number,
        "buyback": buyback,
        "new_strike": new_strike,
        "new_expiry": new_expiry,
        "new_premium": new_premium,
        "pl": roll_pl
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_table(ticker, df)

    st.success(f"Roll #{next_roll_number} saved!")

# -----------------------------------------------------------
# STEP 4 — Show Historical Rolls
# -----------------------------------------------------------
st.subheader("Saved Rolls")

if len(df) == 0:
    st.info("No data yet.")
else:
    st.dataframe(df)
