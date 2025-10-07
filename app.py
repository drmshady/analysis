import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt

def fetch_stock_data(symbol):
  """Fetches historical stock data and fundamental information using yfinance."""
  try:
    stock = yf.Ticker(symbol)
    historical_data = stock.history(period="1y")
    fundamental_info = stock.info
    return historical_data, fundamental_info
  except Exception as e:
    st.error(f"Error fetching data for {symbol}: {e}")
    return None, None

def perform_technical_analysis(df):
  """Calculates technical indicators and adds them to the DataFrame."""
  if df is None or df.empty:
    return None

  # Calculate SMA
  df.ta.sma(length=20, append=True)
  df.ta.sma(length=50, append=True) # Add 50-day SMA

  # Calculate RSI
  df.ta.rsi(length=14, append=True)

  # Calculate MACD
  df.ta.macd(append=True)

  # Add Bollinger Bands
  df.ta.bbands(append=True)

  # Add Average True Range
  df.ta.atr(length=14, append=True) # Explicitly set ATR length

  return df

def perform_fundamental_analysis(fundamental_info):
    """Extracts key fundamental data points from the fundamental information dictionary."""
    fundamental_data = {}
    if fundamental_info:
        # Define a dictionary of fundamental data points to extract
        fundamental_keys = {
            'P/E Ratio (Trailing)': 'trailingPE',
            'P/E Ratio (Forward)': 'forwardPE',
            'EPS (Trailing)': 'forwardPE', # Corrected key
            'EPS (Forward)': 'forwardEPS',
            'Market Cap': 'marketCap',
            'Dividend Yield': 'dividendYield',
            'Beta': 'beta'
        }
        for display_key, yf_key in fundamental_keys.items():
            value = fundamental_info.get(yf_key)
            if value is not None:
                fundamental_data[display_key] = value
            else:
                fundamental_data[display_key] = "N/A" # Handle missing fundamental data

    return fundamental_data

def calculate_stop_loss_take_profit(df):
  """
  Calculates potential stop-loss and take-profit points using ATR.

  Args:
    df: DataFrame with historical stock data including ATR.

  Returns:
    A tuple containing stop-loss and take-profit values, or (None, None) if data is insufficient.
  """
  if df is None or df.empty or 'ATR_14' not in df.columns:
    return None, None

  last_close = df['Close'].iloc[-1]
  atr = df['ATR_14'].iloc[-1]

  # Simple ATR-based stop loss and take profit (can be further refined)
  stop_loss = last_close - (2 * atr) # Example: 2 times ATR below close
  take_profit = last_close + (3 * atr) # Example: 3 times ATR above close

  return stop_loss, take_profit


st.title("Stock Analysis Application")

stock_symbol = st.text_input("Enter Stock Symbol:", "")

analyze_button = st.button("Analyze Stock")

results_placeholder = st.empty()

