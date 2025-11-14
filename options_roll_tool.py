import streamlit as st
import pandas as pd
import os
from datetime import date

# -----------------------------
#  Helper Functions
# -----------------------------
DATA_DIR = "data"

def ensure_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def file_path(ticker):
    ensure_dir()
    return os.path.join(DATA_DIR, f"{ticker.upper()}.csv")

def load_table(ticker):
    path = file_path(ticker)
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=[
            "Type", "Strike", "Expiry", "Premium",
            "New Strike", "New Expiry", "New Premium",
            "Buy Back", "P/L"
        ])

def save_table(ticker, df):
    df.to_csv(file_path(ticker), index=False)

# -----------------------------
#  Streamlit UI
# -----------------------------
st.title("Options Roll Tool — stacked rolls & quick save")

st.write("Enter ticker → load/save initial → add rolls → save each roll.")

# -----------------------------
#  Ticker Input
# -----------------------------
ticker = st.text_input("Stock Ticker (e.g. QQQ, AAPL)").upper().strip()

if ticker == "":
    st.stop()

df = load_table(ticker)

# -----------------------------
#  Load/Refresh Button
# -----------------------------
if st.button("Load / Refresh"):
    df = load_table(ticker)
    st.success(f"Loaded data for {ticker}")
    st.experimental_rerun()

# -----------------------------
#  Initial Trade Input
# -----------------------------
st.subheader("Initial Trade")

c1, c2, c3, c4 = st.columns(4)

with c1:
    option_type = st.selectbox("Option Type", ["Call", "Put"])

with c2:
    initial_strike = st.number_input("Initial Strike", min_value=0.0, step=0.1)

with c3:
    initial_expiry = st.date_input("Expiry Date", value=date.today())

with c4:
    initial_premium = st.number_input("Premium received", min_value=0.0, step=0.1)

if st.button("Save Initial"):
    new_row = {
        "Type": option_type,
        "Strike": initial_strike,
        "Expiry": initial_expiry,
        "Premium": initial_premium,
        "New Strike": "",
        "New Expiry": "",
        "New Premium": "",
        "Buy Back": "",
        "P/L": ""
    }
    df.loc[len(df)] = new_row
    save_table(ticker, df)
    st.success("Initial trade saved!")
    st.experimental_rerun()

# -----------------------------
#  Roll Blocks
# -----------------------------
st.subheader("Rolls")

if "roll_blocks" not in st.session_state:
    st.session_state.roll_blocks = 0

if st.button("➕ New Roll"):
    st.session_state.roll_blocks += 1

for i in range(st.session_state.roll_blocks):
    st.markdown(f"### Roll #{i+1}")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        new_strike = st.number_input(
            f"New Strike (Roll {i+1})",
            min_value=0.0, step=0.1, key=f"strike_{i}"
        )

    with c2:
        new_expiry = st.date_input(
            f"New Expiry (Roll {i+1})",
            key=f"expiry_{i}"
        )

    with c3:
        new_premium = st.number_input(
            f"New Premium Received (Roll {i+1})",
            min_value=0.0, step=0.1, key=f"premium_{i}"
        )

    with c4:
        buy_back = st.number_input(
            f"Buy Back Price (Roll {i+1})",
            min_value=0.0, step=0.1, key=f"buyback_{i}"
        )

    # ----------- P/L Calculation -----------
    pl_value = new_premium - buy_back

    if pl_value >= 0:
        st.write(f"P/L: 🟢 +{pl_value:.2f}")
    else:
        st.write(f"P/L: 🔴 {pl_value:.2f}")

    # ----------- SAVE ROLL BUTTON ----------
    if st.button(f"Save Roll #{i+1}", key=f"save_roll_{i}"):

        last_strike = df.iloc[-1]["Strike"] if len(df) else ""
        last_expiry = df.iloc[-1]["Expiry"] if len(df) else ""
        last_premium = df.iloc[-1]["Premium"] if len(df) else ""

        new_row = {
            "Type": option_type,
            "Strike": last_strike,
            "Expiry": last_expiry,
            "Premium": last_premium,
            "New Strike": new_strike,
            "New Expiry": new_expiry,
            "New Premium": new_premium,
            "Buy Back": buy_back,
            "P/L": pl_value
        }

        df.loc[len(df)] = new_row
        save_table(ticker, df)

        st.success(f"Roll #{i+1} saved!")
        st.experimental_rerun()

# -----------------------------
# Display Table
# -----------------------------
st.subheader("Saved Rolls & History")

if len(df):
    st.dataframe(df, use_container_width=True)
else:
    st.write("No data saved yet for this ticker.")
