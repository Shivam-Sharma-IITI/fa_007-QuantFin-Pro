import pandas as pd
import numpy as np
import plotly.graph_objs as go
from statsmodels.tsa.arima.model import ARIMA
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
import warnings
import sqlite3

warnings.filterwarnings("ignore")

# Native currency mapping for stocks. Used for currency conversion.
STOCK_CURRENCY = {
    'AAPL': 'USD', 'MSFT': 'USD', 'GOOGL': 'USD', 'TSLA': 'USD',
    'RELIANCE.NS': 'INR', 'TCS.NS': 'INR', 'INFY.NS': 'INR', 'HDFCBANK.NS': 'INR'
}

def load_data_from_db(db_path, symbol):
    """Loads historical stock data from the SQLite database for a given symbol."""
    with sqlite3.connect(db_path) as conn:
        # Assumes the ETL pipeline stores data in a 'market_data' table
        query = f"SELECT date, open, high, low, close FROM market_data WHERE symbol = ? ORDER BY date"
        df = pd.read_sql_query(query, conn, params=(symbol,), index_col='date', parse_dates=['date'])
    
    if df.empty:
        raise ValueError(f"No data found for symbol '{symbol}' in the database at {db_path}.")
    return df

def get_fx_rate_from_db(db_path, from_currency, to_currency):
    """Fetches the latest FX rate from the database."""
    if from_currency == to_currency:
        return 1.0
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Assumes the ETL pipeline stores FX rates in an 'fx_rates' table
            query = "SELECT rate FROM fx_rates WHERE from_currency = ? AND to_currency = ? ORDER BY date DESC LIMIT 1"
            cursor = conn.cursor()
            
            # Try direct conversion (e.g., INR to USD)
            cursor.execute(query, (from_currency, to_currency))
            result = cursor.fetchone()
            if result:
                return result[0]

            # If not found, try inverse conversion (e.g., USD to INR)
            cursor.execute(query, (to_currency, from_currency))
            inverse_result = cursor.fetchone()
            if inverse_result:
                return 1 / inverse_result[0]
            
            raise ValueError(f"FX rate for {from_currency}->{to_currency} not found in database.")
    except sqlite3.Error as e:
        # Catches DB errors like "no such table: fx_rates"
        raise ValueError(f"DB error fetching FX rate: {e}. Ensure 'fx_rates' table exists and is populated.")

def add_technical_indicators(df):
    df = df.copy()
    df['sma_14'] = SMAIndicator(df['close'], window=14).sma_indicator()
    df['rsi_14'] = RSIIndicator(df['close'], window=14).rsi()
    df.fillna(method="bfill", inplace=True)
    return df

def arima_forecast(df, periods, order=(5,1,0)):
    model = ARIMA(df['close'], order=order)
    model_fit = model.fit()
    return model_fit.forecast(steps=periods)

def backtest_arima(df, test_size=30, order=(5,1,0)):
    if len(df) <= test_size:
        print(f"Warning: Not enough data for backtesting (data size: {len(df)}, test size: {test_size}). Skipping.")
        return
    train = df['close'][:-test_size]
    test = df['close'][-test_size:]
    model = ARIMA(train, order=order)
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=test_size)
    mape = np.mean(np.abs((test.values - forecast.values) / test.values)) * 100
    rmse = np.sqrt(np.mean((test.values - forecast.values) ** 2))
    print(f"Backtest Accuracy (last {test_size} days) -> MAPE: {mape:.2f}%, RMSE: {rmse:.2f}")

def generate_ohlc_from_close(forecast):
    ohlc_data = []
    for i, close_price in enumerate(forecast):
        open_price = forecast.iloc[i-1] if i > 0 else close_price * (1 - 0.01)
        high = max(open_price, close_price) * (1 + np.random.uniform(0.001, 0.01))
        low = min(open_price, close_price) * (1 - np.random.uniform(0.001, 0.01))
        ohlc_data.append({'open': open_price, 'high': high, 'low': low, 'close': close_price})
    return pd.DataFrame(ohlc_data)

def create_forecast_plot(ohlc_forecast, symbol, days, currency):
    """Generates an interactive Plotly candlestick chart for the forecast."""
    fig = go.Figure(data=[go.Candlestick(
        x=ohlc_forecast.index, open=ohlc_forecast['open'], high=ohlc_forecast['high'],
        low=ohlc_forecast['low'], close=ohlc_forecast['close'],
        increasing_line_color='limegreen', decreasing_line_color='crimson',
        name='Forecast'
    )])
    fig.update_layout(
        title=f"{symbol} Stock Price Forecast ({days} Days) in {currency}",
        xaxis_title='Date', yaxis_title=f'Price ({currency})',
        xaxis_rangeslider_visible=False, plot_bgcolor='white',
        font=dict(family='Arial', size=14)
    )
    return fig

def generate_forecasts(db_path, tickers, forecast_horizon, target_currency):
    """
    Generates and displays forecasts for a list of tickers using data from the database.
    """
    all_results = {}
    print("\n" + "="*50)
    print("STARTING FORECASTING PROCESS")
    print("="*50)

    for symbol in tickers:
        try:
            print(f"\n--- Forecasting for {symbol} ---")
            
            # 1. Load data from the database
            data = load_data_from_db(db_path, symbol)
            
            # 2. Add technical indicators
            data_with_indicators = add_technical_indicators(data)
            
            # 3. Backtest model for accuracy check
            backtest_arima(data_with_indicators, test_size=30, order=(5,1,0))
            
            # 4. Generate the actual forecast
            print(f"Generating {forecast_horizon}-day forecast...")
            forecast = arima_forecast(data_with_indicators, forecast_horizon, order=(5,1,0))
            
            # 5. Handle currency conversion
            native_currency = STOCK_CURRENCY.get(symbol, 'USD')
            display_currency = target_currency
            
            if native_currency != display_currency:
                try:
                    fx_rate = get_fx_rate_from_db(db_path, native_currency, display_currency)
                    forecast *= fx_rate
                    print(f"Converted forecast from {native_currency} to {display_currency} using rate: {fx_rate:.4f}")
                except ValueError as e:
                    print(f"⚠️ Warning: Could not convert currency. {e}. Displaying in native currency ({native_currency}).")
                    display_currency = native_currency
            
            # 6. Prepare forecasted data for plotting
            ohlc_forecast = generate_ohlc_from_close(forecast)
            future_dates = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1), periods=forecast_horizon)
            ohlc_forecast.index = future_dates
            
            # 7. Generate and show the plot
            fig = create_forecast_plot(ohlc_forecast, symbol, forecast_horizon, display_currency)
            fig.show()

            all_results[symbol] = {'message': 'Success', 'forecast': ohlc_forecast}

        except Exception as e:
            print(f"❌ Error forecasting for {symbol}: {e}")
            all_results[symbol] = {'message': f'Failed: {e}', 'forecast': None}
            
    return all_results