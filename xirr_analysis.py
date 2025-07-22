from datetime import datetime
from typing import List, Dict
import pandas as pd

def xnpv(rate, cashflows):
    t0 = cashflows[0][0]
    return sum([cf / (1 + rate) ** ((t - t0).days / 365) for t, cf in cashflows])

def xirr(cashflows):
    from scipy.optimize import newton
    try:
        return newton(lambda r: xnpv(r, cashflows), 0.1)
    except (RuntimeError, OverflowError):
        return None

def calculate_xirr(df: pd.DataFrame) -> Dict[str, float]:
    results = {}
    for symbol in df['Symbol'].unique():
        trades = df[df['Symbol'] == symbol]
        cashflows = []
        for _, row in trades.iterrows():
            date = row['Date/time']
            cashflow = row['Proceeds'] - row['Comm/fee']
            cashflows.append((date, -cashflow))
        if cashflows:
            last_date = trades['Date/time'].max()
            holding = trades['Quantity'].sum()
            if holding != 0:
                cashflows.append((last_date, 0))  # Placeholder for current value
            rate = xirr(cashflows)
            if rate is not None:
                results[symbol] = rate
    return results