if analyze_button and stock_symbol:
    historical_data, fundamental_info = fetch_stock_data(stock_symbol)

    if historical_data is not None and fundamental_info is not None and not historical_data.empty:
        technical_analysis_results = perform_technical_analysis(historical_data.copy()) # Use a copy to avoid modifying the original
        fundamental_analysis_results = perform_fundamental_analysis(fundamental_info)
        stop_loss, take_profit = calculate_stop_loss_take_profit(technical_analysis_results) # Use the dataframe with technical indicators


        with results_placeholder.container():
            st.subheader(f"Analysis for {stock_symbol.upper()}")

            # Plot historical data with indicators
            if technical_analysis_results is not None and not technical_analysis_results.empty:
                st.subheader("Historical Data and Indicators")
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(technical_analysis_results.index, technical_analysis_results['Close'], label='Close Price')

                # Plot SMAs
                if 'SMA_20' in technical_analysis_results.columns:
                    ax.plot(technical_analysis_results.index, technical_analysis_results['SMA_20'], label='SMA (20)', color='orange')
                if 'SMA_50' in technical_analysis_results.columns:
                    ax.plot(technical_analysis_results.index, technical_analysis_results['SMA_50'], label='SMA (50)', color='purple')


                # Plot Bollinger Bands
                if 'BBL_5,2.0' in technical_analysis_results.columns and 'BBM_5,2.0' in technical_analysis_results.columns and 'BBU_5,2.0' in technical_analysis_results.columns:
                     ax.plot(technical_analysis_results.index, technical_analysis_results['BBL_5,2.0'], label='Bollinger Lower', color='red', linestyle='--')
                     ax.plot(technical_analysis_results.index, technical_analysis_results['BBM_5,2.0'], label='Bollinger Middle', color='grey', linestyle='--')
                     ax.plot(technical_analysis_results.index, technical_analysis_results['BBU_5,2.0'], label='Bollinger Upper', color='green', linestyle='--')


                ax.set_title(f"{stock_symbol.upper()} Historical Data with Indicators")
                ax.set_xlabel("Date")
                ax.set_ylabel("Price")
                ax.legend()
                st.pyplot(fig)

                # Display RSI and MACD in separate plots or text
                st.subheader("Momentum Indicators")
                if 'RSI_14' in technical_analysis_results.columns:
                    st.write(f"**RSI (14):** {technical_analysis_results['RSI_14'].iloc[-1]:.2f}")
                    fig_rsi, ax_rsi = plt.subplots(figsize=(12, 3))
                    ax_rsi.plot(technical_analysis_results.index, technical_analysis_results['RSI_14'], label='RSI (14)', color='blue')
                    ax_rsi.axhline(70, color='red', linestyle='--', alpha=0.5)
                    ax_rsi.axhline(30, color='green', linestyle='--', alpha=0.5)
                    ax_rsi.set_title(f"{stock_symbol.upper()} RSI (14)")
                    ax_rsi.set_xlabel("Date")
                    ax_rsi.set_ylabel("RSI")
                    st.pyplot(fig_rsi)


                if 'MACDh_12_26_9' in technical_analysis_results.columns: # MACD Histogram
                    st.write(f"**MACD Histogram:** {technical_analysis_results['MACDh_12_26_9'].iloc[-1]:.2f}")
                    fig_macd, ax_macd = plt.subplots(figsize=(12, 3))
                    ax_macd.bar(technical_analysis_results.index, technical_analysis_results['MACDh_12_26_9'], label='MACD Histogram', color='grey')
                    ax_macd.plot(technical_analysis_results.index, technical_analysis_results['MACD_12_26_9'], label='MACD Line', color='blue')
                    ax_macd.plot(technical_analysis_results.index, technical_analysis_results['MACDs_12_26_9'], label='Signal Line', color='red')
                    ax_macd.set_title(f"{stock_symbol.upper()} MACD")
                    ax_macd.set_xlabel("Date")
                    ax_macd.set_ylabel("Value")
                    ax_macd.legend()
                    st.pyplot(fig_macd)



            st.subheader("Technical Analysis Results (Last 10 rows)")
            if technical_analysis_results is not None and not technical_analysis_results.empty:
                st.dataframe(technical_analysis_results.tail(10))
            else:
                st.warning("Could not perform technical analysis.")


            st.subheader("Fundamental Analysis")
            if fundamental_analysis_results:
                 for key, value in fundamental_analysis_results.items():
                     st.write(f"**{key}:** {value}")
            else:
                st.warning("Could not perform fundamental analysis.")


            st.subheader("Stop-Loss and Take-Profit")
            if stop_loss is not None and take_profit is not None:
                st.write(f"**Calculated based on ATR (14):**")
                st.write(f"**Stop-Loss:** {stop_loss:.2f}")
                st.write(f"**Take-Profit:** {take_profit:.2f}")
            else:
                st.warning("Could not calculate stop-loss and take-profit based on ATR. Data might be insufficient.")


    elif historical_data is not None and historical_data.empty:
         results_placeholder.warning(f"No historical data found for {stock_symbol.upper()}.")
    elif fundamental_info is not None and not fundamental_info:
         results_placeholder.warning(f"No fundamental data found for {stock_symbol.upper()}.")
    else:
        results_placeholder.error(f"Could not fetch data for the provided stock symbol: {stock_symbol.upper()}. Please check the symbol and try again.")
elif analyze_button and not stock_symbol:
    results_placeholder.warning("Please enter a stock symbol.")
