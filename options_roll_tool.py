import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Roll Calculator (Stacked Rolls)", layout="wide")

# ---------- Helpers ----------
def ensure_state():
    if "tickers" not in st.session_state:
        # tickers: dict ticker -> { initial: {...}, rolls: [ {new_strike,...,pl} ... ] }
        st.session_state["tickers"] = {}
    if "unsaved" not in st.session_state:
        # unsaved: dict ticker -> list of unsaved roll placeholders
        st.session_state["unsaved"] = {}

def get_last_initial_for_ticker(ticker):
    t = st.session_state["tickers"].get(ticker)
    if t:
        return t["initial"]
    return None

def save_initial(ticker, initial_data):
    st.session_state["tickers"][ticker] = {"initial": initial_data, "rolls": []}
    st.session_state["unsaved"].pop(ticker, None)

def add_unsaved_roll(ticker):
    st.session_state["unsaved"].setdefault(ticker, [])
    # append an empty roll
    st.session_state["unsaved"][ticker].append({
        "new_strike": None,
        "new_premium": None,
        "buyback_price": None,
        "new_expiry": None
    })

def commit_roll(ticker, roll):
    # compute pl and append to saved rolls
    pl = 0.0
    try:
        pl = float(roll.get("new_premium", 0) or 0) - float(roll.get("buyback_price", 0) or 0)
    except:
        pl = 0.0
    roll_record = {
        "new_strike": roll.get("new_strike"),
        "new_expiry": roll.get("new_expiry"),
        "new_premium": roll.get("new_premium"),
        "buyback_price": roll.get("buyback_price"),
        "pl": round(pl, 2)
    }
    st.session_state["tickers"].setdefault(ticker, {"initial": None, "rolls": []})
    st.session_state["tickers"][ticker]["rolls"].append(roll_record)

def get_cumulative_pl(ticker):
    t = st.session_state["tickers"].get(ticker)
    if not t:
        return 0.0
    return sum(r.get("pl", 0) for r in t["rolls"])

ensure_state()

st.title("Options Roll Tool — stacked rolls & quick save")
st.markdown("Workflow: enter ticker → load or save initial → press **New Roll** to open a blank roll block → fill values (P/L auto-updates) → press **Save Roll** to append to table.")

# ---------- Ticker selection / load ----------
col_t1, col_t2 = st.columns([3,1])
with col_t1:
    ticker = st.text_input("Stock Ticker (e.g. QQQ, AAPL)", value="", max_chars=10).upper().strip()
with col_t2:
    if st.button("Load / Refresh"):
        # no-op other than refresh — session_state persists
        st.experimental_rerun()

if not ticker:
    st.info("Type a ticker to begin (or click Load/Refresh if you already saved data).")
    st.stop()

# load initial if exists
initial = get_last_initial_for_ticker(ticker)

st.header(f"Ticker: {ticker}")

# ---------- Initial section (fixed once saved) ----------
st.subheader("Initial position (fixed once saved)")

if initial:
    # display initial as disabled/read-only values
    c1, c2, c3 = st.columns(3)
    with c1:
        st.number_input("Initial Strike", value=float(initial.get("initial_strike")), key=f"{ticker}_initial_strike", disabled=True)
    with c2:
        st.date_input("Initial Expiry", value=pd.to_datetime(initial.get("initial_expiry")).date(), key=f"{ticker}_initial_expiry", disabled=True)
    with c3:
        st.number_input("Initial Premium Received", value=float(initial.get("initial_premium")), key=f"{ticker}_initial_prem", disabled=True)
    st.caption("Initial values are loaded from the saved data and cannot be changed here. To reset, delete the ticker (see button below).")
    if st.button("Delete ticker data (remove all saved rolls and initial)", key=f"del_{ticker}"):
        st.session_state["tickers"].pop(ticker, None)
        st.session_state["unsaved"].pop(ticker, None)
        st.success(f"Deleted data for {ticker}. Reload the page or enter ticker again to create fresh initial.")
        st.experimental_rerun()
