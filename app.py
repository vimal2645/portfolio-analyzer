import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime
from xirr_analysis import calculate_xirr
from forex_python.converter import CurrencyRates, RatesNotAvailableError
from stock_split_handler import load_stock_splits, apply_splits

st.set_page_config(page_title="Portfolio Analyzer", layout="wide")

st.title("📊 Portfolio Analyzer (2023–2025)")
st.markdown("Upload three CSV files — one for each year (2023, 2024, 2025)")

uploaded_files = st.file_uploader(
    "Upload your trading CSVs", type="csv", accept_multiple_files=True, help="Drag and drop 3 CSVs for 2023, 2024, and 2025"
)

# Step Tracker UI
def step_progress(current_step):
    steps = [
        "Upload & Merge CSVs",
        "Clean & Analyze",
        "Apply Stock Splits",
        "Convert to INR",
        "XIRR & Final Analysis"
    ]
    for i, label in enumerate(steps, 1):
        if i < current_step:
            prefix = "✅"
        elif i == current_step:
            prefix = "🔄"
        else:
            prefix = "⬜"
        st.markdown(f"{prefix} **Step {i}: {label}**")

@st.cache_data
def load_and_clean(file):
    df = pd.read_csv(file)
    rename_map = {
        'Date/Time': 'Date/time',
        'Comm/Fee': 'Comm/fee',
        'Realized P/L': 'Realized p/l',
        'T. Price': 'T. price'
    }
    df.rename(columns=rename_map, inplace=True)
    expected_columns = {'Symbol', 'Date/time', 'Quantity', 'T. price', 'Proceeds', 'Comm/fee', 'Realized p/l'}
    df.columns = [col.strip() for col in df.columns]
    if not expected_columns.issubset(set(df.columns)):
        return None, df.columns
    df['Date/time'] = pd.to_datetime(df['Date/time'], errors='coerce')
    df.dropna(subset=['Date/time'], inplace=True)
    for col in ['Quantity', 'T. price', 'Proceeds', 'Comm/fee', 'Realized p/l']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['Quantity', 'T. price', 'Proceeds', 'Comm/fee', 'Realized p/l'], inplace=True)
    return df, None

# Currency Conversion with rate log
def convert_to_inr(df, base_currency="USD"):
    cr = CurrencyRates()
    df = df.copy()
    df["Proceeds_INR"] = None
    logs = []
    for i, row in df.iterrows():
        date = row["Date/time"].date()
        try:
            rate = cr.get_rate(base_currency, "INR", date)
            df.at[i, "Proceeds_INR"] = row["Proceeds"] * rate
            logs.append((row['Symbol'], date, rate))
        except RatesNotAvailableError:
            df.at[i, "Proceeds_INR"] = None
            logs.append((row['Symbol'], date, "Rate Not Available"))
    return df, logs

# ========== MAIN LOGIC ========== #
if uploaded_files and len(uploaded_files) == 3:
    step_progress(1)

    all_data = []
    for file in uploaded_files:
        df, err = load_and_clean(file)
        if df is None:
            st.error(f"❌ File `{file.name}` is missing required columns.\nFound columns: {list(err)}")
            st.stop()
        all_data.append(df)

    trading_df = pd.concat(all_data)
    trading_df.sort_values(by='Date/time', inplace=True)

    step_progress(2)

    st.subheader("📋 Trading Data")
    st.dataframe(trading_df)

    total_trades = len(trading_df)
    net_pl = trading_df['Realized p/l'].sum()

    st.subheader("💼 Master Holdings")
    master = trading_df.groupby("Symbol").agg({
        "Quantity": "sum",
        "Realized p/l": "sum"
    }).reset_index()
    st.dataframe(master)

    st.subheader("📈 Basic Analysis")
    col1, col2 = st.columns(2)
    col1.metric("Total Trades", total_trades)
    col2.metric("Net Profit/Loss", f"₹{net_pl:,.2f}")

    st.subheader("🏆 Top 5 Gainers")
    gainers = master.sort_values(by="Realized p/l", ascending=False).head(5)
    st.dataframe(gainers)

    st.subheader("🔻 Top 5 Losers")
    losers = master.sort_values(by="Realized p/l", ascending=True).head(5)
    st.dataframe(losers)

    step_progress(3)
    st.subheader("🔍 Stock Split Details")
    stock_splits = load_stock_splits()
    st.dataframe(stock_splits)
    trading_df = apply_splits(trading_df, stock_splits)

    step_progress(4)
    st.subheader("💱 Currency Conversion (USD → INR)")
    with st.spinner("Converting to INR using historical forex rates..."):
        try:
            trading_df, conversion_logs = convert_to_inr(trading_df, base_currency="USD")
            st.success("✅ Currency successfully converted using `forex-python`")
            with st.expander("🔍 View Conversion Logs"):
                logs_df = pd.DataFrame(conversion_logs, columns=["Symbol", "Date", "Rate"])
                st.dataframe(logs_df)
        except Exception as e:
            st.warning(f"⚠️ Conversion failed: {e}")

    step_progress(5)
    st.subheader("💰 XIRR Analysis")
    try:
        xirr_result = calculate_xirr(trading_df)
        if xirr_result:
            for symbol, rate in xirr_result.items():
                st.markdown(f"**{symbol}**: `{rate:.2%}`")
        else:
            st.warning("⚠️ Not enough valid transactions to compute XIRR.")
    except Exception as e:
        st.warning(f"⚠️ XIRR Calculation failed: {e}")

    st.subheader("📥 Export Data")
    csv = trading_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Cleaned Data", csv, "cleaned_trades.csv", "text/csv")

else:
    st.info("📂 Please upload exactly 3 CSV files — one each for 2023, 2024, and 2025.")
