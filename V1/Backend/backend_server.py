from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import requests
import numpy as np
from datetime import datetime, timedelta
from transformers import pipeline
import json
import os
import logging

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = app.logger

# Configuration
NEWSAPI_KEY = '4df94f613dd1434a98dd4ee95305e906'  # Your actual API key

# Initialize FinBERT model (this might take some time on first load)
try:
    finbert = pipeline(
        "sentiment-analysis",
        model="yiyanghkust/finbert-tone",
        tokenizer="yiyanghkust/finbert-tone",
        device=-1  # Use CPU
    )
    logger.info('✅ FinBERT model loaded successfully')
except Exception as e:
    logger.error(f'❌ Error loading FinBERT model: {e}')
    finbert = None

# Sample market data for demonstration
SAMPLE_MARKET_DATA = [
    {"symbol": "AAPL", "price": 189.84, "change": 2.34, "changePercent": 1.25},
    {"symbol": "GOOGL", "price": 142.56, "change": -1.45, "changePercent": -1.01},
    {"symbol": "MSFT", "price": 421.32, "change": 5.67, "changePercent": 1.37},
    {"symbol": "TSLA", "price": 248.50, "change": -3.21, "changePercent": -1.27},
    {"symbol": "NVDA", "price": 917.69, "change": 15.43, "changePercent": 1.71},
    {"symbol": "AMZN", "price": 186.51, "change": 0.94, "changePercent": 0.51},
    {"symbol": "META", "price": 521.18, "change": -2.15, "changePercent": -0.41},
    {"symbol": "JPM", "price": 207.88, "change": 1.23, "changePercent": 0.60}
]

# === SENTIMENT ANALYSIS FUNCTIONS ===