else:
    # allow user to set initial values and save
    c1, c2, c3 = st.columns(3)
    with c1:
        initial_strike_input = st.number_input("Initial Strike", value=100.0, key=f"{ticker}_initial_strike_input")
    with c2:
        initial_expiry_input = st.date_input("Initial Expiry", value=date.today(), key=f"{ticker}_initial_expiry_input")
    with c3:
        initial_prem_input = st.number_input("Initial Premium Received", value=1.0, key=f"{ticker}_initial_prem_input")
    if st.button("Save Initial for " + ticker):
        save_initial(ticker, {
            "initial_strike": float(initial_strike_input),
            "initial_expiry": str(initial_expiry_input),
            "initial_premium": float(initial_prem_input)
        })
        st.success(f"Initial saved for {ticker}. Press Load/Refresh to refresh UI.")
        st.experimental_rerun()

st.markdown("---")

# ---------- Rolls controls ----------
st.subheader("Roll Details")
col_r1, col_r2 = st.columns([1,1])
with col_r1:
    if st.button("New Roll", key=f"newroll_{ticker}"):
        add_unsaved_roll(ticker)
        st.experimental_rerun()
with col_r2:
    st.write("")  # placeholder for spacing

# show unsaved roll blocks (each block stays visible, previous ones remain)
unsaved = st.session_state["unsaved"].get(ticker, [])

if len(unsaved) == 0:
    st.info("No open roll blocks. Click **New Roll** to create one (previous saved rolls are shown below).")
else:
    st.write("Open roll blocks (previous blocks remain visible). Fill fields; P/L auto-updates. When ready, press **Save Roll** to commit to the table.")
    for idx, roll in enumerate(unsaved):
        exp = st.expander(f"Roll block #{idx+1}", expanded=True)
        with exp:
            # use unique keys so Streamlit preserves inputs across runs
            ns_key = f"{ticker}_unsaved_{idx}_new_strike"
            np_key = f"{ticker}_unsaved_{idx}_new_premium"
            bp_key = f"{ticker}_unsaved_{idx}_buyback"
            ne_key = f"{ticker}_unsaved_{idx}_new_expiry"

            new_strike_val = st.number_input("New Strike price", value=roll.get("new_strike") or 0.0, key=ns_key)
            new_premium_val = st.number_input("New premium received", value=roll.get("new_premium") or 0.0, key=np_key)
            buyback_val = st.number_input("Option buy price (buyback)", value=roll.get("buyback_price") or 0.0, key=bp_key)
            new_expiry_val = st.date_input("New Expiry date", value=roll.get("new_expiry") or date.today(), key=ne_key)

            # keep the unsaved state in sync with UI inputs
            st.session_state["unsaved"][ticker][idx]["new_strike"] = float(new_strike_val)
            st.session_state["unsaved"][ticker][idx]["new_premium"] = float(new_premium_val)
            st.session_state["unsaved"][ticker][idx]["buyback_price"] = float(buyback_val)
            st.session_state["unsaved"][ticker][idx]["new_expiry"] = str(new_expiry_val)

            # Auto-calc P/L
            try:
                pl = float(new_premium_val) - float(buyback_val)
            except:
                pl = 0.0

            # show P/L color-coded
            if pl > 0:
                st.markdown(f"<h4 style='color:green;'>Roll P/L: {pl:.2f}</h4>", unsafe_allow_html=True)
            elif pl < 0:
                st.markdown(f"<h4 style='color:red;'>Roll P/L: {pl:.2f}</h4>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h4>Roll P/L: {pl:.2f}</h4>", unsafe_allow_html=True)

            # Show cumulative if there are saved rolls already
            cumulative_before = get_cumulative_pl(ticker)
            st.write(f"Cumulative P/L before committing this roll: {cumulative_before:.2f}")
            st.write(f"Projected cumulative after this roll: {cumulative_before + pl:.2f}")

            # Commit button
            if st.button("Save Roll (commit to table)", key=f"save_{ticker}_{idx}"):
                # commit and remove this unsaved roll
                commit_roll(ticker, st.session_state["unsaved"][ticker][idx])
                # remove the saved unsaved block
                st.session_state["unsaved"][ticker].pop(idx)
                st.success("Roll saved and added to table.")
                st.experimental_rerun()

