from forex_python.converter import CurrencyRates
import pandas as pd

def convert_to_inr(df, base_column='Currency', amount_column='Proceeds'):
    c = CurrencyRates()
    df = df.copy()
    df['INR Amount'] = 0.0

    for idx, row in df.iterrows():
        base_currency = row.get(base_column)
        amount = row.get(amount_column)

        # Skip rows with missing data
        if pd.isna(base_currency) or pd.isna(amount):
            continue

        try:
            if base_currency == 'INR':
                df.at[idx, 'INR Amount'] = amount
            else:
                rate = c.get_rate(base_currency, 'INR')
                df.at[idx, 'INR Amount'] = amount * rate
        except Exception as e:
            print(f"[ERROR] Row {idx} - Failed to convert {amount} {base_currency}: {e}")
            df.at[idx, 'INR Amount'] = None  # or amount

    return df
