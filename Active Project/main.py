# ===============================
# Automated Portfolio Report
# ===============================

import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image, Table, TableStyle
from PIL import Image as PILImage

from send_email import send_email_smtp

# ===============================
# PART 1: CONFIGURATION
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

# 1. Price Chart
def save_price_chart(close_prices, out_path): 
  plt.figure(figsize=(11,6)) # Set figure size
  for col in close_prices.columns:
      plt.plot(close_prices.index, close_prices[col], label=col, linewidth=2) # Plot each asset's price
  plt.title("Asset Performance Comparison", fontsize=25, pad=20) # Chart title
  plt.ylabel("Indexed Price") # Y-axis label
  plt.xlabel("Date") # X-axis label
  ax = plt.gca() # Get current axis
  for spine in ax.spines.values(): 
      spine.set_visible(False) # Hide chart spines
  ax.tick_params(left=False, bottom=False) # Remove tick marks
  plt.grid(True, axis='y', linestyle='--', alpha=0.4) # Add horizontal grid lines
  plt.legend(frameon=False, loc='upper left', bbox_to_anchor=(1, 1)) # Legend outside plot
  plt.tight_layout() # Adjust layout
  plt.savefig(out_path) # Save chart to file
  plt.close() # Close the plot to free memory

# 2. Portfolio Cumulative Returns
def save_cum_returns_chart(port_rets, out_path):
  cum = (1 + port_rets).cumprod() - 1 # Calculate cumulative returns
  plt.figure(figsize=(11,6)) # Set figure size
  plt.plot(cum.index, cum * 100, color='#008080') # Plot cumulative returns
  plt.title("Portfolio Cumulative Return Over Time", fontsize=25, pad=20) # Chart title
  plt.ylabel("Cumulative Return (%)") # Y-axis label
  plt.xlabel("Date") # X-axis label
  ax = plt.gca() # Get current axis
  for spine in ax.spines.values():
      spine.set_visible(False) # Hide chart spines
  ax.tick_params(left=False, bottom=False) # Remove tick marks
  plt.grid(True, axis='y', linestyle='--', alpha=0.4) # Add horizontal grid lines
  final_return = cum.iloc[-1] * 100 # Final cumulative return
  plt.annotate( 
      f"Final Return: {final_return:.1f}%",
      xy=(cum.index[-1], final_return),
      xytext=(-20, 30),
      textcoords="offset points",
      arrowprops=dict(arrowstyle="->", alpha=0.5),
      fontsize=10
  ) # Annotate final return
  plt.tight_layout() # Adjust layout
  plt.savefig(out_path) # Save chart to file
  plt.close() # Close the plot to free memory

# 3. Portfolio Drawdown
def save_drawdown_chart(port_rets, out_path):
  cum = (1 + port_rets).cumprod() # Calculate cumulative returns
  running_max = cum.cummax() # Calculate running maximum
  drawdown = (cum - running_max) / running_max # Calculate drawdown
  max_dd = drawdown.min() # Maximum drawdown
  max_dd_date = drawdown.idxmin() # Date of maximum drawdown

  plt.figure(figsize=(11,4)) # Set figure size
  plt.fill_between(drawdown.index, drawdown * 100, 0, alpha=0.15, color="#D0312D") # Fill area under drawdown curve
  plt.plot(drawdown.index, drawdown * 100, linewidth=1.5, color="#D0312D") # Plot drawdown line
  plt.annotate(
      f"Max Drawdown: {max_dd:.2%}" ,
      xy=(max_dd_date, max_dd * 100),
      xytext=(10, 20),
      textcoords="offset points",
      arrowprops=dict(arrowstyle="->"),
      fontsize=9,
  ) # Annotate maximum drawdown
  plt.title("Portfolio Drawdown Over Time", fontsize=25, pad=20) # Chart title
  plt.ylabel("Drawdown (%)") # Y-axis label
  plt.xlabel("Date") # X-axis label
  ax = plt.gca() # Get current axis
  for spine in ax.spines.values():
      spine.set_visible(False) # Hide chart spines
  ax.tick_params(left=False, bottom=False) # Remove tick marks
  plt.grid(True, axis='y', linestyle='--', alpha=0.4) # Add horizontal grid lines
  plt.tight_layout() # Adjust layout
  plt.savefig(out_path) # Save chart to file
  plt.close() # Close the plot to free memory

