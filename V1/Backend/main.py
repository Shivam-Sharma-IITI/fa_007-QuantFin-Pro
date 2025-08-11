"""
Main entry point for AI Asset Allocator Phase 1

Runs the ETL pipeline and then the forecasting module with command line arguments
"""

import argparse
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.logging_config import setup_logging
from data.etl_pipeline import run_etl_pipeline
from config.config import config

# Import the new forecasting function from stock_forecast.py
from stock_forecast import generate_forecasts

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='AI Asset Allocator ETL & Forecast Pipeline')
    parser.add_argument(
        '--pipeline-type',
        choices=['full', 'market', 'macro', 'news', 'social'],
        default='full',
        help='Type of ETL pipeline to run'
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        help='List of ticker symbols to process'
    )
    parser.add_argument(
        '--db-path',
        help='Custom database path'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    parser.add_argument(
        '--validate-config',
        action='store_true',
        help='Validate configuration and API keys'
    )
    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Validate configuration if requested
    if args.validate_config:
        if config.validate_config():
            print("✅ Configuration is valid")
            return 0
        else:
            print("❌ Configuration validation failed")
            return 1

    try:
        # Determine the tickers to process for the ETL pipeline
        if args.tickers:
            tickers_to_process = args.tickers
        else:
            # Fallback to default tickers from the .env configuration
            tickers_to_process = [t.strip() for t in config.get('DEFAULT_TICKERS', '').split(',') if t.strip()]
        
        if not tickers_to_process:
            print("❌ No tickers specified. Provide them via --tickers or in the .env file.")
            return 1

        # Determine the database path
        db_path = args.db_path if args.db_path else config.get('DATABASE_PATH')
        if not db_path:
            print("❌ Database path not set. Provide it via --db-path or in the .env file.")
            return 1

        # Run ETL pipeline
        etl_results = run_etl_pipeline(
            pipeline_type=args.pipeline_type,
            tickers=tickers_to_process,
            db_path=db_path
        )

        # Print ETL summary
        print("\n" + "="*50)
        print("ETL PIPELINE COMPLETED SUCCESSFULLY")
        print("="*50)
        if 'records_processed' in etl_results:
            records = etl_results['records_processed']
            if isinstance(records, dict):
                for data_type, count in records.items():
                    print(f"{data_type.capitalize()}: {count:,} records")
            else:
                print(f"Total records processed: {records:,}")
        print("="*50)

        # --- FORECASTING SECTION ---
        # After ETL, run the forecast on the same tickers using the populated database
        
        print("\n🚀 Proceeding to forecasting...")
        try:
            forecast_horizon = int(input('Enter number of days to forecast (e.g., 7, 30, 90): '))
            target_currency = input('Enter the currency for the forecast (e.g., USD, EUR, INR): ').upper()
        except (ValueError, TypeError):
            print("\n❌ Invalid input. Please enter a whole number for the forecast days.")
            return 1

        forecast_results = generate_forecasts(
            db_path=db_path,
            tickers=tickers_to_process,
            forecast_horizon=forecast_horizon,
            target_currency=target_currency
        )

        # Print forecast summary
        print("\n" + "="*50)
        print("FORECASTING SUMMARY")
        print("="*50)
        for symbol, result in forecast_results.items():
            print(f"Ticker: {symbol}")
            print(f"Status: {result['message']}")
            if result['forecast'] is not None:
                print("Forecasted Prices (OHLC):")
                print(result['forecast'].round(2))
            print("-" * 25)
        print("="*50)
        print("\n📈 Forecast plots have been generated in separate windows.")

        return 0
    except Exception as e:
        print(f"\n❌ Pipeline or Forecasting failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())