st.markdown("---")

# ---------- Show saved rolls table and summary ----------
st.subheader("Saved Rolls Table (source of truth)")

ticker_data = st.session_state["tickers"].get(ticker)
if not ticker_data:
    st.info("No saved data for this ticker yet.")
else:
    initial = ticker_data["initial"]
    st.markdown("**Initial**")
    colI1, colI2, colI3 = st.columns(3)
    with colI1:
        st.write("Initial Strike")
        st.write(initial.get("initial_strike"))
    with colI2:
        st.write("Initial Expiry")
        st.write(initial.get("initial_expiry"))
    with colI3:
        st.write("Initial Premium Received")
        st.write(initial.get("initial_premium"))

    st.write("---")
    rolls = ticker_data.get("rolls", [])
    if len(rolls) == 0:
        st.info("No saved rolls yet for this ticker.")
    else:
        # build a dataframe for display
        df = pd.DataFrame(rolls)
        # add index starting at 1
        df.index = range(1, len(df) + 1)
        df_display = df.rename(columns={
            "new_strike": "New Strike",
            "new_expiry": "New Expiry",
            "new_premium": "New Premium",
            "buyback_price": "Buyback Price",
            "pl": "P/L"
        })
        st.dataframe(df_display, use_container_width=True)

        cumulative = get_cumulative_pl(ticker)
        if cumulative > 0:
            st.markdown(f"<h3 style='color:green;'>Cumulative P/L: {cumulative:.2f}</h3>", unsafe_allow_html=True)
        elif cumulative < 0:
            st.markdown(f"<h3 style='color:red;'>Cumulative P/L: {cumulative:.2f}</h3>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3>Cumulative P/L: {cumulative:.2f}</h3>", unsafe_allow_html=True)

# ---------- Export / Import simple CSV for manual persistence ----------
st.markdown("---")
st.subheader("Export / Import (manual persistence)")

col_e1, col_e2 = st.columns(2)
with col_e1:
    if st.button("Export all tickers to CSV"):
        rows = []
        for tk, data in st.session_state["tickers"].items():
            initial = data["initial"]
            for r in data["rolls"]:
                rows.append({
                    "Ticker": tk,
                    "Initial Strike": initial.get("initial_strike"),
                    "Initial Expiry": initial.get("initial_expiry"),
                    "Initial Premium": initial.get("initial_premium"),
                    "New Strike": r.get("new_strike"),
                    "New Expiry": r.get("new_expiry"),
                    "New Premium": r.get("new_premium"),
                    "Buyback": r.get("buyback_price"),
                    "P/L": r.get("pl")
                })
        if rows:
            dfout = pd.DataFrame(rows)
            csv = dfout.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, file_name="rolls_export.csv", mime="text/csv")
        else:
            st.info("No data to export.")
with col_e2:
    uploaded = st.file_uploader("Upload CSV to merge/import (optional)", type=["csv"])
    if uploaded is not None:
        try:
            df_in = pd.read_csv(uploaded)
            # expect columns as exported above. We'll merge per ticker.
            for _, row in df_in.iterrows():
                tk = str(row["Ticker"]).upper()
                init = {
                    "initial_strike": float(row["Initial Strike"]),
                    "initial_expiry": str(row["Initial Expiry"]),
                    "initial_premium": float(row["Initial Premium"])
                }
                if tk not in st.session_state["tickers"]:
                    st.session_state["tickers"][tk] = {"initial": init, "rolls": []}
                # append roll
                roll_r = {
                    "new_strike": float(row["New Strike"]),
                    "new_expiry": str(row["New Expiry"]),
                    "new_premium": float(row["New Premium"]),
                    "buyback_price": float(row["Buyback"]),
                    "pl": float(row["P/L"])
                }
                st.session_state["tickers"][tk]["rolls"].append(roll_r)
            st.success("Imported CSV and merged into session data.")
            st.experimental_rerun()
        except Exception as e:
            st.error("Failed to import CSV: " + str(e))
