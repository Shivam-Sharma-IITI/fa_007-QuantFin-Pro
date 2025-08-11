# data/etl_pipeline.py

import sqlite3
import logging
import requests
import time
from datetime import datetime
from config.config import config
from pathlib import Path

logger = logging.getLogger(__name__)

# def _setup_database(db_path):
#     """Creates database tables if they don't exist."""
#     logger.info(f"Setting up database at {db_path}...")
#     with sqlite3.connect(db_path) as conn:
#         cursor = conn.cursor()
        
#         # Create table for market data
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS market_data (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 symbol TEXT NOT NULL,
#                 date DATE NOT NULL,
#                 open REAL,
#                 high REAL,
#                 low REAL,
#                 close REAL,
#                 volume INTEGER,
#                 UNIQUE(symbol, date)
#             )
#         ''')
        
#         # Create table for currency exchange rates
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS fx_rates (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 date DATE NOT NULL,
#                 from_currency TEXT NOT NULL,
#                 to_currency TEXT NOT NULL,
#                 rate REAL,
#                 UNIQUE(date, from_currency, to_currency)
#             )
#         ''')
        
#         conn.commit()
#     logger.info("Database setup complete.")
def _setup_database(db_path):
    """Creates the database directory and tables if they don't exist."""
    db_file = Path(db_path)
    # Create the parent directory if it doesn't exist
    db_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Setting up database at {db_path}...")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Create table for market data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                UNIQUE(symbol, date)
            )
        ''')

        # Create table for currency exchange rates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fx_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                rate REAL,
                UNIQUE(date, from_currency, to_currency)
            )
        ''')

        conn.commit()
    logger.info("Database setup complete.")

def _fetch_market_data(tickers):
    """Fetches daily stock data from Alpha Vantage and returns it."""
    logger.info(f"Fetching market data for: {tickers}")
    api_key = config.get('ALPHA_VANTAGE_API_KEY')
    all_data = []
    
    for symbol in tickers:
        logger.debug(f"Requesting data for {symbol}...")
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': 'full', # 'compact' for last 100 days, 'full' for all history
            'apikey': api_key
        }
        response = requests.get('https://www.alphavantage.co/query', params=params)
        data = response.json()
        
        if 'Time Series (Daily)' not in data:
            logger.error(f"Could not fetch data for {symbol}: {data.get('Note') or data.get('Error Message', 'Unknown error')}")
            time.sleep(15) # Sleep to avoid hitting rate limits
            continue

        for date_str, values in data['Time Series (Daily)'].items():
            all_data.append({
                'symbol': symbol,
                'date': datetime.strptime(date_str, '%Y-%m-%d').date(),
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': int(values['5. volume'])
            })
        
        # Alpha Vantage has a rate limit of 5 calls per minute for the free tier.
        # A 15-second sleep is a safe buffer.
        logger.info(f"Successfully fetched data for {symbol}. Waiting to avoid rate limit...")
        time.sleep(15)
        
    return all_data

def _fetch_fx_rates():
    """Fetches required FX rates (e.g., USD to INR) for currency conversion."""
    logger.info("Fetching FX rates...")
    # This is needed for stocks like RELIANCE.NS (INR) if the target currency is USD
    api_key = config.get('ALPHA_VANTAGE_API_KEY')
    pairs = [('INR', 'USD'), ('USD', 'INR')] # Add other pairs if needed
    all_rates = []

    for from_curr, to_curr in pairs:
        params = {
            'function': 'FX_DAILY',
            'from_symbol': from_curr,
            'to_symbol': to_curr,
            'outputsize': 'full',
            'apikey': api_key
        }
        response = requests.get('https://www.alphavantage.co/query', params=params)
        data = response.json()
        
        if 'Time Series FX (Daily)' not in data:
            logger.error(f"Could not fetch FX rate for {from_curr}->{to_curr}: {data.get('Note') or data.get('Error Message', 'Unknown error')}")
            time.sleep(15)
            continue

        for date_str, values in data['Time Series FX (Daily)'].items():
            all_rates.append({
                'date': datetime.strptime(date_str, '%Y-%m-%d').date(),
                'from_currency': from_curr,
                'to_currency': to_curr,
                'rate': float(values['4. close'])
            })
        
        logger.info(f"Successfully fetched FX for {from_curr}->{to_curr}. Waiting...")
        time.sleep(15)
        
    return all_rates

def _save_to_db(db_path, table_name, data_list):
    """Saves a list of dictionaries to the specified database table."""
    if not data_list:
        logger.info(f"No new data to save to table {table_name}.")
        return 0
        
    logger.info(f"Saving {len(data_list)} records to {table_name}...")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Use INSERT OR IGNORE to avoid errors on duplicate entries (based on UNIQUE constraints)
        for record in data_list:
            columns = ', '.join(record.keys())
            placeholders = ', '.join(['?'] * len(record))
            sql = f'INSERT OR IGNORE INTO {table_name} ({columns}) VALUES ({placeholders})'
            cursor.execute(sql, tuple(record.values()))
            
        conn.commit()
    logger.info(f"Save complete for {table_name}.")
    return len(data_list)


def run_etl_pipeline(pipeline_type, tickers, db_path):
    """
    Main function to run the ETL pipeline based on the specified type.
    """
    _setup_database(db_path)
    records_processed = {}
    
    if pipeline_type in ['full', 'market']:
        market_data = _fetch_market_data(tickers)
        records_processed['market'] = _save_to_db(db_path, 'market_data', market_data)

        fx_rates = _fetch_fx_rates()
        records_processed['fx_rates'] = _save_to_db(db_path, 'fx_rates', fx_rates)

    if pipeline_type in ['full', 'macro']:
        logger.info("Macro data pipeline not yet implemented.")
        records_processed['macro'] = 0

    if pipeline_type in ['full', 'news']:
        logger.info("News data pipeline not yet implemented.")
        records_processed['news'] = 0

    if pipeline_type in ['full', 'social']:
        logger.info("Social media data pipeline not yet implemented.")
        records_processed['social'] = 0
        
    return {"status": "success", "records_processed": records_processed}        