import streamlit as st
import pandas as pd

st.title("Options Roll Tool — Clean Stable Version")

st.subheader("Initial Premium")
initial_premium = st.number_input("Initial Premium Received ($)", value=0.00)

st.subheader("Add Your Rolls")

# A container to store all roll entries
roll_data = []

# Number of rolls the user wants to enter
num_rolls = st.number_input("How many rolls?", min_value=0, value=1, step=1)

for i in range(num_rolls):
    st.markdown(f"### Roll {i+1}")

    col1, col2, col3 = st.columns(3)

    with col1:
        strike = st.text_input(f"Strike Price (Roll {i+1})", key=f"strike_{i}")

    with col2:
        expiration = st.text_input(f"Expiration (Roll {i+1})", key=f"exp_{i}")

    with col3:
        credit_or_debit = st.selectbox(
            f"Credit / Debit (Roll {i+1})",
            ["Credit (+)", "Debit (-)"],
            key=f"type_{i}"
        )

    premium = st.number_input(
        f"Premium Amount (Roll {i+1})",
        value=0.00,
        key=f"premium_{i}"
    )

    # Store roll entry
    roll_data.append({
        "Roll": f"Roll {i+1}",
        "Strike": strike,
        "Expiration": expiration,
        "Type": credit_or_debit,
        "Amount": premium
    })

# Convert to DataFrame
df = pd.DataFrame(roll_data)

st.subheader("Roll Summary")
st.dataframe(df)

# Calculate totals
credits = df[df["Type"] == "Credit (+)"]["Amount"].sum()
debits = df[df["Type"] == "Debit (-)"]["Amount"].sum()

total_net = initial_premium + credits - debits

st.subheader("Final Calculation")
st.write(f"**Initial Premium:** ${initial_premium:,.2f}")
st.write(f"**Total Credits:** ${credits:,.2f}")
st.write(f"**Total Debits:** ${debits:,.2f}")

st.markdown("---")
st.write(f"### 🧮 **Total Net Premium:  ${total_net:,.2f}**")
