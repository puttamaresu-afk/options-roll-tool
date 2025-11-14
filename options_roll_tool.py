# options_roll_tool.py
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Options Roll Tool (stable)", layout="wide")

st.title("Options Roll Tool — Stable (no rerun)")

# ---------- helper utilities ----------
def ensure_session_state():
    if "initial" not in st.session_state:
        st.session_state.initial = {
            "type": "Put",
            "strike": 0.0,
            "expiry": None,
            "premium": 0.0,
        }
    if "rolls_df" not in st.session_state:
        # columns: roll number, buyback cost, new_strike, new_premium, new_expiry, buy_price
        st.session_state.rolls_df = pd.DataFrame(
            columns=["roll", "buyback", "new_strike", "new_premium", "new_expiry", "buy_price"]
        )

def parse_number(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def format_currency(x):
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return "0.00"

def add_roll(buyback, new_strike, new_premium, new_expiry, buy_price):
    df = st.session_state.rolls_df
    next_roll = int(df["roll"].max()) + 1 if (len(df) and "roll" in df.columns and pd.api.types.is_numeric_dtype(df["roll"])) else 1
    # create safe row dict
    row = {
        "roll": next_roll,
        "buyback": float(buyback),
        "new_strike": float(new_strike),
        "new_premium": float(new_premium),
        # store expiry as ISO string to avoid pyarrow conversion/dtype problems
        "new_expiry": (new_expiry.isoformat() if isinstance(new_expiry, date) else str(new_expiry)),
        "buy_price": float(buy_price),
    }
    # Append safely by loc
    st.session_state.rolls_df.loc[len(st.session_state.rolls_df)] = row

def compute_pnl():
    initial_prem = parse_number(st.session_state.initial.get("premium", 0.0))
    df = st.session_state.rolls_df
    total_new_prem = df["new_premium"].astype(float).sum() if len(df) else 0.0
    total_buybacks = df["buyback"].astype(float).sum() if len(df) else 0.0
    pnl = initial_prem + total_new_prem - total_buybacks
    return pnl, initial_prem, total_new_prem, total_buybacks

# ---------- initialize ----------
ensure_session_state()

# ---------- top: ticker & load message ----------
ticker = st.text_input("Stock Ticker (e.g. QQQ, AAPL)", value=st.session_state.get("ticker", ""))
if ticker:
    st.session_state.ticker = ticker.upper()
    st.success(f"Working on {st.session_state.ticker}")

st.markdown("---")

# ---------- Initial trade ----------
st.header("Initial Trade")
col1, col2, col3, col4 = st.columns([2,2,2,2])
with col1:
    opt_type = st.selectbox("Option Type", options=["Put", "Call"], index=0 if st.session_state.initial["type"]=="Put" else 1)
with col2:
    init_strike = st.number_input("Initial Strike", value=float(st.session_state.initial.get("strike", 0.0)))
with col3:
    init_expiry = st.date_input("Expiry Date", value=(st.session_state.initial.get("expiry") or date.today()))
with col4:
    init_prem = st.number_input("Premium received", value=float(st.session_state.initial.get("premium", 0.0)))

if st.button("Save Initial"):
    st.session_state.initial.update({
        "type": opt_type,
        "strike": float(init_strike),
        "expiry": init_expiry,
        "premium": float(init_prem),
    })
    st.success("Initial trade saved!")

st.markdown("---")

# ---------- Roll blocks ----------
st.header("Roll Your Option")

# show existing rolls table
if len(st.session_state.rolls_df):
    st.subheader("Saved Rolls")
    # make a safe display copy: ensure correct dtypes and convert dates to strings
    display_df = st.session_state.rolls_df.copy()
    if "new_expiry" in display_df.columns:
        display_df["new_expiry"] = display_df["new_expiry"].astype(str)
    st.dataframe(display_df.reset_index(drop=True))
else:
    st.info("No rolls saved yet. Use the 'New Roll' area below to add a roll.")

# Add a new roll UI (single-row input, presses Save to append)
st.subheader("New Roll")
c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.5, 1.5])
with c1:
    new_strike = st.number_input("New Strike price", step=0.5, key="ui_new_strike")
with c2:
    new_prem = st.number_input("New premium received", step=0.5, key="ui_new_prem")
with c3:
    buy_back = st.number_input("Option buy price (buyback cost)", step=0.5, key="ui_buy_back")
with c4:
    new_expiry = st.date_input("New Expiry date", key="ui_new_expiry", value=date.today())

if st.button("Save Roll"):
    # store the roll
    add_roll(buyback=buy_back, new_strike=new_strike, new_premium=new_prem, new_expiry=new_expiry, buy_price=buy_back)
    st.success("Roll saved!")

st.markdown("---")

# ---------- P/L Summary ----------
st.header("P/L Summary")
pnl, initial_prem, total_new_prem, total_buybacks = compute_pnl()
col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Initial premium received", format_currency(initial_prem))
col_b.metric("Sum of new premiums", format_currency(total_new_prem))
col_c.metric("Sum of buybacks", format_currency(total_buybacks))
pnl_str = format_currency(pnl)
if pnl >= 0:
    col_d.metric("Net P/L", pnl_str, delta=None)
else:
    col_d.metric("Net P/L (loss)", pnl_str, delta=None)

# show detailed breakdown (saved data)
st.subheader("Saved Data (detailed)")
df_show = st.session_state.rolls_df.copy()
if "new_expiry" in df_show.columns:
    df_show["new_expiry"] = df_show["new_expiry"].astype(str)
# safe dtypes
for col in ["buyback", "new_strike", "new_premium", "buy_price"]:
    if col in df_show.columns:
        df_show[col] = pd.to_numeric(df_show[col], errors="coerce").fillna(0.0)
st.dataframe(df_show.reset_index(drop=True))

# helpful note
st.markdown(
    """
    **Notes**
    - This app stores data in the session state only (no CSV). If you want persistent storage, we can add a save/load CSV or GitHub-backed storage.
    - Dates are stored/displayed as ISO strings to avoid PyArrow conversion issues in Streamlit.
    """
)