# 4. Returns Distribution + VaR
def save_returns_distribution(port_rets, var_95, var_99, out_path):
  mean_ret = port_rets.mean() # Calculate mean return

  plt.figure(figsize=(9,4)) # Set figure size
  plt.hist(port_rets, bins=50, density=True, alpha=0.65, color='#008080') # Plot histogram of returns
  plt.axvline(var_95, linestyle="--", linewidth=2, label=f"VaR 95% ({var_95:.2%})", color='#808080') # VaR 95% line
  plt.axvline(var_99, linestyle=":", linewidth=2, label=f"VaR 99% ({var_99:.2%})", color='#808080') # VaR 99% line
  plt.axvline(mean_ret, linestyle="-", linewidth=1.5, label=f"Mean ({mean_ret:.2%})", color='#808080') # Mean return line
  plt.xlabel("Daily Return") # X-axis label
  plt.ylabel("Probability Density") # Y-axis label
  ax = plt.gca() # Get current axis
  for spine in ax.spines.values():
      spine.set_visible(False) # Hide chart spines
  ax.tick_params(left=False, bottom=False) # Remove tick marks
  plt.grid(True, axis='y', linestyle='--', alpha=0.4) # Add horizontal grid lines
  plt.legend(frameon=False) # Add legend
  plt.tight_layout() # Adjust layout
  plt.savefig(out_path) # Save chart to file
  plt.close() # Close the plot to free memory

# 5. Rolling Volatility
def save_rolling_volatility(port_rets, out_path, window=30):
  rolling_vol = port_rets.rolling(window).std() * np.sqrt(252) # Calculate rolling volatility

  plt.figure(figsize=(11,4)) # Set figure size
  plt.plot(rolling_vol.index, rolling_vol * 100, linewidth=2, label="Rolling Volatility", color='#008080') # Plot rolling volatility
  plt.fill_between(rolling_vol.index, rolling_vol * 100, alpha=0.15, color='#008080') # Fill area under the curve
  plt.title("Portfolio Risk Over Time", fontsize=25, pad=20) # Chart title
  plt.ylabel("Volatility (%)") # Y-axis label
  plt.xlabel("Date") # X-axis label
  ax = plt.gca() # Get current axis
  for spine in ax.spines.values():
      spine.set_visible(False) # Hide chart spines
  ax.tick_params(left=False, bottom=False) # Remove tick marks
  ax.yaxis.set_major_formatter(mtick.PercentFormatter()) # Format y-axis as percentage
  plt.grid(True, axis='y', linestyle='--', alpha=0.4) # Add horizontal grid lines
  plt.tight_layout() # Adjust layout
  plt.savefig(out_path) # Save chart to file
  plt.close() # Close the plot to free memory

# 6. Correlation Heatmap
def save_correlation_heatmap(rets, out_path):
  corr = rets.corr() # Calculate correlation matrix

  plt.figure(figsize=(6,5)) # Set figure size
  sns.heatmap(
    corr,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    linewidths=0.5,
    cbar_kws={"label": "Correlation"}
  ) # Create heatmap
  plt.title("Asset Return Correlation Matrix", fontsize=14, pad=20) # Chart title
  plt.tight_layout() # Adjust layout
  plt.savefig(out_path) # Save chart to file
  plt.close() # Close the plot to free memory

# ===============================
# PDF GENERATION
# ===============================

# Function to scale images for PDF
def scaled_image(path, max_width=7.5*inch, max_height=7*inch):
  img = PILImage.open(path) # Open image using PIL
  w, h = img.size # Get original dimensions
  aspect = h / w # Calculate aspect ratio
  # Scale to fit max_width or max_height
  if w > h: # Landscape
    width = max_width # Set width to max_width
    height = width * aspect # Scale height accordingly
  else: # Portrait
    height = max_height # Set height to max_height
    width = height / aspect # Scale width accordingly
  return Image(path, width=width, height=height)

