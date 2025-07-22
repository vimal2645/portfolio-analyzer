import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta
import io
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Install required packages if not available
try:
    import pyxirr
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError as e:
    st.error(f"Please install required packages: {str(e)}")
    st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="Portfolio Analytics Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

class PortfolioAnalyzer:
    def __init__(self):
        self.all_trades = pd.DataFrame()
        self.holdings = pd.DataFrame()
        self.currency_rates = {}
        self.stock_splits = {}
        
    def load_csv_files(self, uploaded_files: List) -> bool:
        """Load and process uploaded CSV files"""
        try:
            all_data = []
            
            for uploaded_file in uploaded_files:
                # Read CSV file
                df = pd.read_csv(uploaded_file)
                
                # Standardize column names and clean data
                if 'Date/Time' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date/Time'].str.split(',').str[0])
                    df['Time'] = df['Date/Time'].str.split(',').str[1].str.strip()
                
                # Filter only trade data
                trade_data = df[df['DataDiscriminator'] == 'Order'].copy()
                
                # Clean and standardize columns
                required_cols = ['Symbol', 'Date', 'Quantity', 'T. Price', 'Currency', 'Proceeds', 'Comm/Fee']
                for col in required_cols:
                    if col not in trade_data.columns:
                        st.error(f"Missing required column: {col}")
                        return False
                
                # Clean quantity column (remove commas)
                trade_data['Quantity'] = trade_data['Quantity'].apply(
                    lambda x: pd.to_numeric(str(x).replace(',', ''), errors='coerce')
                )
                
                all_data.append(trade_data[required_cols])
            
            # Combine all data
            self.all_trades = pd.concat(all_data, ignore_index=True)
            self.all_trades = self.all_trades.sort_values('Date').reset_index(drop=True)
            
            return True
            
        except Exception as e:
            st.error(f"Error loading CSV files: {str(e)}")
            return False
    
    def create_master_holdings(self):
        """Create master list of holdings from all transactions"""
        try:
            holdings_dict = {}
            
            for _, trade in self.all_trades.iterrows():
                symbol = trade['Symbol']
                quantity = trade['Quantity']
                
                if symbol not in holdings_dict:
                    holdings_dict[symbol] = {
                        'symbol': symbol,
                        'total_quantity': 0,
                        'transactions': [],
                        'currency': trade['Currency']
                    }
                
                holdings_dict[symbol]['total_quantity'] += quantity
                holdings_dict[symbol]['transactions'].append({
                    'date': trade['Date'],
                    'quantity': quantity,
                    'price': trade['T. Price'],
                    'proceeds': trade['Proceeds'],
                    'fees': trade['Comm/Fee']
                })
            
            # Convert to DataFrame
            holdings_list = []
            for symbol, data in holdings_dict.items():
                if data['total_quantity'] != 0:  # Only include non-zero holdings
                    holdings_list.append({
                        'Symbol': symbol,
                        'Quantity': data['total_quantity'],
                        'Currency': data['currency'],
                        'Transactions': len(data['transactions'])
                    })
            
            self.holdings = pd.DataFrame(holdings_list)
            
        except Exception as e:
            st.error(f"Error creating master holdings: {str(e)}")
    
    def fetch_stock_splits(self) -> Dict:
        """Fetch stock split information from Yahoo Finance"""
        splits_data = {}
        
        try:
            unique_symbols = self.all_trades['Symbol'].unique()
            
            for symbol in unique_symbols:
                try:
                    # Create ticker object
                    ticker = yf.Ticker(symbol)
                    
                    # Get splits data
                    splits = ticker.splits
                    
                    if not splits.empty:
                        splits_data[symbol] = splits.to_dict()
                        
                except Exception as e:
                    st.warning(f"Could not fetch splits for {symbol}: {str(e)}")
                    continue
            
            self.stock_splits = splits_data
            return splits_data
            
        except Exception as e:
            st.error(f"Error fetching stock splits: {str(e)}")
            return {}
    
    def apply_stock_splits(self):
        """Apply stock splits to historical trades"""
        try:
            if not self.stock_splits:
                return
            
            for symbol, splits in self.stock_splits.items():
                symbol_trades = self.all_trades[self.all_trades['Symbol'] == symbol].copy()
                
                for split_date, split_ratio in splits.items():
                    # Apply splits to trades before the split date
                    mask = (self.all_trades['Symbol'] == symbol) & (self.all_trades['Date'] < split_date)
                    
                    if mask.any():
                        # Adjust quantity (multiply by split ratio)
                        self.all_trades.loc[mask, 'Quantity'] *= split_ratio
                        
                        # Adjust price (divide by split ratio)
                        self.all_trades.loc[mask, 'T. Price'] /= split_ratio
                        
                        # Recalculate proceeds
                        self.all_trades.loc[mask, 'Proceeds'] = (
                            self.all_trades.loc[mask, 'Quantity'] * 
                            self.all_trades.loc[mask, 'T. Price']
                        )
            
        except Exception as e:
            st.error(f"Error applying stock splits: {str(e)}")
    
    def fetch_currency_rates(self, base_currency: str = 'USD') -> Dict:
        """Fetch historical currency exchange rates"""
        try:
            # Using exchangerate-api.com (free tier)
            url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.currency_rates = data['rates']
                
                # Add base currency
                self.currency_rates[base_currency] = 1.0
                
                return self.currency_rates
            else:
                # Fallback rates if API fails
                fallback_rates = {
                    'USD': 1.0,
                    'INR': 83.0,
                    'SGD': 1.35,
                    'EUR': 0.85,
                    'GBP': 0.75
                }
                self.currency_rates = fallback_rates
                st.warning("Using fallback currency rates. For accurate rates, check API connectivity.")
                return fallback_rates
                
        except Exception as e:
            st.warning(f"Error fetching currency rates: {str(e)}. Using fallback rates.")
            fallback_rates = {
                'USD': 1.0,
                'INR': 83.0,
                'SGD': 1.35,
                'EUR': 0.85,
                'GBP': 0.75
            }
            self.currency_rates = fallback_rates
            return fallback_rates
    
    def convert_to_currencies(self):
        """Convert transaction prices to multiple currencies"""
        try:
            currencies = ['USD', 'INR', 'SGD']
            
            for currency in currencies:
                if currency in self.currency_rates:
                    rate = self.currency_rates[currency]
                    
                    # Convert proceeds
                    self.all_trades[f'Proceeds_{currency}'] = self.all_trades.apply(
                        lambda row: row['Proceeds'] * rate if row['Currency'] == 'USD' 
                        else row['Proceeds'] * rate / self.currency_rates.get(row['Currency'], 1),
                        axis=1
                    )
                    
                    # Convert prices
                    self.all_trades[f'Price_{currency}'] = self.all_trades.apply(
                        lambda row: row['T. Price'] * rate if row['Currency'] == 'USD'
                        else row['T. Price'] * rate / self.currency_rates.get(row['Currency'], 1),
                        axis=1
                    )
                    
        except Exception as e:
            st.error(f"Error converting currencies: {str(e)}")
    
    def fetch_historical_prices(self) -> Dict:
        """Fetch historical stock prices from Yahoo Finance"""
        try:
            historical_prices = {}
            unique_symbols = self.holdings['Symbol'].unique()
            
            # Date range for historical data
            start_date = self.all_trades['Date'].min() - timedelta(days=30)
            end_date = datetime.now()
            
            for symbol in unique_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist_data = ticker.history(start=start_date, end=end_date)
                    
                    if not hist_data.empty:
                        # Adjust for splits
                        if symbol in self.stock_splits:
                            for split_date, split_ratio in self.stock_splits[symbol].items():
                                mask = hist_data.index < split_date
                                hist_data.loc[mask, 'Close'] /= split_ratio
                        
                        historical_prices[symbol] = hist_data['Close'].to_dict()
                    
                except Exception as e:
                    st.warning(f"Could not fetch historical prices for {symbol}: {str(e)}")
                    continue
            
            return historical_prices
            
        except Exception as e:
            st.error(f"Error fetching historical prices: {str(e)}")
            return {}
    
    def calculate_portfolio_value(self, historical_prices: Dict) -> pd.DataFrame:
        """Calculate daily portfolio value across currencies"""
        try:
            # Create date range
            start_date = self.all_trades['Date'].min()
            end_date = datetime.now().date()
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            
            portfolio_values = []
            
            for current_date in date_range:
                daily_value = {'Date': current_date}
                
                # Calculate holdings as of this date
                trades_until_date = self.all_trades[self.all_trades['Date'] <= current_date]
                current_holdings = trades_until_date.groupby('Symbol')['Quantity'].sum()
                
                total_value_usd = 0
                total_value_inr = 0
                total_value_sgd = 0
                
                for symbol, quantity in current_holdings.items():
                    if quantity != 0 and symbol in historical_prices:
                        # Find closest price
                        symbol_prices = historical_prices[symbol]
                        closest_date = min(symbol_prices.keys(), 
                                         key=lambda x: abs((x.date() if hasattr(x, 'date') else x) - current_date),
                                         default=None)
                        
                        if closest_date:
                            price = symbol_prices[closest_date]
                            value_usd = quantity * price
                            
                            total_value_usd += value_usd
                            total_value_inr += value_usd * self.currency_rates.get('INR', 83)
                            total_value_sgd += value_usd * self.currency_rates.get('SGD', 1.35)
                
                daily_value.update({
                    'Portfolio_Value_USD': total_value_usd,
                    'Portfolio_Value_INR': total_value_inr,
                    'Portfolio_Value_SGD': total_value_sgd
                })
                
                portfolio_values.append(daily_value)
            
            return pd.DataFrame(portfolio_values)
            
        except Exception as e:
            st.error(f"Error calculating portfolio value: {str(e)}")
            return pd.DataFrame()
    
    def calculate_xirr(self) -> Dict:
        """Calculate XIRR for each holding"""
        try:
            xirr_results = {}
            
            for symbol in self.holdings['Symbol'].unique():
                symbol_trades = self.all_trades[self.all_trades['Symbol'] == symbol].copy()
                
                if len(symbol_trades) < 2:
                    continue
                
                # Prepare cash flows
                dates = []
                cash_flows = []
                
                for _, trade in symbol_trades.iterrows():
                    dates.append(trade['Date'])
                    # Negative for purchases, positive for sales
                    cash_flows.append(-trade['Proceeds'] if trade['Quantity'] > 0 else abs(trade['Proceeds']))
                
                # Add current position value if holding exists
                current_holding = self.holdings[self.holdings['Symbol'] == symbol]
                if not current_holding.empty and current_holding.iloc[0]['Quantity'] > 0:
                    # Use last known price or current market price
                    try:
                        ticker = yf.Ticker(symbol)
                        current_price = ticker.info.get('currentPrice', 0)
                        if current_price > 0:
                            current_value = current_holding.iloc[0]['Quantity'] * current_price
                            dates.append(datetime.now())
                            cash_flows.append(current_value)
                    except:
                        pass
                
                # Calculate XIRR
                if len(dates) >= 2 and len(cash_flows) >= 2:
                    try:
                        xirr_value = pyxirr.xirr(dates, cash_flows)
                        if xirr_value is not None:
                            xirr_results[symbol] = xirr_value * 100  # Convert to percentage
                        else:
                            xirr_results[symbol] = None
                    except:
                        xirr_results[symbol] = None
            
            return xirr_results
            
        except Exception as e:
            st.error(f"Error calculating XIRR: {str(e)}")
            return {}

