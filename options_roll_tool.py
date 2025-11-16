import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Options Roll Calculator",
    layout="wide",
)

st.title("📈 Options Roll Calculator")
st.caption("Compare your current short option vs. a new rolled position (not financial advice).")

# ---------- SIDEBAR: GLOBAL SETTINGS ----------
with st.sidebar:
    st.header("⚙️ Settings")

    position_type = st.selectbox(
        "Position type",
        ["Short Call", "Short Put"],
        index=0,
        help="Choose whether you are rolling a short call or a short put.",
    )

    contracts = st.number_input(
        "Number of contracts",
        min_value=1,
        value=1,
        step=1,
    )

    contract_size = st.number_input(
        "Contract size (shares per contract)",
        min_value=1,
        value=100,
        step=1,
        help="US equity options are usually 100 shares per contract.",
    )

    commission_per_contract_close = st.number_input(
        "Commission per contract to CLOSE current leg",
        min_value=0.0,
        value=0.0,
        step=0.01,
    )

    commission_per_contract_open = st.number_input(
        "Commission per contract to OPEN new leg",
        min_value=0.0,
        value=0.0,
        step=0.01,
    )

# ---------- LAYOUT ----------
col_current, col_new = st.columns(2)

# ---------- CURRENT POSITION INPUTS ----------
with col_current:
    st.subheader("🔻 Current Short Option (to be closed)")

    underlying_symbol = st.text_input(
        "Underlying symbol (ticker)",
        value="QQQ",
    )

    current_underlying_price = st.number_input(
        "Current underlying price",
        min_value=0.0,
        value=400.0,
        step=0.5,
    )

    current_strike = st.number_input(
        "Current short strike",
        min_value=0.0,
        value=410.0,
        step=0.5,
    )

    current_expiry = st.date_input(
        "Current expiry date",
        value=date.today(),
    )

    entry_premium = st.number_input(
        "Original premium RECEIVED (per share) when you opened this short option",
        min_value=0.0,
        value=4.00,
        step=0.05,
        help="Example: if you sold for $4.00, enter 4.00",
    )

    current_option_price = st.number_input(
        "Current option price to CLOSE (per share)",
        min_value=0.0,
        value=6.50,
        step=0.05,
        help="Mid price you expect to pay to close the current option.",
    )

# ---------- NEW POSITION INPUTS ----------
with col_new:
    st.subheader("🔁 New Short Option (after rolling)")

    new_strike = st.number_input(
        "New short strike",
        min_value=0.0,
        value=420.0,
        step=0.5,
    )

    new_expiry = st.date_input(
        "New expiry date",
        value=date.today(),
        key="new_expiry",
    )

    new_premium = st.number_input(
        "Premium RECEIVED for NEW short option (per share)",
        min_value=0.0,
        value=7.00,
        step=0.05,
        help="Expected premium for the new short option.",
    )

    # Optional: hedging leg (vertical spread)
    st.markdown("### Optional Hedge (Vertical Spread)")
    use_hedge = st.checkbox("Add long option leg (for a spread)?")

    hedge_strike = None
    hedge_premium = None
    if use_hedge:
        hedge_strike = st.number_input(
            "Long leg strike (hedge)",
            min_value=0.0,
            value=new_strike + 10 if position_type == "Short Call" else max(0.0, new_strike - 10),
            step=0.5,
        )
        hedge_premium = st.number_input(
            "Premium PAID for long leg (per share)",
            min_value=0.0,
            value=2.00,
            step=0.05,
        )

# ---------- CALCULATE BUTTON ----------
calculate = st.button("🔍 Calculate Roll")