# Function to create PDF report
def create_pdf_report(report_path, metrics, asset_metrics, charts, config=None):
  doc = SimpleDocTemplate(
      report_path,
      pagesize=letter, 
      rightMargin=36,
      leftMargin=36,
      topMargin=36,
      bottomMargin=36
  ) # Initialize PDF document
  styles = getSampleStyleSheet() # Get default styles
  story = [] # Initialize story list

  # Title
  story.append(Paragraph("Automated Portfolio Performance & Risk Report", styles['Title'])) 
  story.append(Spacer(1, 14)) # Add space after title
  story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (GMT)", styles['Normal'])) # Add date
  story.append(Spacer(1, 30)) # Add space after date

  # Portfolio metrics table
  data = [["Metric", "Value"]] # Table header
  def fmt(x): 
    return f"{x:.4f}" if isinstance(x, float) else str(x) # Format float to 4 decimal places
  for k, v in metrics.items():
      data.append([k, fmt(v)]) # Add metric rows
  tbl = Table(data, colWidths=[200, 200]) # Create table
  tbl.setStyle(TableStyle([
      ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), # Header background
      ('GRID', (0,0), (-1,-1), 0.5, colors.grey), # Grid lines
  ])) # Set table style
  story.append(tbl) # Add table to story
  story.append(Spacer(1, 30)) # Add space after table

  # Asset metrics table
  data2 = [["Asset", "Annualized Return", "Annualized Vol", "Sharpe", "Max Drawdown"]] # Table header
  for asset, m in asset_metrics.items(): 
      data2.append([
          asset,
          f"{m['annual_return']:.4f}",
          f"{m['annual_vol']:.4f}",
          f"{m['sharpe']:.4f}",
          f"{m['max_drawdown']:.4f}"
      ]) # Add asset metric rows
  tbl2 = Table(data2, colWidths=[120, 100, 100, 100, 100]) # Create table
  tbl2.setStyle(TableStyle([  
      ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), # Header background
      ('GRID', (0,0), (-1,-1), 0.5, colors.grey), # Grid lines
  ])) # Set table style
  story.append(tbl2) # Add table to story
  story.append(Spacer(1, 30)) # Add space after table

  # Charts
  for chart_path in charts: 
      if os.path.exists(chart_path): # Check if chart file exists
          story.append(scaled_image(chart_path)) # Add scaled image to story
          story.append(Spacer(1, 65)) # Add space after image

  # Build PDF
  doc.build(story) # Generate the PDF document



# ===============================
# MAIN PIPELINE
# ===============================

# Main function to run the pipeline
def main():
    end = datetime.now() # Current date
    start = end - timedelta(days=LOOKBACK_DAYS) # Start date based on lookback period

    prices = fetch_prices(TICKERS, start, end) # Fetch historical price data
    close_prices = validate_and_align(prices) # Validate and align price data
    rets = close_prices.pct_change().dropna() # Calculate daily returns

    weights = np.array([WEIGHTS[t] for t in rets.columns]) # Get weights array
    port_rets = rets.dot(weights) # Calculate portfolio returns

    # Compute metrics
    metrics = {
        "Annual Return": annualized_return(port_rets),
        "Annual Volatility": annualized_vol(port_rets),
        "Sharpe Ratio": sharpe_ratio(port_rets),
        "Sortino Ratio": sortino_ratio(port_rets),
        "Max Drawdown": max_drawdown(port_rets),
        "VaR 95%": var_historic(port_rets, 0.95),
        "VaR 99%": var_historic(port_rets, 0.99),
    }

    # Compute asset-level metrics
    asset_metrics = {}
    for t in rets.columns:
      s = rets[t]
      asset_metrics[t] = {
      "annual_return": annualized_return(s),
      "annual_vol": annualized_vol(s),
      "sharpe": sharpe_ratio(s),
      "max_drawdown": max_drawdown(s),
    }

    # Generate and save charts
    charts = [
        os.path.join(REPORT_DIR, "price.png"),
        os.path.join(REPORT_DIR, "cum.png"),
        os.path.join(REPORT_DIR, "dd.png"),
        os.path.join(REPORT_DIR, "dist.png"),
        os.path.join(REPORT_DIR, "vol.png"),
        os.path.join(REPORT_DIR, "corr.png"),
    ]

    # Save charts
    save_price_chart(close_prices, charts[0])
    save_cum_returns_chart(port_rets, charts[1])
    save_drawdown_chart(port_rets, charts[2])
    save_returns_distribution(port_rets, metrics["VaR 95%"], metrics["VaR 99%"], charts[3])
    save_rolling_volatility(port_rets, charts[4])
    save_correlation_heatmap(rets, charts[5])

    # Create PDF report
    report_path = os.path.join(REPORT_DIR, f"portfolio_report_{end.strftime('%Y%m%d')}.pdf")
    create_pdf_report(report_path, metrics, asset_metrics, charts)

    # Send email with PDF report
    send_email_smtp(
      smtp_user=EMAIL_USER,
      smtp_password=EMAIL_PASS,
      smtp_server=SMTP_SERVER,
      smtp_port=SMTP_PORT,
      receiver_email=RECEIVER_EMAIL,
      report_path=report_path,
    )

# ===============================
# Run main function    
# ===============================

if __name__ == "__main__":
    main()

# ===================================================================END OF THE FILE=================================================================