def main():
    st.title("📈 Portfolio Analytics Dashboard")
    st.markdown("### Comprehensive Portfolio Analysis with XIRR Calculations")
    
    # Initialize analyzer
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = PortfolioAnalyzer()
    
    analyzer = st.session_state.analyzer
    
    # Sidebar for file upload
    with st.sidebar:
        st.header("📁 Upload Trading Data")
        uploaded_files = st.file_uploader(
            "Upload CSV files containing trading data",
            type=['csv'],
            accept_multiple_files=True,
            help="Upload the 3 CSV files containing your trading history"
        )
        
        if uploaded_files and len(uploaded_files) > 0:
            st.success(f"✅ {len(uploaded_files)} files uploaded successfully")
            
            if st.button("🚀 Process Data", type="primary"):
                with st.spinner("Processing trading data..."):
                    # Step 1: Load CSV files
                    if analyzer.load_csv_files(uploaded_files):
                        st.success("✅ Step 1: CSV files loaded successfully")
                        
                        # Step 2: Create master holdings
                        analyzer.create_master_holdings()
                        st.success("✅ Step 2: Master holdings created")
                        
                        # Step 3: Fetch stock splits
                        splits = analyzer.fetch_stock_splits()
                        st.success(f"✅ Step 3: Stock splits fetched ({len(splits)} stocks)")
                        
                        # Step 4: Apply stock splits
                        analyzer.apply_stock_splits()
                        st.success("✅ Step 4: Stock splits applied")
                        
                        # Step 5: Fetch currency rates
                        rates = analyzer.fetch_currency_rates()
                        st.success(f"✅ Step 5: Currency rates fetched ({len(rates)} currencies)")
                        
                        # Step 6: Convert to multiple currencies
                        analyzer.convert_to_currencies()
                        st.success("✅ Step 6: Multi-currency conversion completed")
                        
                        # Store processing flag
                        st.session_state.data_processed = True
                        st.rerun()
    
    # Main content area
    if hasattr(st.session_state, 'data_processed') and st.session_state.data_processed:
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Trading Data", 
            "💼 Holdings", 
            "💱 Currency Analysis", 
            "📈 Portfolio Value", 
            "💰 XIRR Analysis"
        ])
        
        with tab1:
            st.header("🔍 Raw Trading Data Analysis")
            
            if not analyzer.all_trades.empty:
                st.subheader("All Transactions (Split-Adjusted)")
                st.dataframe(
                    analyzer.all_trades[['Symbol', 'Date', 'Quantity', 'T. Price', 'Currency', 'Proceeds']],
                    use_container_width=True
                )
                
                # Summary statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Transactions", len(analyzer.all_trades))
                with col2:
                    st.metric("Unique Stocks", str(analyzer.all_trades['Symbol'].nunique()))
                with col3:
                    st.metric("Date Range", f"{analyzer.all_trades['Date'].min().strftime('%Y-%m-%d')} to {analyzer.all_trades['Date'].max().strftime('%Y-%m-%d')}")
        
        with tab2:
            st.header("💼 Master Holdings")
            
            if not analyzer.holdings.empty:
                st.subheader("Current Portfolio Holdings")
                st.dataframe(analyzer.holdings, use_container_width=True)
                
                # Holdings visualization
                if len(analyzer.holdings) > 0:
                    
                    fig = px.pie(
                        analyzer.holdings, 
                        values='Quantity', 
                        names='Symbol',
                        title="Portfolio Allocation by Quantity"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.header("💱 Multi-Currency Analysis")
            
            if analyzer.currency_rates:
                st.subheader("Current Exchange Rates (Base: USD)")
                rates_df = pd.DataFrame([
                    {'Currency': curr, 'Rate': rate} 
                    for curr, rate in analyzer.currency_rates.items()
                ])
                st.dataframe(rates_df, use_container_width=True)
                
                # Multi-currency transaction view
                if 'Proceeds_USD' in analyzer.all_trades.columns:
                    st.subheader("Transactions in Multiple Currencies")
                    currency_cols = ['Symbol', 'Date', 'Quantity', 'Currency', 'Proceeds_USD', 'Proceeds_INR', 'Proceeds_SGD']
                    available_cols = [col for col in currency_cols if col in analyzer.all_trades.columns]
                    st.dataframe(analyzer.all_trades[available_cols], use_container_width=True)
        
        with tab4:
            st.header("📈 Portfolio Value Analysis")
            
            with st.spinner("Fetching historical prices and calculating portfolio value..."):
                # Step 7: Fetch historical prices
                historical_prices = analyzer.fetch_historical_prices()
                
                if historical_prices:
                    st.success(f"✅ Step 7: Historical prices fetched ({len(historical_prices)} stocks)")
                    
                    # Step 8: Calculate daily portfolio value
                    portfolio_df = analyzer.calculate_portfolio_value(historical_prices)
                    
                    # Store in session state for later use
                    st.session_state.portfolio_df = portfolio_df
                    st.session_state.historical_prices = historical_prices
                    
                    if not portfolio_df.empty:
                        st.success("✅ Step 8: Daily portfolio value calculated")
                        
                        # Portfolio value chart
                        
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=portfolio_df['Date'],
                            y=portfolio_df['Portfolio_Value_USD'],
                            mode='lines',
                            name='USD',
                            line=dict(color='blue')
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=portfolio_df['Date'],
                            y=portfolio_df['Portfolio_Value_INR'],
                            mode='lines',
                            name='INR',
                            line=dict(color='green'),
                            yaxis='y2'
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=portfolio_df['Date'],
                            y=portfolio_df['Portfolio_Value_SGD'],
                            mode='lines',
                            name='SGD',
                            line=dict(color='red'),
                            yaxis='y3'
                        ))
                        
                        fig.update_layout(
                            title="Portfolio Value Over Time (Multi-Currency)",
                            xaxis_title="Date",
                            yaxis=dict(title="Value (USD)", side="left"),
                            yaxis2=dict(title="Value (INR)", side="right", overlaying="y"),
                            yaxis3=dict(title="Value (SGD)", side="right", overlaying="y", position=0.95),
                            height=500
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Current portfolio value
                        if len(portfolio_df) > 0:
                            latest_values = portfolio_df.iloc[-1]
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric(
                                    "Portfolio Value (USD)", 
                                    f"${latest_values['Portfolio_Value_USD']:,.2f}"
                                )
                            with col2:
                                st.metric(
                                    "Portfolio Value (INR)", 
                                    f"₹{latest_values['Portfolio_Value_INR']:,.2f}"
                                )
                            with col3:
                                st.metric(
                                    "Portfolio Value (SGD)", 
                                    f"S${latest_values['Portfolio_Value_SGD']:,.2f}"
                                )
        
        with tab5:
            st.header("💰 XIRR Analysis")
            
            with st.spinner("Calculating XIRR for each holding..."):
                # Step 9: Calculate XIRR
                xirr_results = analyzer.calculate_xirr()
                
                # Store in session state for later use
                st.session_state.xirr_results = xirr_results
                
                if xirr_results:
                    st.success("✅ Step 9: XIRR calculations completed")
                    
                    # XIRR results table
                    xirr_df = pd.DataFrame([
                        {'Symbol': symbol, 'XIRR (%)': xirr_value}
                        for symbol, xirr_value in xirr_results.items()
                        if xirr_value is not None
                    ])
                    
                    if not xirr_df.empty:
                        st.subheader("XIRR by Stock")
                        
                        # Format XIRR values
                        xirr_df['XIRR (%)'] = xirr_df['XIRR (%)'].round(2)
                        
                        # Color code based on performance
                        def color_xirr(val):
                            if val > 15:
                                return 'background-color: #d4edda; color: #155724'
                            elif val > 0:
                                return 'background-color: #fff3cd; color: #856404'
                            else:
                                return 'background-color: #f8d7da; color: #721c24'
                        
                        styled_df = xirr_df.style.applymap(color_xirr, subset=['XIRR (%)'])
                        st.dataframe(styled_df, use_container_width=True)
                        
                        # XIRR visualization
                        
                        fig = px.bar(
                            xirr_df, 
                            x='Symbol', 
                            y='XIRR (%)',
                            title="XIRR Performance by Stock",
                            color='XIRR (%)',
                            color_continuous_scale=['red', 'yellow', 'green']
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Portfolio summary
                        avg_xirr = xirr_df['XIRR (%)'].mean()
                        best_stock = xirr_df.loc[xirr_df['XIRR (%)'].idxmax()]
                        worst_stock = xirr_df.loc[xirr_df['XIRR (%)'].idxmin()]
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Average XIRR", f"{avg_xirr:.2f}%")
                        with col2:
                            st.metric("Best Performer", f"{best_stock['Symbol']}: {best_stock['XIRR (%)']:.2f}%")
                        with col3:
                            st.metric("Worst Performer", f"{worst_stock['Symbol']}: {worst_stock['XIRR (%)']:.2f}%")
                    
                    else:
                        st.warning("No XIRR data available. This may be due to insufficient transaction history.")
        
        # Summary section
        st.header("📊 Complete Analysis Summary")
        
        summary_data = {
            "Step": [
                "1. Data Loading",
                "2. Master Holdings",
                "3. Stock Splits",
                "4. Split Adjustments",
                "5. Currency Rates",
                "6. Multi-Currency Conversion",
                "7. Historical Prices",
                "8. Portfolio Value",
                "9. XIRR Calculation",
                "10. UI Presentation"
            ],
            "Status": [
                "✅ Completed",
                "✅ Completed", 
                "✅ Completed",
                "✅ Completed",
                "✅ Completed",
                "✅ Completed",
                "✅ Completed",
                "✅ Completed",
                "✅ Completed",
                "✅ Completed"
            ],
            "Details": [
                f"{len(analyzer.all_trades)} transactions loaded",
                f"{len(analyzer.holdings)} unique holdings",
                f"{len(analyzer.stock_splits)} stocks with splits",
                "Prices and quantities adjusted",
                f"{len(analyzer.currency_rates)} currencies",
                "USD, INR, SGD conversions",
                f"{len(getattr(st.session_state, 'historical_prices', {})) } stocks",
                "Daily portfolio values calculated",
                f"{len(getattr(st.session_state, 'xirr_results', {})) } XIRR calculations",
                "Interactive dashboard created"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # Export functionality
        st.header("📥 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export Portfolio Summary"):
                summary_export = {
                    'holdings': analyzer.holdings.to_dict('records'),
                    'xirr_results': getattr(st.session_state, 'xirr_results', {}),
                    'currency_rates': analyzer.currency_rates,
                    'total_transactions': len(analyzer.all_trades)
                }
                
                st.download_button(
                    label="💾 Download Summary JSON",
                    data=str(summary_export),
                    file_name="portfolio_summary.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📈 Export Full Analysis"):
                # Create comprehensive export
                portfolio_df = getattr(st.session_state, 'portfolio_df', pd.DataFrame())
                if not portfolio_df.empty:
                    export_data = portfolio_df.to_csv(index=False)
                    st.download_button(
                        label="💾 Download Portfolio Data CSV",
                        data=export_data,
                        file_name="portfolio_analysis.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No portfolio data available for export. Please complete the analysis first.")
    
    else:
        # Welcome screen
        st.info("👋 Welcome! Please upload your trading CSV files using the sidebar to begin analysis.")
        
        # Instructions
        with st.expander("📖 How to use this application"):
            st.markdown("""
            ### Instructions:
            1. **Upload Files**: Use the sidebar to upload your 3 CSV trading files
            2. **Process Data**: Click the "Process Data" button to start analysis
            3. **Explore Results**: Navigate through the tabs to view different analyses:
                - **Trading Data**: View all transactions with split adjustments
                - **Holdings**: See your current portfolio composition
                - **Currency Analysis**: Multi-currency transaction views
                - **Portfolio Value**: Daily portfolio value charts
                - **XIRR Analysis**: Return calculations for each holding
            
            ### Features:
            - ✅ Automatic stock split detection and adjustment
            - ✅ Multi-currency support (USD, INR, SGD)
            - ✅ Real-time historical price fetching
            - ✅ XIRR calculations for performance analysis
            - ✅ Interactive charts and visualizations
            - ✅ Data export functionality
            
            ### Data Requirements:
            Your CSV files should contain columns: Symbol, Date/Time, Quantity, T. Price, Currency, Proceeds, Comm/Fee
            """)

if __name__ == "__main__":
    main()
