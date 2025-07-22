# Portfolio Analytics Dashboard

## Overview

This is a Streamlit-based portfolio analytics dashboard that processes financial trading data from CSV files and provides comprehensive portfolio analysis. The application uses Python for data processing and analysis, with Streamlit providing the web interface for user interaction and visualization.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web framework
- **UI Pattern**: Single-page application with sidebar navigation
- **Layout**: Wide layout with expandable sidebar for better data visualization
- **Responsive Design**: Streamlit's built-in responsive components

### Backend Architecture
- **Language**: Python
- **Architecture Pattern**: Object-oriented design with a main `PortfolioAnalyzer` class
- **Data Processing**: Pandas for data manipulation and NumPy for numerical computations
- **Financial Data**: Yahoo Finance (yfinance) integration for real-time market data

### Data Storage
- **Primary Storage**: In-memory pandas DataFrames
- **Input Format**: CSV file uploads (no persistent database)
- **Data Types**: Trading data, holdings data, currency rates, stock splits

## Key Components

### PortfolioAnalyzer Class
- **Purpose**: Core business logic for portfolio analysis
- **Responsibilities**: 
  - CSV file processing and data standardization
  - Portfolio calculations and metrics
  - Currency conversion handling
  - Stock split adjustments

### Data Processing Pipeline
- **CSV Upload Handler**: Processes multiple CSV files with trading data
- **Data Standardization**: Normalizes column names and date/time formats
- **Trade Filtering**: Separates order data from other transaction types
- **Data Validation**: Ensures data quality and consistency

### Financial Calculations
- **IRR Calculations**: Uses pyxirr library for internal rate of return calculations
- **Portfolio Metrics**: Performance analysis and risk calculations
- **Currency Support**: Multi-currency portfolio handling
- **Market Data Integration**: Real-time price feeds via Yahoo Finance

## Data Flow

1. **Data Input**: Users upload CSV files containing trading data
2. **Data Processing**: Files are parsed, cleaned, and standardized
3. **Trade Extraction**: Order data is filtered and processed
4. **Portfolio Calculation**: Holdings and performance metrics are computed
5. **Visualization**: Results are displayed through Streamlit interface
6. **Real-time Updates**: Market data is fetched for current valuations

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **yfinance**: Yahoo Finance API for market data
- **pyxirr**: Internal Rate of Return calculations
- **requests**: HTTP client for API calls

### Data Sources
- **Yahoo Finance**: Real-time stock prices and market data
- **User CSV Files**: Historical trading data input

## Deployment Strategy

### Local Development
- **Runtime**: Python application server via Streamlit
- **Port**: Default Streamlit port (8501)
- **Dependencies**: Requirements managed via pip

### Production Considerations
- **Platform**: Designed for Streamlit Cloud or similar Python hosting
- **Scalability**: Single-user sessions with in-memory data processing
- **Performance**: Optimized for CSV file sizes typical of individual portfolios

### Configuration
- **Page Setup**: Wide layout with custom title and icon
- **Error Handling**: Graceful handling of missing dependencies
- **Warnings**: Suppressed for cleaner user experience

## Technical Decisions

### Framework Choice: Streamlit
- **Problem**: Need for rapid development of interactive financial dashboard
- **Solution**: Streamlit for its simplicity and built-in data visualization
- **Pros**: Fast development, automatic UI generation, great for data apps
- **Cons**: Limited customization compared to full web frameworks

### Data Storage: In-Memory Processing
- **Problem**: Need to process uploaded financial data
- **Solution**: Pandas DataFrames for in-memory processing
- **Pros**: Fast processing, no database setup required, stateless sessions
- **Cons**: No data persistence, limited to single-user sessions

### Financial Data Integration: Yahoo Finance
- **Problem**: Need real-time market data for portfolio valuation
- **Solution**: yfinance library for easy access to Yahoo Finance data
- **Pros**: Free, reliable, comprehensive market data
- **Cons**: Rate limiting, dependency on external service