# 📊 Portfolio Analyzer (2023–2025)
**By Vimal Prakash**

This project is an interactive Streamlit dashboard that helps you analyze your personal trading portfolio across multiple years. It performs advanced financial computations including stock split adjustment, multi-currency conversion, historical price fetching, portfolio valuation, and XIRR calculation.

---

## ✅ What This App Does

- Upload and merge multiple yearly trade CSVs.
- Clean and preprocess trading data.
- Apply stock splits to adjust quantities and prices.
- Convert foreign currency trades (USD, SGD) to INR using historical rates.
- Fetch historical prices of equities using Yahoo Finance.
- Calculate daily portfolio value.
- Compute final return (XIRR) for each holding.
- Visual display of portfolio performance and metrics.

---

## 📂 Project Structure

📁 portfolio-analyzer/
├── app.py
├── stock_split_handler.py
├── xirr_analysis.py
├── requirements.txt
├── README.md

🚀 How to Run
Install dependencies:

pip install -r requirements.txt

Launch the app:

streamlit run app.py

Open in your browser:
👉 http://localhost:5000/#portfolio-analyzer-2023-2025