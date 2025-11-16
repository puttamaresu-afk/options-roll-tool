import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(page_title="Options Roll Calculator", layout="centered")

st.title("Options Roll Calculator")

# ------------------------------------------------------------------
# Initialise session state table
# ------------------------------------------------------------------
COLUMNS = [
    "Stock Ticker",
    "Option Type",
    "Initial Strike",
    "Expiry Date",
    "Premium received",
    "New Strike price",
    "New premium received",
    "New Expiry date",
    "Option buy price",
    "Profit/loss (per share)",
]

if "rolls_df" not in st.session_state:
    st.session_state["rolls_df"] = pd.DataFrame(columns=COLUMNS)


# ------------------------------------------------------------------
# 1️⃣ INITIAL LEG (top section of your sketch)
# ------------------------------------------------------------------
st.subheader("Initial Position")

stock_ticker = st.text_input("Stock Tickr", value="QQQ")

option_type = st.selectbox(
    "Option Type",
    ["Call", "Put"],
    help="Type of option you are selling/rolling.",
)

col1, col2, col3 = st.columns(3)
with col1:
    initial_strike = st.number_input("Initial Strike", min_value=0.0, step=0.5)
with col2:
    initial_expiry = st.date_input("Expiry Date", value=date.today())
with col3:
    initial_premium = st.number_input(
        "Premium received (per share)",
        min_value=0.0,
        step=0.05,
    )

add_initial = st.button("Save / Start New Chain")

if add_initial:
    # Start a fresh chain for this ticker
    st.session_state["rolls_df"] = pd.DataFrame(columns=COLUMNS)

    # First row: only the initial leg, no roll yet
    first_row = {
        "Stock Ticker": stock_ticker,
        "Option Type": option_type,
        "Initial Strike": initial_strike,
        "Expiry Date": initial_expiry,
        "Premium received": initial_premium,
        "New Strike price": np.nan,
        "New premium received": np.nan,
        "New Expiry date": pd.NaT,
        "Option buy price": np.nan,
        # For convenience we treat this as initial net credit per share
        "Profit/loss (per share)": initial_premium,
    }

    st.session_state["rolls_df"] = pd.concat(
        [st.session_state["rolls_df"], pd.DataFrame([first_row])],
        ignore_index=True,
    )
    st.success("Initial leg saved. You can now add rolls below.")


st.markdown("---")

# ------------------------------------------------------------------
# 2️⃣ ROLL DETAILS (middle section of your sketch)
# ------------------------------------------------------------------
st.subheader("Roll Details")

col4, col5, col6, col7 = st.columns(4)
with col4:
    new_strike = st.number_input("New Strike price", min_value=0.0, step=0.5)
with col5:
    new_premium = st.number_input(
        "New premium received (per share)",
        min_value=0.0,
        step=0.05,
    )
with col6:
    option_buy_price = st.number_input(
        "Option buy price (per share)",
        min_value=0.0,
        step=0.05,
        help="Price paid to buy back / close the current short option.",
    )
with col7:
    new_expiry = st.date_input("New Expiry date", value=date.today(), key="new_expiry")

add_roll = st.button("New roll")

if add_roll:
    df = st.session_state["rolls_df"]

    if df.empty:
        st.error("Please save an initial leg first before adding a roll.")
    else:
        # Use LAST ROW as the leg we are rolling FROM
        prev = df.iloc[-1]

        # Previous leg that is currently open:
        # If there has already been at least one roll, the open leg is the *new* one.
        prev_strike = (
            prev["New Strike price"]
            if pd.notna(prev["New Strike price"])
            else prev["Initial Strike"]
        )
        prev_expiry = (
            prev["New Expiry date"]
            if pd.notna(prev["New Expiry date"])
            else prev["Expiry Date"]
        )
        prev_premium = (
            prev["New premium received"]
            if pd.notna(prev["New premium received"])
            else prev["Premium received"]
        )

        # Cumulative net credit / P&L per share up to previous leg
        prev_cum_pl = prev["Profit/loss (per share)"] if pd.notna(prev["Profit/loss (per share)"]) else 0.0

        # New cumulative net credit: old credit - cost to close + new premium
        new_cum_pl = prev_cum_pl - option_buy_price + new_premium

        new_row = {
            "Stock Ticker": prev["Stock Ticker"],
            "Option Type": prev["Option Type"],
            "Initial Strike": prev_strike,
            "Expiry Date": prev_expiry,
            "Premium received": prev_premium,
            "New Strike price": new_strike,
            "New premium received": new_premium,
            "New Expiry date": new_expiry,
            "Option buy price": option_buy_price,
            "Profit/loss (per share)": new_cum_pl,
        }

        st.session_state["rolls_df"] = pd.concat(
            [df, pd.DataFrame([new_row])],
            ignore_index=True,
        )
        st.success("Roll added to the table.")


st.markdown("---")

# ------------------------------------------------------------------
# 3️⃣ PROFIT / LOSS SUMMARY (bottom line “Profit/loss” in your sketch)
# ------------------------------------------------------------------
st.subheader("Profit/loss")

df = st.session_state["rolls_df"]

if df.empty:
    st.info("No data yet. Add an initial leg to begin tracking.")
else:
    last = df.iloc[-1]
    current_pl = last["Profit/loss (per share)"]

    st.write(
        f"**Current cumulative net credit / P&L (per share)** "
        f"after the latest roll: **{current_pl:.2f}**"
    )
    st.caption(
        "Multiply this number by your contract size (usually 100) and the number of "
        "contracts to get the total P&L."
    )

    # ------------------------------------------------------------------
    # 4️⃣ TABULATED COLUMN OF THE DETAILS (your table sketch)
    # ------------------------------------------------------------------
    st.subheader("Tabulated column of the details")

    # Nice display copy
    display_df = df.copy()
    st.dataframe(display_df, use_container_width=True)

    if st.button("Clear table / start over"):
        st.session_state["rolls_df"] = pd.DataFrame(columns=COLUMNS)
        st.success("Table cleared. You can enter a new initial position now.")
