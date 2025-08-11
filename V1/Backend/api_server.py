# In api_server.py, at the top with other imports
import os
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
import asyncio
import sys
from pathlib import Path
import requests
from fastapi import HTTPException
from logging import getLogger,basicConfig

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import config
from data.etl_pipeline import run_etl_pipeline
from stock_forecast import generate_forecasts
from chatbot import handle_general_question, get_last_close_price, get_allocation_decision

# Initialize FastAPI app
app = FastAPI(title="Portfolio Dashboard API", version="1.0.0")

# CORS configuration for frontend
# Make sure this is right after the app instance is created and is not duplicated
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the FinBERT model
try:
    finbert_pipeline = pipeline(
        "sentiment-analysis",
        model="yiyanghkust/finbert-tone",
        tokenizer="yiyanghkust/finbert-tone",
        device=-1  # Use CPU
    )
    print('✅ FinBERT model loaded successfully')
except Exception as e:
    print(f'❌ Error loading FinBERT model: {e}')
    finbert_pipeline = None

# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    type: str  # "general" or "forecast"

class ForecastRequest(BaseModel):
    ticker: str
    days: int
    currency: str

class TradeRequest(BaseModel):
    symbol: str
    quantity: int
    action: str  # "buy" or "sell"

class PortfolioData(BaseModel):
    totalValue: float
    dailyChange: float
    dailyChangePercent: float
    totalReturn: float
    totalReturnPercent: float
    allocation: Dict[str, float]

class MarketDataItem(BaseModel):
    symbol: str
    price: float
    change: Optional[float]
    changePercent: Optional[float]

class NewsItem(BaseModel):
    title: str
    summary: str
    sentiment: str
    time: str
    url: Optional[str] = None

class TeamMember(BaseModel):
    name: str
    role: str
    description: str
    expertise: List[str]
    linkedin: str
    image: str


# Database helper functions
def get_db_connection():
    db_path = config.get('DATABASE_PATH', 'database/financial_data.db')
    return sqlite3.connect(db_path)

def get_portfolio_from_db():
    """Get portfolio data from database or return mock data"""
    try:
        with get_db_connection() as conn:
            query = """
            SELECT symbol, SUM(close * volume) as total_value, COUNT(*) as positions
            FROM market_data
            WHERE date = (SELECT MAX(date) FROM market_data)
            GROUP BY symbol
            """
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                total_value = df['total_value'].sum()
                daily_change = total_value * 0.0232
                return {
                    "totalValue": total_value,
                    "dailyChange": daily_change,
                    "dailyChangePercent": 2.32,
                    "totalReturn": total_value * 0.2542,
                    "totalReturnPercent": 25.42,
                    "allocation": {
                        "stocks": 65.2,
                        "bonds": 15.8,
                        "crypto": 12.5,
                        "cash": 6.5
                    }
                }
    except Exception as e:
        print(f"Error getting portfolio from DB: {e}")
        getLogger(__name__).error(e)
    
    return {
        "totalValue": 125420.50,
        "dailyChange": 2840.25,
        "dailyChangePercent": 2.32,
        "totalReturn": 25420.50,
        "totalReturnPercent": 25.42,
        "allocation": {
            "stocks": 65.2,
            "bonds": 15.8,
            "crypto": 12.5,
            "cash": 6.5
        }
    }

def get_market_data_from_db():
    """Get latest market data from database"""
    try:
        with get_db_connection() as conn:
            query = """
            SELECT symbol, close as price,
                    (close - LAG(close) OVER (PARTITION BY symbol ORDER BY date)) as change,
                    ((close - LAG(close) OVER (PARTITION BY symbol ORDER BY date)) / LAG(close) OVER (PARTITION BY symbol ORDER BY date)) * 100 as changePercent
            FROM market_data
            WHERE date = (SELECT MAX(date) FROM market_data)
            """
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                return df.to_dict('records')
    except Exception as e:
        print(f"Error getting market data from DB: {e}")
    
    return [
        {"symbol": "AAPL", "price": 195.84, "change": 2.34, "changePercent": 1.21},
        {"symbol": "GOOGL", "price": 142.56, "change": -1.23, "changePercent": -0.85},
        {"symbol": "MSFT", "price": 378.91, "change": 4.67, "changePercent": 1.25},
        {"symbol": "TSLA", "price": 248.73, "change": -3.21, "changePercent": -1.27},
        {"symbol": "NVDA", "price": 567.12, "change": 12.45, "changePercent": 2.24},
        {"symbol": "BTC-USD", "price": 67234.56, "change": 1823.45, "changePercent": 2.78}
    ]

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Portfolio Dashboard API is running"}

