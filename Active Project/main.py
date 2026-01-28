# ===============================
# Automated Portfolio Report
# ===============================

import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# ===============================
# CONFIGURATION
# ===============================

# Portfolio Configuration
TICKERS = ["AAPL", "MSFT", "SPY"] # List of tickers in the portfolio
WEIGHTS = {"AAPL": 0.4, "MSFT": 0.4, "SPY": 0.2} # Weights for each ticker
LOOKBACK_DAYS = 365 * 3 # 3 years lookback period
TRADING_DAYS = 252 # Typical number of trading days in a year

# Path Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Base directory of the project
REPORT_DIR = os.path.join(BASE_DIR, "reports") # Directory to save reports
os.makedirs(REPORT_DIR, exist_ok=True) # Create reports directory if it doesn't exist

# Email Configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com") # SMTP server address
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587)) # SMTP server port
EMAIL_USER = os.environ.get("EMAIL_USER") 
EMAIL_PASS = os.environ.get("EMAIL_PASS")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

# ===============================
# DATA FETCHING
# ===============================

# Create a function to fetch historical price data
def fetch_prices(tickers, start, end):
    data = {} # Initialize empty dictionary to store historical price data
    for t in tickers: 
        df = yf.download( 
            t,
            start=start.strftime("%Y-%m-%d"), 
            end=end.strftime("%Y-%m-%d"), 
            progress=False, # Disable progress bar
            auto_adjust=True, # Adjusts data for dividends and stock splits
        )
        if not df.empty: # Check if data is returned
            data[t] = df # Store DataFrame in dictionary
    return data 

# ===============================
# VALIDATION & PROCESSING
# ===============================

# Create a function to validate and align price data
def validate_and_align(prices_dict):
    close_dict = {} # Initialize dictionary to store 'Close' prices
    for ticker, df in prices_dict.items(): 
        if isinstance(df.columns, pd.MultiIndex): # Check for MultiIndex columns
            close_dict[ticker] = df.xs("Close", level=0, axis=1)[ticker] # Extract 'Close' prices
        else: # Single level columns
            close_dict[ticker] = df["Close"] 
    close_df = pd.DataFrame(close_dict) # Combine into a single DataFrame
    close_df = close_df.dropna(how="all") # Drop rows where all values are NaN
    close_df = close_df.ffill().bfill() # Forward-fill and back-fill missing values
    return close_df

# ===============================
# METRICS
# ===============================

# Create a function to compute Annualized return
def annualized_return(series): 
  cumulative = (1 + series).prod() # Calculate cumulative return
  n = len(series) / TRADING_DAYS # Number of years
  return cumulative ** (1/n) - 1 # Annualized return formula

# Create a function to compute Annualized volatility
def annualized_vol(series):
  return series.std() * np.sqrt(TRADING_DAYS) # Annualized volatility formula

# Create a function to compute Sharpe Ratio
def sharpe_ratio(series, risk_free = 0.0):
  ar = annualized_return(series) # Annualized return
  avol = annualized_vol(series) # Annualized volatility
  if avol == 0: # Avoid division by zero
    return np.nan # Return NaN if volatility is zero
  return (ar - risk_free) / avol # Sharpe ratio formula

# Create a function to compute Maximum Drawdown
def max_drawdown(series):
  cum = (1 + series).cumprod() # Cumulative returns
  running_max = cum.cummax() # Running maximum
  drawdown = (cum - running_max)/running_max # Drawdown calculation
  return drawdown.min() # Return maximum drawdown

# Create a function to compute Historical Value at Risk (VaR)
def var_historic(series, level = 0.95):
  return -np.percentile(series.dropna(), (1 - level)* 100) # Historical VaR calculation

# Create a function to compute Sortino Ratio
def sortino_ratio(series, risk_free = 0.0):
  neg_rets = series[series < 0] # Filter negative returns
  downside_std = neg_rets.std() * np.sqrt(TRADING_DAYS) # Downside deviation
  ar = annualized_return(series) # Annualized return
  if downside_std == 0: # Avoid division by zero
    return np.nan # Return NaN if downside deviation is zero
  return (ar - risk_free) / downside_std # Sortino ratio formula

# ===============================
# CHARTS
# ===============================