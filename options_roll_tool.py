import streamlit as st
import pandas as pd
import os
import json
from datetime import date

st.set_page_config(page_title="Options Roll Tool", layout="wide")

# -------------------------
# Storage helpers
# -------------------------
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def meta_path(ticker: str):
    return os.path.join(DATA_DIR, f"{ticker.upper()}_meta.json")

def rolls_path(ticker: str):
    return os.path.join(DATA_DIR, f"{ticker.upper()}_rolls.csv")

def load_meta(ticker: str):
    p = meta_path(ticker)
    if os.path.exists(p):
        try:
            with open(p, "r") as f:
                return json.load(f)
        except:
            return None
    return None

def save_meta(ticker: str, meta: dict):
    p = meta_path(ticker)
    with open(p, "w") as f:
        json.dump(meta, f)

def load_rolls(ticker: str):
    p = rolls_path(ticker)
    if os.path.exists(p):
        try:
            df = pd.read_csv(p)
            # ensure columns exist
            required = ["roll", "buyback", "new_strike", "new_expiry", "new_premium", "pl"]
            for c in required:
                if c not in df.columns:
                    df[c] = pd.NA
            return df[["roll", "buyback", "new_strike", "new_expiry", "new_premium", "pl"]]
        except:
            # if file corrupted, return empty
            return pd.DataFrame(columns=["roll", "buyback", "new_strike", "new_expiry", "new_premium", "pl"])
    else:
        return pd.DataFrame(columns=["roll", "buyback", "new_strike", "new_expiry", "new_premium", "pl"])

def save_rolls(ticker: str, df: pd.DataFrame):
    p = rolls_path(ticker)
    df.to_csv(p, index=False)

# -------------------------
# Utility calculations
# -------------------------
def roll_pl(new_premium, buyback):
    try:
        return float(new_premium) - float(buyback)
    except:
        return 0.0

def total_pl(initial_premium, rolls_df: pd.DataFrame):
    # total = initial_premium + sum(new_premium) - sum(buyback)
    try:
        sum_new = rolls_df["new_premium"].astype(float).sum() if len(rolls_df) else 0.0
        sum_buy = rolls_df["buyback"].astype(float).sum() if len(rolls_df) else 0.0
        return float(initial_premium or 0.0) + float(sum_new or 0.0) - float(sum_buy or 0.0)
    except:
        # if conversion fails, fallback safe
        s_new = 0.0
        s_buy = 0.0
        for _, r in rolls_df.iterrows():
            try:
                s_new += float(r.get("new_premium", 0) or 0)
            except: pass
            try:
                s_buy += float(r.get("buyback", 0) or 0)
            except: pass
        return float(initial_premium or 0.0) + s_new - s_buy

# -------------------------
# Begin UI
# -------------------------
st.title("Options Roll Tool — Stacked Rolls (No CSV required initially)")

st.markdown("""
Enter a ticker, save an initial position, then press **New Roll** to create a fresh roll block.
Each roll's P/L = New Premium Received − Buy Back Price.
Total P/L = Initial premium + sum(new premiums) − sum(buybacks).
""")

# --- Ticker input ---
ticker = st.text_input("Stock Ticker (e.g., QQQ, AAPL)").upper().strip()
if not ticker:
    st.info("Type a ticker to begin.")
    st.stop()

# load stored meta & rolls (if any)
meta = load_meta(ticker)  # dict or None
rolls_df = load_rolls(ticker)  # DataFrame possibly empty

if meta:
    st.success(f"Loaded saved initial for {ticker}.")
else:
    st.info(f"No saved initial for {ticker} (save initial to begin).")

# -------------------------
# Initial trade (fixed once saved)
# -------------------------
st.subheader("Initial Trade (stays fixed)")

c1, c2, c3, c4 = st.columns([1,1,1,1])

with c1:
    option_type = st.selectbox("Option Type", ["Put", "Call"], index=0, key=f"{ticker}_type")

with c2:
    initial_strike = st.number_input("Initial Strike", min_value=0.0, step=0.1, key=f"{ticker}_init_strike")

with c3:
    initial_expiry = st.date_input("Initial Expiry Date", value=date.today(), key=f"{ticker}_init_expiry")

with c4:
    initial_premium = st.number_input("Initial Premium Received", min_value=0.0, step=0.1, key=f"{ticker}_init_prem")

# Show saved meta if exists
if meta:
    st.markdown("**Saved Initial:**")
    colA, colB, colC, colD = st.columns(4)
    with colA:
        st.write("Option Type")
        st.write(meta.get("option_type"))
    with colB:
        st.write("Initial Strike")
        st.write(meta.get("initial_strike"))
    with colC:
        st.write("Initial Expiry")
        st.write(meta.get("initial_expiry"))
    with colD:
        st.write("Initial Premium Received")
        st.write(meta.get("initial_premium"))

# Save initial
if st.button("Save Initial"):
    # store as simple JSON meta
    meta_obj = {
        "option_type": option_type,
        "initial_strike": float(initial_strike),
        "initial_expiry": str(initial_expiry),
        "initial_premium": float(initial_premium)
    }
    save_meta(ticker, meta_obj)
    st.success("Initial saved.")
    # reload meta variable in-session
    meta = meta_obj