@app.get("/api/portfolio", response_model=PortfolioData)
async def get_portfolio():
    """Get portfolio overview data"""
    try:
        portfolio_data = get_portfolio_from_db()
        return PortfolioData(**portfolio_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio data: {str(e)}")

@app.get("/api/market-data", response_model=List[MarketDataItem])
async def get_market_data():
    """Get latest market data for ticker and watchlist"""
    try:
        market_data = get_market_data_from_db()
        print(type(market_data))
        return [MarketDataItem(**item) for item in market_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")

@app.get("/api/team", response_model=List[TeamMember])
async def get_team():
    """Get team members information"""
    team_members = [
        {
            "name": "Shivam Vijai Sharma",
            "role": "Team Lead",
            "description": "Leading the team with vision and clarity, bringing strong technical insight into quantitative finance and algorithmic trading.",
            "expertise": ["Quantitative Finance", "Algorithmic Trading", "Python", "LaTeX", "Team Leadership"],
            "linkedin": "https://www.linkedin.com/in/shivam-sharma-80a838261/",
            "image": "shivam.png"
        },
        {
            "name": "Aditya Dave",
            "role": "Financial Strategy Developer",
            "description": "A meticulous thinker with a knack for market behavior, focusing on shaping financial logic and trading models.",
            "expertise": ["Market Analysis", "Trading Models", "Python", "Financial Logic", "Algorithm Development"],
            "linkedin": "https://www.linkedin.com/in/aditya-dave-690097352/",
            "image": "aditya.jpg"
        },
        {
            "name": "Mohit Patil",
            "role": "Full Stack Developer",
            "description": "Crafting digital interfaces and backend flow, translating ideas into seamless user experiences.",
            "expertise": ["Full Stack Development", "Web Technologies", "Machine Learning", "Backend Systems"],
            "linkedin": "https://www.linkedin.com/in/mohit-mangesh-patil-606a7b361/",
            "image": "mohit.jpg"
        }
    ]
    return [TeamMember(**member) for member in team_members]

# === SENTIMENT ANALYSIS FUNCTIONS ===
def fetch_ticker_news(ticker, n_headlines=15):
    """Fetch news headlines for a ticker symbol"""
    try:
        NEWSAPI_KEY = config.get('NEWS_API_KEY')
        if not NEWSAPI_KEY:
            raise ValueError("NEWSAPI_KEY not configured")

        url = (
            "https://newsapi.org/v2/everything?"
            f"q={ticker}&language=en&sortBy=publishedAt&pageSize={n_headlines}&apiKey={NEWSAPI_KEY}"
        )
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            articles = resp.json().get("articles", [])
            headlines = [a['title'] for a in articles if a.get('title')]
            # Assuming logger is configured
            # logger.info(f"Fetched {len(headlines)} news headlines for {ticker}")
            return headlines
        else:
            # Assuming logger is configured
            # logger.warning(f"Failed to fetch news: {resp.status_code}")
            return []
    except Exception as e:
        # Assuming logger is configured
        # logger.error(f"Error fetching news for {ticker}: {e}")
        return []

def analyze_headline_sentiment(headlines):
    """Analyze sentiment of headlines using FinBERT"""
    if not finbert_pipeline:
        print("FinBERT model not available")
        return {'positive': 0, 'neutral': 0, 'negative': 0}, [], []

    if not headlines:
        return {'positive': 0, 'neutral': 0, 'negative': 0}, [], []

    sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    sentiment_scores = []
    results = []

    try:
        for text in headlines:
            result = finbert_pipeline(text[:512])[0]
            label = result['label'].lower()
            score = result['score']
            numerical_score = score if label == 'positive' else -score if label == 'negative' else 0
            sentiment_scores.append(numerical_score)
            sentiment_counts[label] += 1
            results.append({
                'text': text,
                'label': label,
                'score': score,
                'numerical_score': numerical_score
            })
        return sentiment_counts, sentiment_scores, results
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return {'positive': 0, 'neutral': 0, 'negative': 0}, [], []

def suggest_allocation(avg_score):
    """Suggest asset allocation based on sentiment score"""
    if avg_score > 0.3:
        return {
            "strategy": "🚀 Aggressive",
            "allocation": {"stocks": 80, "bonds": 15, "cash": 5},
            "description": "High confidence, aggressive growth strategy"
        }
    elif avg_score > 0.1:
        return {
            "strategy": "🙂 Growth",
            "allocation": {"stocks": 65, "bonds": 25, "cash": 10},
            "description": "Moderate confidence, growth-oriented strategy"
        }
    elif avg_score < -0.3:
        return {
            "strategy": "🛡️ Defensive",
            "allocation": {"stocks": 15, "bonds": 60, "cash": 25},
            "description": "Low confidence, capital preservation focus"
        }
    elif avg_score < -0.1:
        return {
            "strategy": "🙁 Conservative",
            "allocation": {"stocks": 30, "bonds": 50, "cash": 20},
            "description": "Cautious approach, reduced risk exposure"
        }
    else:
        return {
            "strategy": "😐 Balanced",
            "allocation": {"stocks": 50, "bonds": 35, "cash": 15},
            "description": "Neutral sentiment, balanced approach"
        }

# === API ROUTES ===
from pydantic import BaseModel

class BulkSentimentRequest(BaseModel):
    tickers: List[str]

@app.get("/api/sentiment-analysis")
async def get_sentiment_analysis(ticker: str, headlines: int = 15):
    """Get sentiment analysis for a single ticker."""
    ticker = ticker.upper()
    try:
        news_headlines = fetch_ticker_news(ticker, headlines)

        if not news_headlines:
            return {
                'success': False,
                'message': f'No news found for {ticker}',
                'ticker': ticker,
                'sentiment_counts': {'positive': 0, 'neutral': 0, 'negative': 0},
                'average_score': 0,
                'allocation_suggestion': suggest_allocation(0),
                'headlines': []
            }

        sentiment_counts, sentiment_scores, detailed_results = analyze_headline_sentiment(news_headlines)
        avg_score = np.mean(sentiment_scores) if sentiment_scores else 0
        allocation = suggest_allocation(avg_score)

        return {
            'success': True,
            'ticker': ticker,
            'sentiment_counts': sentiment_counts,
            'average_score': float(avg_score),
            'allocation_suggestion': allocation,
            'headlines': detailed_results[:10],
            'total_headlines_analyzed': len(news_headlines)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error analyzing sentiment for {ticker}: {str(e)}')

@app.post("/api/bulk-sentiment")
async def get_bulk_sentiment(request: BulkSentimentRequest):
    """Get sentiment analysis for multiple tickers."""
    if not request.tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")

    results = {}
    for ticker in request.tickers:
        try:
            headlines = fetch_ticker_news(ticker.upper(), 10)
            if headlines:
                sentiment_counts, sentiment_scores, _ = analyze_headline_sentiment(headlines)
                avg_score = np.mean(sentiment_scores) if sentiment_scores else 0
                allocation = suggest_allocation(avg_score)
                results[ticker.upper()] = {
                    'sentiment_counts': sentiment_counts,
                    'average_score': float(avg_score),
                    'allocation_suggestion': allocation,
                    'headlines_count': len(headlines)
                }
            else:
                results[ticker.upper()] = {
                    'sentiment_counts': {'positive': 0, 'neutral': 0, 'negative': 0},
                    'average_score': 0,
                    'allocation_suggestion': suggest_allocation(0),
                    'headlines_count': 0
                }
        except Exception as e:
            results[ticker.upper()] = {
                'error': str(e),
                'sentiment_counts': {'positive': 0, 'neutral': 0, 'negative': 0},
                'average_score': 0,
                'allocation_suggestion': suggest_allocation(0),
                'headlines_count': 0
            }
    return {'success': True, 'results': results}


@app.get("/api/news", response_model=List[NewsItem])
async def get_news():
    api_key = config.get('NEWS_API_KEY')
    url = (
    "https://newsapi.org/v2/top-headlines?"
    "category=business&language=en&pageSize=8&apiKey={}".format(api_key)
    )

    try:
        resp = requests.get(url, timeout=7)
        if resp.status_code == 200:
            articles = resp.json().get("articles", [])
            news_items = []
            for a in articles:
                news_items.append({
                    "title": a["title"],
                    "summary": a["description"] or "",
                    "sentiment": "",
                    "time": a["publishedAt"],
                    "url": a.get("url")
                })
            return news_items
        else:
            raise HTTPException(status_code=500, detail="News API error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News fetch failed: {e}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(message: ChatMessage):
    """Handle AI chat requests"""
    try:
        user_input = message.message.strip()

        if user_input.lower().startswith('forecast'):
            try:
                parts = user_input.split()
                ticker = parts[1].upper()
                days = int(parts[3])
                currency = parts[6].upper()
                db_path = config.get('DATABASE_PATH', 'database/financial_data.db')
                run_etl_pipeline('market', [ticker], db_path)
                forecast_results = generate_forecasts(db_path, [ticker], days, currency)
                forecast_df = forecast_results.get(ticker, {}).get('forecast')
                last_actual_price = get_last_close_price(db_path, ticker)
                decision, justification = get_allocation_decision(forecast_df, last_actual_price, days)
                response_text = f"Forecast completed for {ticker}.\n\nDecision: {decision}\nJustification: {justification}"
                return ChatResponse(response=response_text, type="forecast")
            except (IndexError, ValueError) as e:
                return ChatResponse(
                    response="Invalid forecast format. Please use: 'forecast [TICKER] for [DAYS] days in [CURRENCY]'",
                    type="general"
                )
        else:
            try:
                import io
                import sys
                from contextlib import redirect_stdout
                f = io.StringIO()
                with redirect_stdout(f):
                    handle_general_question(user_input)
                ai_response = f.getvalue()
                if not ai_response.strip():
                    ai_response = "I'm here to help with your financial questions. Could you please rephrase your question?"
                return ChatResponse(response=ai_response, type="general")
            except Exception as e:
                return ChatResponse(
                    response="I'm experiencing some technical difficulties. Please try again later.",
                    type="general"
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@app.post("/api/forecast")
async def generate_forecast(request: ForecastRequest, background_tasks: BackgroundTasks):
    """Generate stock forecast"""
    try:
        db_path = config.get('DATABASE_PATH', 'database/financial_data.db')
        background_tasks.add_task(run_etl_pipeline, 'market', [request.ticker], db_path)
        forecast_results = generate_forecasts(db_path, [request.ticker], request.days, request.currency)
        return {"status": "success", "results": forecast_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")

@app.post("/api/trade")
async def execute_trade(request: TradeRequest):
    """Execute a trade (mock implementation)"""
    try:
        return {
            "status": "success",
            "message": f"Successfully {request.action} {request.quantity} shares of {request.symbol}",
            "orderId": f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing trade: {str(e)}")

@app.get("/api/analytics/sentiment")
async def get_market_sentiment():
    """Get AI market sentiment analysis"""
    return {
        "sentiment": "Bullish",
        "confidence": 85,
        "factors": [
            "Strong earnings reports from tech sector",
            "Positive GDP growth indicators",
            "Stable inflation rates"
        ]
    }

@app.get("/api/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

from fastapi import APIRouter
from typing import List

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(request: LoginRequest):
    if request.username == "admin" and request.password == "secret":
        return {"token": "jwt-or-session-token"}
    raise HTTPException(status_code=401, detail="Incorrect credentials")


class PortfolioHistoryItem(BaseModel):
    date: str
    total_value: float

@app.get("/api/portfolio/history", response_model=List[PortfolioHistoryItem])
async def get_portfolio_history():
    """
    Get portfolio performance history (time series).
    """
    try:
        with get_db_connection() as conn:
            query = """
            SELECT date, SUM(close * volume) AS total_value
            FROM market_data
            GROUP BY date
            ORDER BY date ASC
            """
            df = pd.read_sql_query(query, conn)
            if not df.empty:
                history = [
                    {"date": row["date"], "total_value": float(row["total_value"])}
                    for idx, row in df.iterrows()
                ]
                return history
            else:
                from datetime import datetime, timedelta
                today = datetime.today()
                return [
                    {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "total_value": 100000 + 500*i}
                    for i in range(10, -1, -1)
                ]
    except Exception as e:
        print(f"Error in get_portfolio_history: {e}")
        raise HTTPException(status_code=500, detail="Unable to get portfolio history")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)