def fetch_ticker_news(ticker, n_headlines=15):
    """Fetch news headlines for a ticker symbol"""
    try:
        url = (
            "https://newsapi.org/v2/everything?"
            f"q={ticker}&language=en&sortBy=publishedAt&pageSize={n_headlines}&apiKey={NEWSAPI_KEY}"
        )
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            articles = resp.json().get("articles", [])
            headlines = [a['title'] for a in articles if a.get('title')]
            logger.info(f"Fetched {len(headlines)} news headlines for {ticker}")
            return headlines
        else:
            logger.warning(f"Failed to fetch news: {resp.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return []

def analyze_headline_sentiment(headlines):
    """Analyze sentiment of headlines using FinBERT"""
    if not finbert:
        logger.error("FinBERT model not available")
        return {'positive': 0, 'neutral': 0, 'negative': 0}, [], []

    if not headlines:
        return {'positive': 0, 'neutral': 0, 'negative': 0}, [], []

    sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    sentiment_scores = []
    results = []

    try:
        for text in headlines:
            # FinBERT max length is 512 tokens
            result = finbert(text[:512])[0]
            label = result['label'].lower()
            score = result['score']

            # Convert to numerical score
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
        logger.error(f"Error analyzing sentiment: {e}")
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

@app.route('/')
def index():
    """Serve the main HTML file"""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/api/sentiment-analysis/', methods=['GET'])
def get_sentiment_analysis():
    ticker = request.args.get('ticker', '').upper()
    try:
        # Get number of headlines from query parameter
        n_headlines = request.args.get('headlines', 15, type=int)

        # Fetch news headlines
        headlines = fetch_ticker_news(ticker.upper(), n_headlines)

        if not headlines:
            return jsonify({
                'success': False,
                'message': f'No news found for {ticker.upper()}',
                'ticker': ticker.upper(),
                'sentiment_counts': {'positive': 0, 'neutral': 0, 'negative': 0},
                'average_score': 0,
                'allocation_suggestion': suggest_allocation(0),
                'headlines': []
            })

        # Analyze sentiment
        sentiment_counts, sentiment_scores, detailed_results = analyze_headline_sentiment(headlines)
        avg_score = np.mean(sentiment_scores) if sentiment_scores else 0

        # Get allocation suggestion
        allocation = suggest_allocation(avg_score)

        return jsonify({
            'success': True,
            'ticker': ticker.upper(),
            'sentiment_counts': sentiment_counts,
            'average_score': float(avg_score),
            'allocation_suggestion': allocation,
            'headlines': detailed_results[:10],  # Return top 10 detailed results
            'total_headlines_analyzed': len(headlines),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in sentiment analysis for {ticker}: {e}")
        return jsonify({
            'success': False,
            'message': f'Error analyzing sentiment for {ticker}: {str(e)}',
            'ticker': ticker.upper()
        }), 500

@app.route('/api/bulk-sentiment', methods=['POST'])
def get_bulk_sentiment():
    """Get sentiment analysis for multiple tickers"""
    try:
        data = request.get_json()
        tickers = data.get('tickers', [])

        if not tickers:
            return jsonify({'success': False, 'message': 'No tickers provided'}), 400

        results = {}

        for ticker in tickers:
            try:
                headlines = fetch_ticker_news(ticker.upper(), 10)  # Fewer headlines for bulk processing
                if headlines:
                    sentiment_counts, sentiment_scores, detailed_results = analyze_headline_sentiment(headlines)
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
                logger.error(f"Error processing {ticker}: {e}")
                results[ticker.upper()] = {
                    'error': str(e),
                    'sentiment_counts': {'positive': 0, 'neutral': 0, 'negative': 0},
                    'average_score': 0,
                    'allocation_suggestion': suggest_allocation(0),
                    'headlines_count': 0
                }

        return jsonify({
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in bulk sentiment analysis: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/market-data', methods=['GET'])
def get_market_data():
    """Get market data with sentiment analysis"""
    try:
        # Add some sentiment data to market data for demonstration
        enhanced_market_data = []

        for stock in SAMPLE_MARKET_DATA:
            # Add a simulated sentiment score for demo purposes
            # In production, you'd fetch real sentiment data
            sentiment_score = np.random.uniform(-0.5, 0.5)
            enhanced_stock = stock.copy()
            enhanced_stock['sentiment_score'] = sentiment_score
            enhanced_stock['sentiment_label'] = 'positive' if sentiment_score > 0.1 else 'negative' if sentiment_score < -0.1 else 'neutral'
            enhanced_market_data.append(enhanced_stock)

        return jsonify(enhanced_market_data)

    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get portfolio data"""
    try:
        # Sample portfolio data
        portfolio_data = {
            'totalValue': 125847.32,
            'dailyChange': 2847.15,
            'dailyChangePercent': 2.31,
            'positions': [
                {'symbol': 'AAPL', 'shares': 50, 'value': 9492.00, 'change': 117.00},
                {'symbol': 'GOOGL', 'shares': 25, 'value': 3564.00, 'change': -36.25},
                {'symbol': 'MSFT', 'shares': 30, 'value': 12639.60, 'change': 170.10},
                {'symbol': 'TSLA', 'shares': 15, 'value': 3727.50, 'change': -48.15},
                {'symbol': 'NVDA', 'shares': 10, 'value': 9176.90, 'change': 154.30}
            ]
        }
        return jsonify(portfolio_data)

    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/news', methods=['GET'])
def get_news():
    """Get financial news with sentiment analysis"""
    try:
        # Sample news data with sentiment
        news_data = [
            {
                'title': 'Tech Stocks Rally as AI Optimism Grows',
                'summary': 'Major technology companies see significant gains as investors remain bullish on artificial intelligence prospects.',
                'timestamp': '2 hours ago',
                'sentiment': 'positive',
                'source': 'Financial Times'
            },
            {
                'title': 'Federal Reserve Signals Potential Rate Changes',
                'summary': 'Central bank officials hint at monetary policy adjustments in upcoming meetings.',
                'timestamp': '4 hours ago',
                'sentiment': 'neutral',
                'source': 'Reuters'
            },
            {
                'title': 'Market Volatility Concerns Rise Amid Global Tensions',
                'summary': 'Investors show caution as geopolitical events create uncertainty in global markets.',
                'timestamp': '6 hours ago',
                'sentiment': 'negative',
                'source': 'Bloomberg'
            }
        ]
        return jsonify(news_data)

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Handle user login"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Simple authentication (in production, use proper authentication)
        if email and password:
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {'email': email, 'name': email.split('@')[0]}
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'finbert_loaded': finbert is not None,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')

    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')

    print("🚀 Starting QuantFin Pro Backend Server...")
    print("📊 Sentiment Analysis API Ready")
    print("🔗 Frontend Integration Complete")
    print("\n📍 Available Endpoints:")
    print("   GET  /                                    - Main application")
    print("   GET  /api/sentiment-analysis/<ticker>     - Single ticker sentiment")
    print("   POST /api/bulk-sentiment                  - Multiple tickers sentiment")
    print("   GET  /api/market-data                     - Market data with sentiment")
    print("   GET  /api/portfolio                       - Portfolio information")
    print("   GET  /api/news                           - News with sentiment")
    print("   POST /api/auth/login                     - User authentication")
    print("   GET  /api/health                         - Health check")
    print("\n🌐 Access the application at: http://localhost:5000")

    app.run(debug=True, host='0.0.0.0', port=5000)
