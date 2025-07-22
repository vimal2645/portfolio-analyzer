import pandas as pd

def load_stock_splits(path="stock_splits.csv"):
    try:
        df = pd.read_csv(path)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=['Date'], inplace=True)
        return df
    except Exception as e:
        print(f"Error loading stock splits: {e}")
        return pd.DataFrame(columns=['Symbol', 'Date', 'Split Ratio'])

def apply_splits(trading_df, split_df):
    trading_df = trading_df.copy()

    for _, row in split_df.iterrows():
        symbol = row['Symbol']
        split_date = row['Date']
        ratio = row['Split Ratio']

        # Apply split to rows before the split date
        mask = (trading_df['Symbol'] == symbol) & (trading_df['Date/time'] < split_date)

        if mask.any():
            trading_df.loc[mask, 'Quantity'] *= ratio
            trading_df.loc[mask, 'T. price'] /= ratio
            trading_df.loc[mask, 'Proceeds'] = trading_df.loc[mask, 'Quantity'] * trading_df.loc[mask, 'T. price']

    return trading_df