if calculate:
    # Basic quantities
    qty = contracts * contract_size

    # ---- Current leg P/L if you close now ----
    gross_premium_received = entry_premium * qty
    cost_to_close = current_option_price * qty
    total_commissions_close = commission_per_contract_close * contracts

    realized_pnl_current_leg = gross_premium_received - cost_to_close - total_commissions_close

    # ---- New leg cashflow ----
    cash_in_new_short = new_premium * qty
    total_commissions_open = commission_per_contract_open * contracts

    cash_out_hedge = 0.0
    if use_hedge and hedge_premium is not None:
        cash_out_hedge = hedge_premium * qty

    net_cashflow_today = (
        -cost_to_close  # closing old short
        + cash_in_new_short  # opening new short
        - cash_out_hedge  # paying for hedge
        - total_commissions_close
        - total_commissions_open
    )

    total_premium_collected_gross = entry_premium + new_premium - (hedge_premium or 0.0)
    total_premium_collected_cash = (
        gross_premium_received + cash_in_new_short - cash_out_hedge
        - total_commissions_close - total_commissions_open
    )

    # ---- New breakeven (per share) ----
    # Use net credits from BOTH shorts minus hedge cost, divided by contract size.
    # For simplicity: breakeven = strike +/- total net credit per share
    net_credit_per_share_from_shorts = entry_premium + new_premium
    hedge_cost_per_share = hedge_premium or 0.0
    net_credit_per_share = net_credit_per_share_from_shorts - hedge_cost_per_share

    if position_type == "Short Put":
        new_breakeven = new_strike - net_credit_per_share
    else:
        new_breakeven = new_strike + net_credit_per_share

    # ---- Days to new expiry ----
    today = date.today()
    days_to_new_expiry = (new_expiry - today).days

    # ---------- METRICS DISPLAY ----------
    st.markdown("---")
    st.subheader("📊 Roll Summary")

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "Realized P/L on current leg (if closed now)",
            f"${realized_pnl_current_leg:,.2f}",
        )

    with m2:
        per_contract_roll_credit = new_premium - current_option_price - (hedge_premium or 0.0)
        total_roll_credit = per_contract_roll_credit * qty - total_commissions_close - total_commissions_open

        st.metric(
            "Net roll credit / debit TODAY (all legs)",
            f"${total_roll_credit:,.2f}",
            help="Includes cost to close, new short premium, hedge premium, and commissions.",
        )

    with m3:
        st.metric(
            "Total net premium (shorts minus hedge, per share)",
            f"${net_credit_per_share:,.2f}",
        )

    with m4:
        st.metric(
            "New breakeven price",
            f"${new_breakeven:,.2f}",
            help="Approx. breakeven after the roll, using new strike and total net credit.",
        )

    st.markdown(
        f"""
        **Underlying:** `{underlying_symbol}`  
        **New strike:** {new_strike} • **New expiry:** {new_expiry}  
        **Days to new expiry:** `{days_to_new_expiry}` days  
        """
    )

    # ---------- PAYOFF CHART AT NEW EXPIRY ----------
    st.markdown("---")
    st.subheader("📉 P/L at New Expiry (Approximate)")

    # Build price range
    price_center = current_underlying_price if current_underlying_price > 0 else new_strike
    price_min = max(0, price_center * 0.5)
    price_max = price_center * 1.5 if price_center > 0 else new_strike * 1.5
    prices = np.linspace(price_min, price_max, 100)

    # Payoff of new short at expiry (per share)
    if position_type == "Short Call":
        payoff_new_short_per_share = new_premium - np.maximum(0, prices - new_strike)
    else:  # Short Put
        payoff_new_short_per_share = new_premium - np.maximum(0, new_strike - prices)

    # Hedge payoff (per share)
    hedge_payoff_per_share = np.zeros_like(prices)
    if use_hedge and hedge_strike is not None:
        if position_type == "Short Call":
            # Long call as hedge
            hedge_payoff_per_share = -hedge_premium + np.maximum(0, prices - hedge_strike)
        else:
            # Long put as hedge
            hedge_payoff_per_share = -hedge_premium + np.maximum(0, hedge_strike - prices)

    # Total P/L at new expiry (all contracts), including realized P/L from old leg
    total_pl_per_share = payoff_new_short_per_share + hedge_payoff_per_share
    total_pl_all_contracts = total_pl_per_share * qty + realized_pnl_current_leg

    df = pd.DataFrame(
        {
            "Underlying Price": prices,
            "P/L at New Expiry (all contracts)": total_pl_all_contracts,
        }
    ).set_index("Underlying Price")

    st.line_chart(df)

    st.info(
        "This chart is a simplified payoff at the NEW expiry, assuming you close the current leg "
        "now and open the new leg today. It does not include margin, assignment risk, early "
        "exercise, or tax effects."
    )
else:
    st.info("Fill in your inputs on the left and click **“Calculate Roll”** to see the results.")