# -------------------------
# New Roll Blocks (stacked)
# -------------------------
st.markdown("---")
st.subheader("Roll Details")

if "roll_blocks" not in st.session_state:
    st.session_state["roll_blocks"] = 0

if st.button("➕ New Roll"):
    st.session_state["roll_blocks"] += 1

if st.session_state["roll_blocks"] == 0:
    st.info("Click 'New Roll' to open a fresh roll block. Previous saved rolls are shown below.")
else:
    st.write("Open roll blocks (previous saved rolls remain below). Fill the fields; P/L auto-updates.")
    for i in range(st.session_state["roll_blocks"]):
        exp = st.expander(f"Roll #{i+1}", expanded=True)
        with exp:
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                new_strike = st.number_input(f"New Strike (Roll {i+1})", min_value=0.0, step=0.1, key=f"{ticker}_rs_{i}")
            with r2:
                new_expiry = st.date_input(f"New Expiry (Roll {i+1})", key=f"{ticker}_re_{i}")
            with r3:
                new_premium = st.number_input(f"New Premium Received (Roll {i+1})", min_value=0.0, step=0.1, key=f"{ticker}_rp_{i}")
            with r4:
                buy_back = st.number_input(f"Buy Back Price (Roll {i+1})", min_value=0.0, step=0.1, key=f"{ticker}_rb_{i}")

            # auto P/L for this roll
            pl_val = roll_pl(new_premium, buy_back)
            if pl_val >= 0:
                st.markdown(f"<h4 style='color:green;'>Roll P/L: {pl_val:.2f}</h4>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h4 style='color:red;'>Roll P/L: {pl_val:.2f}</h4>", unsafe_allow_html=True)

            # Projected total P/L if we saved this roll now
            saved_initial = meta.get("initial_premium") if meta else 0.0
            # build a temporary rolls_df including existing saved rolls + this unsaved roll
            tmp = rolls_df.copy()
            tmp = tmp.append({
                "roll": (tmp["roll"].max() if len(tmp) else 0) + 1,
                "buyback": buy_back,
                "new_strike": new_strike,
                "new_expiry": str(new_expiry),
                "new_premium": new_premium,
                "pl": pl_val
            }, ignore_index=True)
            proj_total = total_pl(saved_initial, tmp)
            # Show projected cumulative
            if proj_total >= 0:
                st.markdown(f"<b>Projected Total P/L (including initial):</b> <span style='color:green'>{proj_total:.2f}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<b>Projected Total P/L (including initial):</b> <span style='color:red'>{proj_total:.2f}</span>", unsafe_allow_html=True)

            # Save roll button
            if st.button(f"Save Roll #{i+1}", key=f"{ticker}_save_{i}"):
                # check meta exists (initial saved)
                if not meta:
                    st.error("Please save the initial trade first before saving rolls.")
                else:
                    # prepare new row and append
                    next_roll_num = int(rolls_df["roll"].max() + 1) if len(rolls_df) else 1
                    row = {
                        "roll": next_roll_num,
                        "buyback": float(buy_back),
                        "new_strike": float(new_strike),
                        "new_expiry": str(new_expiry),
                        "new_premium": float(new_premium),
                        "pl": round(float(pl_val), 2)
                    }
                    rolls_df = rolls_df.append(row, ignore_index=True)
                    save_rolls(ticker, rolls_df)
                    st.success(f"Saved Roll #{next_roll_num} for {ticker}.")
                    # do not remove the block automatically; user can add more

# -------------------------
# Saved Rolls view and totals
# -------------------------
st.markdown("---")
st.subheader("Saved Rolls (per ticker)")

if len(rolls_df) == 0:
    st.info("No saved rolls yet for this ticker.")
else:
    # show each roll as its own expander (Roll 1 / Roll 2 / ...)
    for idx, r in rolls_df.iterrows():
        num = int(r["roll"])
        exp = st.expander(f"Saved Roll #{num}", expanded=False)
        with exp:
            st.write(f"New Strike: {r['new_strike']}")
            st.write(f"New Expiry: {r['new_expiry']}")
            st.write(f"New Premium Received: {r['new_premium']}")
            st.write(f"Buy Back Price: {r['buyback']}")
            pl_show = float(r["pl"]) if r["pl"] != "" else 0.0
            if pl_show >= 0:
                st.markdown(f"<b>P/L:</b> <span style='color:green'>{pl_show:.2f}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<b>P/L:</b> <span style='color:red'>{pl_show:.2f}</span>", unsafe_allow_html=True)

    # show totals
    init_p = meta.get("initial_premium") if meta else 0.0
    tot = total_pl(init_p, rolls_df)
    st.markdown("---")
    if tot >= 0:
        st.markdown(f"<h3 style='color:green;'>Total P/L (Initial + Rolls): {tot:.2f}</h3>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h3 style='color:red;'>Total P/L (Initial + Rolls): {tot:.2f}</h3>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Data stored locally in the app container (data folder). Use Export/Import if you want persistence across redeploys.")
