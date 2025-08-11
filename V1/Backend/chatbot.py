# chatbot.py

import sys
import sqlite3
import pandas as pd
from pathlib import Path
import groq  # New import

# Add project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import config
from data.etl_pipeline import run_etl_pipeline
from stock_forecast import generate_forecasts

# --- Updated Groq Client Initialization ---
groq_client = None
key_found = False
api_key = config.get('GROQ_API_KEY')

if api_key:
    groq_client = groq.Groq(api_key=api_key)
    key_found = True
else:
    print("⚠️  Warning: GROQ_API_KEY not found in your .env file. The general Q&A function will be disabled.")


# --- Helper Functions (No changes here) ---

def get_last_close_price(db_path, ticker):
    with sqlite3.connect(db_path) as conn:
        query = "SELECT close FROM market_data WHERE symbol = ? ORDER BY date DESC LIMIT 1"
        cursor = conn.cursor()
        result = cursor.execute(query, (ticker,)).fetchone()
    return result[0] if result else None

def get_allocation_decision(forecast_df, last_actual_price, forecast_horizon):
    if forecast_df is None or forecast_df.empty or last_actual_price is None:
        return "Insufficient Data", "Could not make a decision due to lack of data."

    last_forecast_price = forecast_df['close'].iloc[-1]
    pct_change = ((last_forecast_price - last_actual_price) / last_actual_price) * 100

    if pct_change > 4.0:
        decision = "Potential Buy Opportunity"
        justification = f"The model forecasts a potential upside of {pct_change:.2f}% over the next {forecast_horizon} days."
    elif pct_change < -4.0:
        decision = "Potential Sell/Review"
        justification = f"The model forecasts a potential downside of {abs(pct_change):.2f}% over the next {forecast_horizon} days."
    else:
        decision = "Hold / Monitor"
        justification = f"The forecast indicates a relatively stable trend with a potential change of {pct_change:.2f}%."

    return decision, justification

# --- Updated Q&A Function for Groq ---
def handle_general_question(query):
    """
    Handles general financial questions by sending them to the Groq API.
    """
    if not key_found or groq_client is None:
        print("Sorry, the Q&A function is disabled because the Groq API key is missing.")
        return

    print("")
    try:
        # --- NEW, MORE FORCEFUL SYSTEM PROMPT ---
        system_message = {
            "role": "system",
            "content": ""
        }

        stream = groq_client.chat.completions.create(
            model="llama3-8b-8192",  # Groq uses specific model names
            messages=[system_message, {"role": "user", "content": query}],
            stream=True,
        )
        
        for chunk in stream:
            print(chunk.choices[0].delta.content or "", end="")
        print("\n")

    except Exception as e:
        print(f"Sorry, I encountered an error with the AI model: {e}")
# def handle_general_question(query):
#     """
#     Handles general financial questions by sending them to the Groq API.
#     """
#     if not key_found or groq_client is None:
#         print("Sorry, the Q&A function is disabled because the Groq API key is missing.")
#         return

#     print("\n⚡ Asking Groq... (This will be fast!)\n")
#     try:
#         system_message = {
#             "role": "system",
#             "content": """
#             You are a helpful financial AI assistant. Your role is to answer general financial questions.
#             You must always begin your response with a disclaimer stating that you are an AI and not a licensed financial advisor, and that your information is for educational purposes only.
#             Do not provide personal financial advice. Keep your answers clear and concise.
#             """
#         }

#         stream = groq_client.chat.completions.create(
#             model="llama3-8b-8192",  # Groq uses specific model names
#             messages=[system_message, {"role": "user", "content": query}],
#             stream=True,
#         )
        
#         for chunk in stream:
#             print(chunk.choices[0].delta.content or "", end="")
#         print("\n")

#     except Exception as e:
#         print(f"Sorry, I encountered an error with the AI model: {e}")

# --- Main Chatbot Loop (No changes here) ---

def run_chatbot():
    print("="*60)
    print("📈 Welcome to the AI Financial Chatbot! (Powered by Groq)")
    print("="*60)
    print("You can ask for a stock forecast (e.g., 'forecast TSLA for 30 days in USD')")
    print("or ask a general financial question (e.g., 'what is a mutual fund?').")
    print("\nIMPORTANT DISCLAIMER:")
    print("I am an AI assistant, not a licensed financial advisor. All information,")
    print("forecasts, and suggestions are for educational purposes only.")
    print("Type 'quit' or 'exit' to close the chatbot.\n")
    
    if not key_found:
        print("NOTE: Groq API key not found. General Q&A will be disabled.\n")

    db_path = config.get('DATABASE_PATH', 'database/financial_data.db')

    while True:
        user_input = input(">> ").strip()

        if user_input.lower() in ['quit', 'exit']:
            print("👋 Goodbye!")
            break
        
        if not user_input:
            continue

        if user_input.lower().startswith('forecast'):
            try:
                parts = user_input.split()
                ticker = parts[1].upper()
                days = int(parts[3])
                currency = parts[6].upper()

                print(f"\nAlright, processing your request for a {days}-day forecast for {ticker} in {currency}.")
                print(f"\n[1/4] Updating database for {ticker}...")
                run_etl_pipeline('market', [ticker], db_path)
                print("[1/4] Database update complete.")

                print(f"\n[2/4] Generating forecast...")
                forecast_results = generate_forecasts(db_path, [ticker], days, currency)
                print("[2/4] Forecast generation complete.")

                print("\n[3/4] Analyzing forecast for allocation decision...")
                forecast_df = forecast_results.get(ticker, {}).get('forecast')
                last_actual_price = get_last_close_price(db_path, ticker)
                
                decision, justification = get_allocation_decision(forecast_df, last_actual_price, days)
                print(f"Decision: {decision}")
                print(f"Justification: {justification}")
                
                print("\n[4/4] Process Complete!")
                if forecast_df is not None:
                    print(f"✅ Forecast plot for {ticker} has been generated in a new window.")
                else:
                    print(f"❌ Failed to generate forecast for {ticker}.")

                print("\nWhat would you like to do next?")

            except (IndexError, ValueError):
                print("Invalid command format. Please use: 'forecast [TICKER] for [DAYS] days in [CURRENCY]'")
            except Exception as e:
                print(f"An unexpected error occurred during forecasting: {e}")
        else:
            handle_general_question(user_input)
            print("\nWhat would you like to do next?")

if __name__ == "__main__":
    run_chatbot()