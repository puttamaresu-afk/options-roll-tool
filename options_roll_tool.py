import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Options Roll Tool", layout="wide")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


# -----------------------------
# Helpers
# -----------------------------
def get_file_path(ticker):
    return os.path.join(DATA_DIR, f"{ticker.upper()}.csv")


def load_table(ticker):
    file_path = get_file_path(ticker)
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame(
        columns=[
            "Type", "Strike", "Expiry", "Premium",
            "New Strike", "New Expiry", "New Premium", "P/L"
        ]
    )


def save_table(ticker, df):
    df.to_csv(get_file_path(ticker), index=False)


def calc_pl(initial, new):
    if pd.isna(initial) or pd.isna(new):
        return None
    return float(new) - float(initial)


# -----------------------------
# UI
# -----------------------------
st.title("📘 Options Roll Tool — Stacked Rolls & Quick Save")

st.write("Workflow: enter ticker → load or save initial → press **New Roll** → enter details → **Save Roll**")

ticker = st.text_input("Stock Ticker (e.g., QQQ, AAPL)").upper().strip()
if not ticker:
    st.stop()

# Load existing table
df = load_table(ticker)

colA, colB = st.columns([1, 1])
with colA:
    if st.button("Load / Refresh"):
        st.rerun()

with colB:
    if st.button("Clear All Data For This Ticker"):
        save_table(ticker, df.iloc[0:0])
        st.success(f"All data cleared for {ticker}")
        st.rerun()


# -----------------------------
# Initial Trade Block
# -----------------------------
st.subheader("Initial Position")

initial_type = st.selectbox("Put / Call", ["Put", "Call"])
initial_strike = st.number_input("Strike Price", min_value=0.0, step=0.1)
initial_expiry = st.date_input("Expiry Date", value=date.today())
initial_premium = st.number_input("Premium Received", min_value=0.0, step=0.1)

if st.button("Save Initial"):
    new_row = {
        "Type": initial_type,
        "Strike": initial_strike,
        "Expiry": initial_expiry,
        "Premium": initial_premium,
        "New Strike": "",
        "New Expiry": "",
        "New Premium": "",
        "P/L": ""
    }
    df.loc[len(df)] = new_row
    save_table(ticker, df)
    st.success(f"Initial saved for {ticker}")
    st.rerun()


# -----------------------------
# NEW ROLL SYSTEM
# -----------------------------
st.subheader("Rolls")

if "roll_blocks" not in st.session_state:
    st.session_state.roll_blocks = 0

if st.button("➕ New Roll"):
    st.session_state.roll_blocks += 1

for i in range(st.session_state.roll_blocks):
    st.markdown(f"### Roll #{i+1}")

    roll_col1, roll_col2, roll_col3 = st.columns(3)

    with roll_col1:
        new_strike = st.number_input(f"New Strike (Roll {i+1})", min_value=0.0, key=f"strike_{i}", step=0.1)
    with roll_col2:
        new_expiry = st.date_input(f"New Expiry (Roll {i+1})", key=f"expiry_{i}")
    with roll_col3:
        new_premium = st.number_input(f"New Premium Received (Roll {i+1})", min_value=0.0, key=f"premium_{i}", step=0.1)

    # Auto P/L using LAST ROW PREMIUM
    if len(df) > 0:
        previous_premium = df.iloc[-1]["Premium"] if pd.notna(df.iloc[-1]["Premium"]) else 0
    else:
        previous_premium = 0

    pl_value = new_premium - previous_premium

    st.write("**P/L:** ", f"🟢 +{pl_value:.2f}" if pl_value >= 0 else f"🔴 {pl_value:.2f}")

    # Save button
    if st.button(f"Save Roll #{i+1}", key=f"save_roll_{i}"):

        new_row = {
            "Type": df.iloc[0]["Type"] if len(df) else "",
            "Strike": df.iloc[-1]["Strike"] if len(df) else "",
            "Expiry": df.iloc[-1]["Expiry"] if len(df) else "",
            "Premium": previous_premium,
            "New Strike": new_strike,
            "New Expiry": new_expiry,
            "New Premium": new_premium,
            "P/L": pl_value
        }

        df.loc[len(df)] = new_row
        save_table(ticker, df)

        st.success(f"Roll #{i+1} saved")
        st.rerun()


# -----------------------------
# DISPLAY TABLE
# -----------------------------
st.subheader("Trade History")

if len(df) == 0:
    st.info("No data yet. Save initial to begin.")
else:
    st.dataframe(df, use_container_width=True)
