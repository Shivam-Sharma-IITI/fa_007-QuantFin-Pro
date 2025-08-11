// Your Firebase project configuration
const firebaseConfig = {
  apiKey: "AIzaSyDTjmFYmteSH9oGlvQzKFvzhwNdoTzdyG4",
  authDomain: "iitisoc-9a022.firebaseapp.com",
  projectId: "iitisoc-9a022",
  storageBucket: "iitisoc-9a022.firebasestorage.app",
  messagingSenderId: "985980490635",
  appId: "1:985980490635:web:30a5ad2ac8d62dc08bd58e",
  measurementId: "G-59FZV3FS52"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// DOM Elements for Authentication
const authContainer = document.getElementById('auth-container');
const appContainer = document.getElementById('app-container');
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const logoutBtn = document.getElementById('logout-btn');
const showSignupBtn = document.getElementById('show-signup');
const showLoginBtn = document.getElementById('show-login');
const userInfo = document.getElementById('user-info');
const userEmailSpan = document.getElementById('user-email');
const loginErrorMsg = document.getElementById('login-error-message');
const signupErrorMsg = document.getElementById('signup-error-message');

// --- Authentication State Observer ---
// This is the core function that checks if a user is logged in or out.
auth.onAuthStateChanged(user => {
    if (user) {
        // User is signed in.
        console.log('User is signed in:', user.email);
        
        // Show the main application and hide the auth forms
        authContainer.classList.add('hidden');
        appContainer.classList.remove('hidden');

        // Display user info in the header
        userEmailSpan.textContent = user.email;
        userInfo.classList.remove('hidden');

        // Initialize the main dashboard application
        // This ensures the dashboard only loads for logged-in users.
        //initializeApp();

    } else {
        // User is signed out.
        console.log('User is signed out.');

        // Show the authentication forms and hide the main application
        authContainer.classList.remove('hidden');
        appContainer.classList.add('hidden');
        
        // Hide user info from the header
        userInfo.classList.add('hidden');
        userEmailSpan.textContent = '';
    }
});

// --- Event Listeners for Auth Forms ---

if(loginForm) {
    // Login Form Submission
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = loginForm['login-email'].value;
        const password = loginForm['login-password'].value;

        auth.signInWithEmailAndPassword(email, password)
            .then(userCredential => {
                console.log('User logged in:', userCredential.user.email);
                loginForm.reset();
                loginErrorMsg.classList.add('hidden');
            })
            .catch(error => {
                console.error('Login Error:', error.message);
                loginErrorMsg.textContent = error.message;
                loginErrorMsg.classList.remove('hidden');
            });
    });
}

if(signupForm) {
    // Signup Form Submission
    signupForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = signupForm['signup-email'].value;
        const password = signupForm['signup-password'].value;

        auth.createUserWithEmailAndPassword(email, password)
            .then(userCredential => {
                console.log('User signed up:', userCredential.user.email);
                signupForm.reset();
                signupErrorMsg.classList.add('hidden');
            })
            .catch(error => {
                console.error('Signup Error:', error.message);
                signupErrorMsg.textContent = error.message;
                signupErrorMsg.classList.remove('hidden');
            });
    });
}

if(logoutBtn) {
    // Logout Button Click
    logoutBtn.addEventListener('click', () => {
        auth.signOut().then(() => {
            console.log('User signed out successfully.');
            // The onAuthStateChanged observer will handle the UI changes.
        });
    });
}
        
if(showSignupBtn) {
    // Toggle between Login and Signup forms
    showSignupBtn.addEventListener('click', () => {
        loginForm.classList.add('hidden');
        signupForm.classList.remove('hidden');
        loginErrorMsg.classList.add('hidden');
    });
}

if(showLoginBtn) {
    showLoginBtn.addEventListener('click', () => {
        signupForm.classList.add('hidden');
        loginForm.classList.remove('hidden');
        signupErrorMsg.classList.add('hidden');
    });
}
// --- Portfolio Dashboard App - 2025 Advanced Features with API Integration ---

// API Configuration
const API_BASE_URL = 'http://localhost:8000';        // FastAPI backend (portfolio, market, etc.)
  

// Application Data
let portfolioData = {};
let marketData = [];
let teamMembers = [];
let news = [];

// Global variables for charts
let allocationChart = null;
let performanceChart = null;
let trendsChart = null;

// DOM Elements - Initialize after DOM is loaded
let hamburgerBtn, sidebar, mainContent, themeToggle, chatbotFab, chatbotModal, closeChatbot, loadingScreen;

// --- API Helper ---
async function apiRequest(endpoint, options = {}) {
    console.log(`Making API request to: ${API_BASE_URL}${endpoint}`);
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        console.log(`API response status: ${response.status} for ${endpoint}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`API Error for ${endpoint}:`, response.status, response.statusText, errorText);
            throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log(`API data received for ${endpoint}:`, data);
        return data;
        
    } catch (error) {
        console.error(`API Request failed for ${endpoint}:`, error);
        throw error;
    }
}

async function refreshMarketData() {
    console.log('Manually refreshing market data...');
    try {
        const newMarketData = await apiRequest('/api/market-data');
        console.log('Manual refresh - received data:', newMarketData);
        
        if (newMarketData && Array.isArray(newMarketData)) {
            marketData = newMarketData;
            loadMarketTicker();
            loadWatchlist();
            console.log('Manual refresh completed successfully');
        } else {
            console.error('Invalid data received:', newMarketData);
        }
    } catch (error) {
        console.error('Manual refresh failed:', error);
        showError('Failed to refresh market data: ' + error.message);
    }
}

function initializeSentimentAnalyzer() {
  const sentimentForm = document.getElementById('sentimentForm');
  const input = document.getElementById('sentimentTicker');
  const resultArea = document.getElementById('sentimentResult');
  if (!sentimentForm) return;

  sentimentForm.addEventListener('submit', async function(e) {
    e.preventDefault();  // <-- This is critical to prevent page reload
    const symbol = input.value.trim().toUpperCase();
    if (!symbol) return;

    resultArea.innerHTML = 'Analyzing sentiment for ' + symbol + '...';
    try {
      const resp = await fetch(`${API_BASE_URL}/api/sentiment-analysis/?ticker=${symbol}`);
      const data = await resp.json();
      if (!data.success) {
        resultArea.innerHTML = `No sentiment data found for <b>${symbol}</b>: ${data.message || ''}`;
        return;
      }
      // Prepare HTML for sentiment results
      const c = data.sentiment_counts;
      const avg = Number(data.average_score).toFixed(2);
      const alloc = data.allocation_suggestion.allocation || {};
      const headlines = (data.headlines || []).slice(0, 5)
        .map(h => `<li>[${h.label.toUpperCase()} | ${h.score.toFixed(2)}] ${h.text}</li>`)
        .join('');

      resultArea.innerHTML = `
        <strong>${symbol} Sentiment:</strong> 
        <ul>
          <li>Positive: ${c.positive} | Neutral: ${c.neutral} | Negative: ${c.negative}</li>
        </ul>
        <div>Average Sentiment Score: <b>${avg}</b></div>
        <div>Allocation Suggestion: <b>${data.allocation_suggestion.strategy}</b>
          <ul>
            <li>Stocks: ${alloc.stocks}%</li>
            <li>Bonds: ${alloc.bonds}%</li>
            <li>Cash: ${alloc.cash}%</li>
          </ul>
          <em>${data.allocation_suggestion.description || ''}</em>
        </div>
        <div>News Headlines:</div>
        <ul>${headlines}</ul>
      `;
    } catch (error) {
      resultArea.innerHTML = `<span style="color:red">Error analyzing sentiment: ${error}</span>`;
    }
  });
}


// --- MAIN APP LOGIC ---
document.addEventListener('DOMContentLoaded', function() {
    // Initialize DOM elements
    hamburgerBtn = document.getElementById('hamburgerBtn');
    sidebar = document.getElementById('sidebar');
    mainContent = document.getElementById('mainContent');
    themeToggle = document.getElementById('themeToggle');
    chatbotFab = document.getElementById('chatbotFab');
    chatbotModal = document.getElementById('chatbotModal');
    closeChatbot = document.getElementById('closeChatbot');
    loadingScreen = document.getElementById('loadingScreen');
    initializeApp();
    initializeSentimentAnalyzer();
});

function initializeApp() {
    // Show loading screen
    setTimeout(async () => {
        try {
            loadingScreen.classList.add('hidden');
            // Initialize main components
            initializeHamburgerMenu();
            initializeThemeToggle();
            initializeNavigation();
            initializeChatbot();
            initializeVoiceSearch();
            // Load data from API
            await loadAllData();
            // Initialize charts
            initializeCharts();
            // Initialize Mock Trading
            initializeMockTrading();
            // Start real-time updates
            startRealTimeUpdates();
            // Important: Initialize Sentiment Analyzer
            initializeSentimentAnalyzer();
            initializeHeatmap();
        } catch (error) {

        }
    }, 1500);
}

// === FORECASTING ===
async function handleForecastForm(event) {
    event.preventDefault();
    const symbol = document.getElementById('forecastSymbol').value.trim();
    const days = parseInt(document.getElementById('forecastDays').value, 10);
    const currency = document.getElementById('forecastCurrency').value;
    const resultDiv = document.getElementById('forecastResult');
    if (!symbol || isNaN(days) || days < 1) {
        resultDiv.textContent = 'Please fill all required fields correctly.';
        return;
    }
    resultDiv.textContent = 'Generating forecast...';
    try {
        const response = await apiRequest('/api/forecast', {
            method: 'POST',
            body: JSON.stringify({ ticker: symbol, days: days, currency: currency })
        });
        if (
            response.status === "success" &&
            response.results[symbol] &&
            response.results[symbol].forecast
        ) {
            // Plot chart
            displayForecastCandlestick(response.results[symbol].forecast, symbol, "forecastChart");
            // Optionally show table too:
            displayForecastTable(response.results[symbol].forecast, symbol, resultDiv);
        } else {
            resultDiv.textContent = `Failed: ${response.results[symbol]?.message || 'Unknown error'}`;
            // Optionally clear chart:
            Plotly.purge("forecastChart");
        }
    } catch (error) {
        resultDiv.textContent = `Error: ${error.message}`;
        Plotly.purge("forecastChart");
    }
}

function displayForecastTable(forecast, symbol, container) {
    let html = `<h4>${symbol} Forecast (next days)</h4>
<table style="margin: 0 auto; border-collapse: collapse; text-align: center;">
<tr>
  <th>Date</th>
  <th>Open</th>
  <th>High</th>
  <th>Low</th>
  <th>Close</th>
</tr>`;

    const keys = Object.keys(forecast.close || forecast['close']);
    for (let i = Math.max(0, keys.length - 5); i < keys.length; i++) {
        let date = keys[i];
        html += `<tr>
            <td>${date}</td>
            <td>${forecast.open[date].toFixed(2)}</td>
            <td>${forecast.high[date].toFixed(2)}</td>
            <td>${forecast.low[date].toFixed(2)}</td>
            <td>${forecast.close[date].toFixed(2)}</td>
        </tr>`;
    }
    html += '</table>';
    container.innerHTML = html;
}

function displayForecastCandlestick(forecast, symbol, containerId) {
    const ohlc = forecast;
    const dates = Object.keys(ohlc.close || ohlc['close']);
    const open = dates.map(date => ohlc.open[date]);
    const high = dates.map(date => ohlc.high[date]);
    const low = dates.map(date => ohlc.low[date]);
    const close = dates.map(date => ohlc.close[date]);
    const trace = {
        x: dates,
        open: open,
        high: high,
        low: low,
        close: close,
        type: 'candlestick',
        name: symbol,
        increasing: {line: {color: 'green'}},
        decreasing: {line: {color: 'red'}}
    };
    const layout = {
        title: `${symbol} Forecasted Candlestick Chart`,
        xaxis: { title: 'Date' },
        yaxis: { title: 'Price' },
    };
    Plotly.newPlot(containerId, [trace], layout, {responsive: true});
}

document.addEventListener('DOMContentLoaded', function () {
    const forecastForm = document.getElementById('forecastForm');
    if (forecastForm) forecastForm.addEventListener('submit', handleForecastForm);
});

// === DATA LOAD/REFRESH ===
async function loadAllData() {
    console.log('Loading all data from API...');
    try {
        const [portfolioResponse, marketResponse, teamResponse, newsResponse] = await Promise.all([
            apiRequest('/api/portfolio').catch(err => {
                console.error('Portfolio API failed:', err);
                return null;
            }),
            apiRequest('/api/market-data').catch(err => {
                console.error('Market data API failed:', err);
                return null;
            }),
            apiRequest('/api/team').catch(err => {
                console.error('Team API failed:', err);
                return [];
            }),
            apiRequest('/api/news').catch(err => {
                console.error('News API failed:', err);
                return [];
            })
        ]);
        
        // Handle portfolio data
        if (portfolioResponse) {
            portfolioData = portfolioResponse;
            console.log('Portfolio data loaded:', portfolioData);
        } else {
            console.log('Using mock portfolio data');
            portfolioData = {
                totalValue: 125420.50,
                dailyChange: 2840.25,
                dailyChangePercent: 2.32,
                totalReturn: 25420.50,
                totalReturnPercent: 25.42,
                allocation: { stocks: 65.2, bonds: 15.8, crypto: 12.5, cash: 6.5 }
            };
        }
        
        // Handle market data with enhanced debugging
        if (marketResponse && Array.isArray(marketResponse) && marketResponse.length > 0) {
            marketData = marketResponse;
            console.log('Live market data loaded:', marketData.length, 'items');
            console.log('Sample market data:', marketData.slice(0, 2));
        } else {
            console.log('No live market data available, using mock data');
            console.log('Market response was:', marketResponse);
            marketData = [
                {"symbol": "AAPL", "price": 195.84, "change": 2.34, "changePercent": 1.21},
                {"symbol": "GOOGL", "price": 142.56, "change": -1.23, "changePercent": -0.85},
                {"symbol": "MSFT", "price": 378.91, "change": 4.67, "changePercent": 1.25},
                {"symbol": "TSLA", "price": 248.73, "change": -3.21, "changePercent": -1.27},
                {"symbol": "NVDA", "price": 567.12, "change": 12.45, "changePercent": 2.24},
                {"symbol": "BTC-USD", "price": 67234.56, "change": 1823.45, "changePercent": 2.78}
            ];
        }
        
        // Handle team and news data
        teamMembers = teamResponse || [];
        news = newsResponse || [];
        
        // Load UI components
        loadPortfolioData();
        loadMarketTicker();
        loadWatchlist();
        loadTeamMembers();
        loadNews();
        
    } catch (error) {
        console.error('Failed to load data:', error);
        showError('Failed to load some data. Using fallback data.');
        loadMockData();
    }
}

// === MOCK TRADING INITIALIZATION (NEW FUNCTION) ===
function initializeMockTrading() {
    const tradingForm = document.getElementById('trading-form');
    const symbolSelect = document.getElementById('trade-symbol');
    const quantityInput = document.getElementById('trade-quantity');
    const buyBtn = document.getElementById('buy-btn');
    const sellBtn = document.getElementById('sell-btn');
    const tradeMessage = document.getElementById('trade-message');

    if (!tradingForm) {
        console.log('Mock trading form not found, skipping initialization.');
        return;
    }

    // 1. Populate the dropdown with stocks from marketData
    if (marketData && marketData.length > 0) {
        symbolSelect.innerHTML = marketData.map(stock => 
            `<option value="${stock.symbol}">${stock.symbol} - $${stock.price.toFixed(2)}</option>`
        ).join('');
    } else {
        symbolSelect.innerHTML = '<option>No stocks available</option>';
        if(buyBtn) buyBtn.disabled = true;
        if(sellBtn) sellBtn.disabled = true;
    }

    // 2. Helper to display messages
    const displayTradeMessage = (message, type) => {
        if (!tradeMessage) return;
        tradeMessage.textContent = message;
        tradeMessage.className = `trade-message ${type}`; // 'success' or 'error'
        
        // Hide the message after 4 seconds
        setTimeout(() => {
            tradeMessage.style.display = 'none';
        }, 4000);
    };

    // 3. Create a handler function for trades
    const handleTrade = (action) => {
        const symbol = symbolSelect.value;
        const quantity = parseInt(quantityInput.value, 10);

        // --- Validation ---
        if (!symbol || !marketData.length) {
            displayTradeMessage('Please select a valid stock.', 'error');
            return;
        }
        if (isNaN(quantity) || quantity <= 0) {
            displayTradeMessage('Please enter a valid quantity.', 'error');
            return;
        }

        const stock = marketData.find(s => s.symbol === symbol);
        if (!stock) {
            displayTradeMessage('Stock data not found.', 'error');
            return;
        }

        const tradeValue = stock.price * quantity;

        // --- Update Portfolio ---
        if (action === 'buy') {
            portfolioData.totalValue += tradeValue;
            displayTradeMessage(`Successfully bought ${quantity} of ${symbol} for $${tradeValue.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}`, 'success');
        } else if (action === 'sell') {
             if (tradeValue > portfolioData.totalValue) {
                displayTradeMessage(`Cannot sell. Trade value (${tradeValue.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}) exceeds portfolio value.`, 'error');
                return;
            }
            portfolioData.totalValue -= tradeValue;
            displayTradeMessage(`Successfully sold ${quantity} of ${symbol} for $${tradeValue.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}`, 'success');
        }

        // --- Update Dashboard UI ---
        // Re-use the existing function to animate the portfolio value change
        loadPortfolioData(); 

        // Reset form
        quantityInput.value = '';
    };

    // 4. Add event listeners
    if(buyBtn) buyBtn.addEventListener('click', () => handleTrade('buy'));
    if(sellBtn) sellBtn.addEventListener('click', () => handleTrade('sell'));
}


// === ERROR NOTIFICATION ===
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-notification';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ff4757;
        color: white;
        padding: 15px;
        border-radius: 8px;
        z-index: 9999;
        max-width: 300px;
    `;
    document.body.appendChild(errorDiv);
    setTimeout(() => { errorDiv.remove(); }, 5000);
}

// === SIDEBAR ===
function initializeHamburgerMenu() {
    if (!hamburgerBtn || !sidebar || !mainContent) return;
    hamburgerBtn.addEventListener('click', function() {
        hamburgerBtn.classList.toggle('active');
        sidebar.classList.toggle('open');
        if (window.innerWidth <= 1024) {
            if (sidebar.classList.contains('open')) createOverlay();
            else removeOverlay();
        } else mainContent.classList.toggle('sidebar-open');
    });
}
function createOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.5); z-index: 998; backdrop-filter: blur(5px);`;
    overlay.addEventListener('click', closeSidebar);
    document.body.appendChild(overlay);
}
function removeOverlay() {
    const overlay = document.querySelector('.sidebar-overlay');
    if (overlay) overlay.remove();
}
function closeSidebar() {
    if (hamburgerBtn && sidebar && mainContent) {
        hamburgerBtn.classList.remove('active');
        sidebar.classList.remove('open');
        mainContent.classList.remove('sidebar-open');
        removeOverlay();
    }
}







// === THEME TOGGLE ===
function initializeThemeToggle() {
    if (!themeToggle) return;
    const savedTheme = 'light';
    applyTheme(savedTheme);
    themeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-color-scheme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        applyTheme(newTheme);
    });
}
function applyTheme(theme) {
    document.documentElement.setAttribute('data-color-scheme', theme);
    if (themeToggle) themeToggle.classList.toggle('dark-mode', theme === 'dark');
}

// === NAVIGATION ===
function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.section');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const targetSection = this.getAttribute('data-section');
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            sections.forEach(section => {
                section.classList.remove('active');
                section.style.display = 'none';
            });
            const targetElement = document.getElementById(targetSection);
            if (targetElement) {
                targetElement.style.display = 'block';
                setTimeout(() => { targetElement.classList.add('active'); }, 10);
            }
            if (window.innerWidth <= 1024) closeSidebar();
            if (targetSection === 'dashboard' || targetSection === 'analytics') {
                setTimeout(() => { initializeCharts(); }, 300);
            }
        });
    });
}

// === CHATBOT ===
function initializeChatbot() {
    if (!chatbotFab || !chatbotModal || !closeChatbot) return;
    chatbotFab.addEventListener('click', function() {
        chatbotModal.classList.add('open');
    });
    closeChatbot.addEventListener('click', function() {
        chatbotModal.classList.remove('open');
    });
    chatbotModal.addEventListener('click', function(e) {
        if (e.target === chatbotModal) chatbotModal.classList.remove('open');
    });
    const chatInput = document.getElementById('chatInput');
    const sendChat = document.getElementById('sendChat');
    const chatMessages = document.getElementById('chatMessages');
    async function sendMessage() {
        if (!chatInput || !chatMessages) return;
        const message = chatInput.value.trim();
        if (!message) return;
        addChatMessage(message, 'user');
        chatInput.value = '';
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message bot-message typing';
        typingDiv.innerHTML = '<p>AI is thinking...</p>';
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        try {
            const response = await apiRequest('/api/chat', {
                method: 'POST',
                body: JSON.stringify({ message })
            });
            typingDiv.remove();
            addChatMessage(response.response, 'bot');
        } catch (error) {
            typingDiv.remove();
            addChatMessage('Sorry, I encountered an error. Please try again later.', 'bot');
        }
    }
    function addChatMessage(message, sender) {
        if (!chatMessages) return;
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message`;
        messageDiv.innerHTML = `<p>${message}</p>`;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    if (sendChat) sendChat.addEventListener('click', sendMessage);
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    }
}

// === VOICE SEARCH ===
function initializeVoiceSearch() {
    const voiceBtn = document.querySelector('.voice-search-btn');
    if (!voiceBtn) return;
    voiceBtn.addEventListener('click', function() {
        this.style.background = 'linear-gradient(135deg, #1FB8CD, #32b8c8)';
        this.style.color = 'white';
        this.innerHTML = '🎙️';
        setTimeout(() => {
            this.style.background = '';
            this.style.color = '';
            this.innerHTML = '🎤';
            const searchInput = document.querySelector('.search-input');
            if (searchInput) {
                const mockQueries = ['AAPL stock price', 'Bitcoin news', 'Portfolio performance', 'Market trends'];
                searchInput.value = mockQueries[Math.floor(Math.random() * mockQueries.length)];
                searchInput.focus();
            }
        }, 2000);
    });
}

// === PORTFOLIO/TEAM/NEWS UI UPDATES ===
function loadPortfolioData() {
    animateValue('portfolioValue', 0, portfolioData.totalValue, 2000, (v) => `$${v.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`);
    const changeElement = document.getElementById('portfolioChange');
    if (changeElement) {
        const changeAmount = changeElement.querySelector('.change-amount');
        const changePercent = changeElement.querySelector('.change-percent');
        if (changeAmount) animateValue(changeAmount, 0, portfolioData.dailyChange, 2000, (v) => `+$${v.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`);
        if (changePercent) changePercent.textContent = `(+${portfolioData.dailyChangePercent}%)`;
    }
    const totalReturnElement = document.getElementById('totalReturn');
    if (totalReturnElement) animateValue(totalReturnElement, 0, portfolioData.totalReturn, 2000, (v) => `$${v.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`);
}
function animateValue(element, start, end, duration, formatter) {
    const targetElement = typeof element === 'string' ? document.getElementById(element) : element;
    if (!targetElement) return;

    const startValue = parseFloat(targetElement.textContent.replace(/[^0-9.-]+/g,"")) || start;
    const endValue = end;

    const startTime = performance.now();

    function updateValue(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const currentValue = startValue + (endValue - startValue) * easeOutQuart;
        
        if (targetElement) {
            targetElement.textContent = formatter ? formatter(currentValue) : currentValue.toFixed(2);
        }
        if (progress < 1) {
            requestAnimationFrame(updateValue);
        } else {
             if (targetElement) {
                targetElement.textContent = formatter ? formatter(endValue) : endValue.toFixed(2);
            }
        }
    }
    requestAnimationFrame(updateValue);
}
function loadMarketTicker() {
    const tickerContent = document.getElementById('marketTicker');
    if (!tickerContent) {
        console.error('Market ticker element not found');
        return;
    }
    
    console.log('Loading market ticker with data:', marketData);
    
    if (!marketData || marketData.length === 0) {
        console.warn('No market data available for ticker');
        tickerContent.innerHTML = '<div class="ticker-error">No market data available</div>';
        return;
    }
    
    const tickerItems = marketData.map(stock => {
        const symbol = stock.symbol || 'N/A';
        const price = typeof stock.price === 'number' ? stock.price : 0;
        const change = typeof stock.change === 'number' ? stock.change : 0;
        const changePercent = typeof stock.changePercent === 'number' ? stock.changePercent : 0;
        
        const changeClass = change >= 0 ? 'positive' : 'negative';
        const changeSymbol = change >= 0 ? '+' : '';
        
        return `
            <div class="ticker-item">
                <span class="ticker-symbol">${symbol}</span>
                <span class="ticker-price">$${price.toFixed(2)}</span>
         
            </div>
        `;
    }).join('');
    
    tickerContent.innerHTML = tickerItems;
    console.log('Market ticker updated with', marketData.length, 'items');
}
function loadWatchlist() {
    const watchlist = document.getElementById('watchlist');
    if (!watchlist) {
        console.error('Watchlist element not found');
        return;
    }
    
    console.log('Loading watchlist with market data:', marketData);
    
    if (!marketData || marketData.length === 0) {
        console.warn('No market data available for watchlist');
        watchlist.innerHTML = '<div class="watchlist-error">No market data available</div>';
        return;
    }
    

    console.log("Full marketData before slicing:", marketData);
console.log("Length of marketData:", marketData.length);

    
    // Take first 6 items for watchlist display
    const watchlistItems = marketData.slice(0, 6).map(stock => {
        console.log('Processing stock for watchlist:', stock);
        
        // Ensure we have valid data
        const symbol = stock.symbol || 'N/A';
        const price = typeof stock.price === 'number' ? stock.price : 0;
        const change = typeof stock.change === 'number' ? stock.change : 0;
        const changePercent = typeof stock.changePercent === 'number' ? stock.changePercent : 0;
        
        const changeClass = change >= 0 ? 'positive' : 'negative';
        const changeSymbol = change >= 0 ? '+' : '';
        
        return `
            <div class="watchlist-item">
                <div class="watchlist-main">
                    <div class="watchlist-symbol">${symbol}</div>
                    <div class="watchlist-price">$${price.toFixed(2)}</div>
                </div>
               
                </div>
            </div>
        `;
    }).join('');
    
    watchlist.innerHTML = watchlistItems;
    console.log('Watchlist updated with', marketData.slice(0, 6).length, 'items');
}




// === HEATMAP INITIALIZATION ===
function initializeHeatmap() {
    const heatmapDataSource = document.getElementById('heatmapDataSource');
    const heatmapGrouping = document.getElementById('heatmapGrouping');
    const heatmapTheme = document.getElementById('heatmapTheme');
    const heatmapContainer = document.getElementById('tradingHeatmapWidget');
    const heatmapLoading = document.getElementById('heatmapLoading');

    if (!heatmapContainer) {
        console.log('Heatmap container not found');
        return;
    }

    // Function to load heatmap widget
    function loadHeatmapWidget() {
        if (!heatmapContainer) return;
        
        // Show loading
        if (heatmapLoading) heatmapLoading.style.display = 'flex';
        if (heatmapContainer) heatmapContainer.style.display = 'none';

        // Clear existing widget
        const widgetContainer = heatmapContainer.querySelector('.tradingview-widget-container__widget');
        if (widgetContainer) {
            widgetContainer.innerHTML = '';
        }

        // Get current settings
        const dataSource = heatmapDataSource ? heatmapDataSource.value : 'SPX500';
        const grouping = heatmapGrouping ? heatmapGrouping.value : 'sector';
        const theme = heatmapTheme ? heatmapTheme.value : 'light';

        // Create widget configuration
        const widgetConfig = {
            "dataSource": dataSource,
            "blockSize": "market_cap_basic",
            "blockColor": "change",
            "grouping": grouping,
            "blockSizeVisibility": true,
            "blockColorVisibility": true,
            "symbolUrl": "",
            "colorTheme": theme,
            "hasTopBar": false,
            "isDataSetEnabled": true,
            "isZoomEnabled": true,
            "hasSymbolTooltip": true,
            "width": "100%",
            "height": "400",
            "locale": "en"
        };

        // Create script element for TradingView widget
        const script = document.createElement('script');
        script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js';
        script.async = true;
        script.innerHTML = JSON.stringify(widgetConfig);

        // Add script to widget container
        if (widgetContainer) {
            widgetContainer.appendChild(script);
        }

        // Simulate loading delay and show widget
        setTimeout(() => {
            if (heatmapLoading) heatmapLoading.style.display = 'none';
            if (heatmapContainer) heatmapContainer.style.display = 'block';
        }, 2000);
    }

    // Add event listeners for controls
    if (heatmapDataSource) {
        heatmapDataSource.addEventListener('change', loadHeatmapWidget);
    }
    if (heatmapGrouping) {
        heatmapGrouping.addEventListener('change', loadHeatmapWidget);
    }
    if (heatmapTheme) {
        heatmapTheme.addEventListener('change', loadHeatmapWidget);
    }

    // Initial load
    loadHeatmapWidget();
}






function loadTeamMembers() {
    const teamGrid = document.getElementById('teamGrid');
    if (!teamGrid) return;

    const teamCards = teamMembers.map(member => {
        const expertiseTags = member.expertise.map(skill =>
            `<span class="expertise-tag">${skill}</span>`
        ).join('');

        return `
            <div class="card glass-card team-card">
                <div class="team-avatar">
                    <img src="${member.image}" alt="${member.name}" 
                         class="team-photo">
                </div>
                <div class="team-name">${member.name}</div>
                <div class="team-role">${member.role}</div>
                <div class="team-description">${member.description}</div>
                <div class="team-expertise">${expertiseTags}</div>
                <div class="team-linkedin">
                    <a href="${member.linkedin}" target="_blank" title="LinkedIn Profile" class="linkedin-link">
                        <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/linkedin.svg" 
                             alt="LinkedIn" class="linkedin-icon">
                    </a>
                </div>
            </div>
        `;
    }).join('');

    teamGrid.innerHTML = teamCards;
}



async function loadNews() {
    const newsFeed = document.getElementById('newsFeed');
    if (!newsFeed) return;
    try {
        const response = await fetch(`${API_BASE_URL}/api/news`);
        const news = await response.json();
        
        // Debug: Log the news data to see what URLs are being returned
        console.log('News data received:', news);
        news.forEach((article, i) => {
            console.log(`Article ${i}: URL = "${article.url}"`);
        });
        
        const newsItemsHtml = news.map((article, index) => `
          <div class="card glass-card news-item" data-url="${article.url || '#'}" data-index="${index}">
            <div class="news-header">
              <div>
                <div class="news-title">${article.title}</div>
                <div class="news-time">${article.time || ""}</div>
              </div>
              <span class="news-sentiment ${article.sentiment}">${article.sentiment}</span>
            </div>
            <div class="news-summary">${article.summary}</div>
          </div>
        `).join('');
        newsFeed.innerHTML = newsItemsHtml;
        
        // Add click handlers to all news cards
        const newsCards = newsFeed.querySelectorAll('.news-item');
        newsCards.forEach(card => {
            card.style.cursor = 'pointer';
            card.addEventListener('click', function() {
                const url = this.getAttribute('data-url');
                console.log('Clicked URL:', url); // Debug log
                if (url && url !== '#') {
                    window.open(url, '_blank', 'noopener,noreferrer');
                }
            });
        });
    } catch (error) {
        newsFeed.innerHTML = `<div class="news-error">Could not load latest news.</div>`;
        console.error('Error fetching news:', error);
    }
}

// === CHARTS ===
function initializeCharts() {
    if (allocationChart) { allocationChart.destroy(); allocationChart = null; }
    if (performanceChart) { performanceChart.destroy(); performanceChart = null; }
    if (trendsChart) { trendsChart.destroy(); trendsChart = null; }
    // Portfolio Allocation Chart
    const allocationCanvas = document.getElementById('allocationChart');
    if (allocationCanvas && portfolioData.allocation) {
        const allocationCtx = allocationCanvas.getContext('2d');
        allocationChart = new Chart(allocationCtx, {
            type: 'doughnut',
            data: {
                labels: ['Stocks', 'Bonds', 'Crypto', 'Cash'],
                datasets: [{
                    data: [
                        portfolioData.allocation.stocks,
                        portfolioData.allocation.bonds,
                        portfolioData.allocation.crypto,
                        portfolioData.allocation.cash
                    ],
                    backgroundColor: ['#1FB8CD', '#FFC185', '#B4413C', '#ECEBD5'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { usePointStyle: true, padding: 20 }
                    }
                }
            }
        });
    }
    // Performance Chart
    const performanceCanvas = document.getElementById('performanceChart');
    if (performanceCanvas) {
        const performanceCtx = performanceCanvas.getContext('2d');
        const performanceData = Array.from({length: 30}, (_, i) => ({
            x: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000),
            y: 100000 + Math.random() * 30000 + i * 800
        }));
        performanceChart = new Chart(performanceCtx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Portfolio Value',
                    data: performanceData,
                    borderColor: '#1FB8CD',
                    backgroundColor: 'rgba(31, 184, 205, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        }
                    },
                    y: {
                        beginAtZero: false,
                        ticks: { callback: function(value) { return '$' + value.toLocaleString(); } }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
    // Trends Chart
    const trendsCanvas = document.getElementById('trendsChart');
    if (trendsCanvas) {
        const trendsCtx = trendsCanvas.getContext('2d');
        const trendsData = {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Market Trend',
                data: [12, 19, 3, 5, 2, 3],
                borderColor: '#1FB8CD',
                backgroundColor: 'rgba(31, 184, 205, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        };
        trendsChart = new Chart(trendsCtx, {
            type: 'line',
            data: trendsData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
    }
}

// === REAL-TIME ===
function startRealTimeUpdates() {
    console.log('Starting real-time updates...');
    
    // Market data updates every 30 seconds
    const marketUpdateInterval = setInterval(async () => {
        try {
            console.log('Updating market data...');
            const newMarketData = await apiRequest('/api/market-data');
            
            if (newMarketData && Array.isArray(newMarketData) && newMarketData.length > 0) {
                marketData = newMarketData;
                console.log('Market data updated:', marketData.length, 'items');
                loadMarketTicker();
                loadWatchlist();
            } else {
                console.warn('No valid market data received in update');
            }
        } catch (error) {
            console.error('Failed to update market data:', error);
            // Don't show error to user for automatic updates, just log it
        }
    }, 30000); // 30 seconds
    
    // Portfolio data updates every 60 seconds
    const portfolioUpdateInterval = setInterval(async () => {
        try {
            console.log('Updating portfolio data...');
            const newPortfolioData = await apiRequest('/api/portfolio');
            
            if (newPortfolioData) {
                portfolioData = newPortfolioData;
                console.log('Portfolio data updated:', portfolioData);
                loadPortfolioData();
            }
        } catch (error) {
            console.error('Failed to update portfolio data:', error);
        }
    }, 60000); // 60 seconds
    
    // Store intervals so they can be cleared if needed
    window.marketUpdateInterval = marketUpdateInterval;
    window.portfolioUpdateInterval = portfolioUpdateInterval;
}

// === RESPONSIVE ===
window.addEventListener('resize', function() {
    if (window.innerWidth > 1024) {
        removeOverlay();
        if (sidebar && sidebar.classList.contains('open') && mainContent) {
            mainContent.classList.add('sidebar-open');
        }
    } else {
        if (mainContent) mainContent.classList.remove('sidebar-open');
    }
});

document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'b') {
        e.preventDefault(); if (hamburgerBtn) hamburgerBtn.click();
    }
    if (e.ctrlKey && e.key === 't') {
        e.preventDefault(); if (themeToggle) themeToggle.click();
    }
    if (e.ctrlKey && e.code === 'Space') {
        e.preventDefault(); if (chatbotFab) chatbotFab.click();
    }
});

console.log('Portfolio Dashboard Pro initialized successfully! 🚀');








class DashboardStockChart {
            constructor() {
                this.chart = null;
                this.candlestickSeries = null;
                this.currentSymbol = 'AAPL';
                this.currentTimeframe = '1D';
                this.isInitialized = false;

                this.init();
            }

            init() {
                // Wait for DOM and library to load
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', () => this.waitForLibrary(0));
                } else {
                    this.waitForLibrary(0);
                }
            }

            waitForLibrary(attempts) {
                const maxAttempts = 20;

                if (typeof LightweightCharts !== 'undefined') {
                    console.log('Lightweight Charts library loaded successfully');
                    this.setupChart();
                    this.setupEventListeners();
                    this.loadSampleData();
                } else if (attempts < maxAttempts) {
                    setTimeout(() => this.waitForLibrary(attempts + 1), 500);
                } else {
                    this.showError('Chart library failed to load.');
                }
            }

            setupChart() {
                try {
                    const chartContainer = document.getElementById('stockChartContainer');
                    if (!chartContainer) return;

                    chartContainer.innerHTML = '';

                    this.chart = LightweightCharts.createChart(chartContainer, {
                        width: chartContainer.clientWidth,
                        height: 300,
                        layout: {
                            background: { type: 'solid', color: 'transparent' },
                            textColor: 'rgba(255, 255, 255, 0.8)',
                        },
                        grid: {
                            vertLines: { color: 'rgba(255, 255, 255, 0.1)' },
                            horzLines: { color: 'rgba(255, 255, 255, 0.1)' },
                        },
                        crosshair: {
                            mode: LightweightCharts.CrosshairMode.Normal,
                        },
                        rightPriceScale: {
                            borderVisible: false,
                        },
                        timeScale: {
                            borderVisible: false,
                            timeVisible: true,
                            secondsVisible: false,
                        },
                    });

                    this.candlestickSeries = this.chart.addCandlestickSeries({
                        upColor: '#26a69a',
                        downColor: '#ef5350',
                        borderVisible: false,
                        wickUpColor: '#26a69a',
                        wickDownColor: '#ef5350',
                    });

                    // Handle resize
                    window.addEventListener('resize', () => {
                        if (this.chart && chartContainer) {
                            this.chart.applyOptions({ width: chartContainer.clientWidth });
                        }
                    });

                    this.isInitialized = true;

                } catch (error) {
                    console.error('Error setting up chart:', error);
                    this.showError('Error initializing chart: ' + error.message);
                }
            }

            setupEventListeners() {
                const symbolSelect = document.getElementById('stockSymbolSelect');
                const refreshBtn = document.getElementById('refreshStockBtn');
                const timeframeBtns = document.querySelectorAll('.timeframe-btn');

                if (symbolSelect) {
                    symbolSelect.addEventListener('change', (e) => {
                        this.currentSymbol = e.target.value;
                        this.loadSampleData();
                    });
                }

                if (refreshBtn) {
                    refreshBtn.addEventListener('click', () => {
                        this.loadSampleData();
                    });
                }

                timeframeBtns.forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        document.querySelector('.timeframe-btn.active')?.classList.remove('active');
                        e.target.classList.add('active');
                        this.currentTimeframe = e.target.dataset.timeframe;
                        this.loadSampleData();
                    });
                });
            }

            generateSampleData(symbol, timeframe) {
                const basePrice = {
                    'AAPL': 150, 'GOOGL': 120, 'MSFT': 280, 'TSLA': 200, 'AMZN': 130, 'NVDA': 400
                }[symbol] || 150;

                const days = { '1D': 1, '5D': 5, '1M': 30, '3M': 90, '1Y': 365 }[timeframe] || 30;

                const data = [];
                let currentPrice = basePrice;
                const now = new Date();

                for (let i = days; i >= 0; i--) {
                    const date = new Date(now);
                    date.setDate(date.getDate() - i);

                    const volatility = 0.02;
                    const trend = (Math.random() - 0.5) * volatility;
                    const dailyRange = currentPrice * 0.03;

                    const open = currentPrice;
                    const close = open * (1 + trend + (Math.random() - 0.5) * volatility);
                    const high = Math.max(open, close) + Math.random() * dailyRange * 0.5;
                    const low = Math.min(open, close) - Math.random() * dailyRange * 0.5;

                    const timeString = date.toISOString().split('T')[0];

                    data.push({
                        time: timeString,
                        open: parseFloat(open.toFixed(2)),
                        high: parseFloat(high.toFixed(2)),
                        low: parseFloat(low.toFixed(2)),
                        close: parseFloat(close.toFixed(2)),
                    });

                    currentPrice = close;
                }

                return data;
            }

            async loadSampleData() {
                if (!this.isInitialized) return;

                this.showLoading(true);

                try {
                    await new Promise(resolve => setTimeout(resolve, 300));

                    const data = this.generateSampleData(this.currentSymbol, this.currentTimeframe);

                    if (this.candlestickSeries) {
                        this.candlestickSeries.setData(data);

                        if (data.length > 0) {
                            const lastCandle = data[data.length - 1];
                            const previousCandle = data[data.length - 2];
                            this.updateCurrentPrice(lastCandle, previousCandle);
                        }

                        this.chart.timeScale().fitContent();
                    }

                } catch (error) {
                    console.error('Error loading chart data:', error);
                } finally {
                    this.showLoading(false);
                }
            }

            updateCurrentPrice(current, previous) {
                try {
                    const price = current.close;
                    const change = price - (previous ? previous.close : price);
                    const changePercent = previous ? ((change / previous.close) * 100) : 0;

                    const priceEl = document.getElementById('stockCurrentPrice');
                    const changeEl = document.getElementById('stockPriceChange');

                    if (priceEl) priceEl.textContent = `$${price.toFixed(2)}`;

                    if (changeEl) {
                        const changeText = `${change >= 0 ? '+' : ''}$${change.toFixed(2)} (${change >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)`;
                        changeEl.textContent = changeText;
                        changeEl.className = 'price-change ' + (change >= 0 ? 'positive' : 'negative');
                    }
                } catch (error) {
                    console.error('Error updating price display:', error);
                }
            }

            showLoading(show) {
                const loadingEl = document.getElementById('stockChartLoading');
                if (loadingEl) {
                    loadingEl.classList.toggle('show', show);
                }
            }

            showError(message) {
                const chartContainer = document.getElementById('stockChartContainer');
                if (chartContainer) {
                    chartContainer.innerHTML = `<div style="text-align:center;padding:40px;color:rgba(255,255,255,0.6);">${message}</div>`;
                }
                this.showLoading(false);
            }
        }

        // Initialize the stock chart
        let dashboardStockChart;

        // Wait for the page to load completely
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(() => {
                    dashboardStockChart = new DashboardStockChart();
                }, 1000);
            });
        } else {
            setTimeout(() => {
                dashboardStockChart = new DashboardStockChart();
            }, 1000);
        }
// === THREE.JS 3D ENHANCEMENTS ===

class ThreeJSManager {
  constructor() {
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.portfolioScene = null;
    this.portfolioCamera = null;
    this.portfolioRenderer = null;
    this.particles = [];
    this.animationId = null;
    this.portfolioAnimationId = null;
  }

  init() {
    this.initBackgroundScene();
    this.initPortfolio3D();
    this.initFloatingParticles();
    this.startAnimationLoop();
  }

  initBackgroundScene() {
    const canvas = document.getElementById('background-canvas');
    if (!canvas) return;

    // Scene setup
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({ 
      canvas: canvas, 
      alpha: true,
      antialias: true 
    });
    
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setClearColor(0x000000, 0);

    // Create subtle geometric background
    this.createBackgroundGeometry();
    
    this.camera.position.z = 50;
  }

  createBackgroundGeometry() {
    // Create floating geometric shapes
    const geometries = [
      new THREE.IcosahedronGeometry(1, 0),
      new THREE.OctahedronGeometry(1),
      new THREE.TetrahedronGeometry(1)
    ];

    const material = new THREE.MeshBasicMaterial({ 
      color: 0x21808d,
      wireframe: true,
      transparent: true,
      opacity: 0.1
    });

    for (let i = 0; i < 20; i++) {
      const geometry = geometries[Math.floor(Math.random() * geometries.length)];
      const mesh = new THREE.Mesh(geometry, material.clone());
      
      mesh.position.set(
        (Math.random() - 0.5) * 100,
        (Math.random() - 0.5) * 100,
        (Math.random() - 0.5) * 100
      );
      
      mesh.rotation.set(
        Math.random() * Math.PI,
        Math.random() * Math.PI,
        Math.random() * Math.PI
      );
      
      mesh.userData = {
        rotationSpeed: {
          x: (Math.random() - 0.5) * 0.01,
          y: (Math.random() - 0.5) * 0.01,
          z: (Math.random() - 0.5) * 0.01
        }
      };

      this.scene.add(mesh);
    }
  }

  initPortfolio3D() {
    const container = document.getElementById('portfolio-3d-container');
    if (!container) return;

    // Portfolio 3D scene setup
    this.portfolioScene = new THREE.Scene();
    this.portfolioCamera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    this.portfolioRenderer = new THREE.WebGLRenderer({ 
      alpha: true,
      antialias: true 
    });
    
    this.portfolioRenderer.setSize(container.clientWidth, container.clientHeight);
    this.portfolioRenderer.setClearColor(0x000000, 0);
    container.appendChild(this.portfolioRenderer.domElement);

    this.createPortfolioVisualization();
    this.portfolioCamera.position.set(0, 5, 10);
  }

  createPortfolioVisualization() {
    // Create 3D portfolio representation using bars/cylinders
    const portfolioData = [
      { name: 'Stocks', value: 45, color: 0x21808d },
      { name: 'Bonds', value: 25, color: 0x32b8c6 },
      { name: 'Crypto', value: 20, color: 0x1fb8cd },
      { name: 'Cash', value: 10, color: 0x60d9eb }
    ];

    portfolioData.forEach((item, index) => {
      const height = (item.value / 50) * 5; // Scale height
      const geometry = new THREE.CylinderGeometry(0.5, 0.5, height, 8);
      const material = new THREE.MeshLambertMaterial({ 
        color: item.color,
        transparent: true,
        opacity: 0.8 
      });
      
      const cylinder = new THREE.Mesh(geometry, material);
      cylinder.position.x = (index - 1.5) * 2;
      cylinder.position.y = height / 2;
      
      cylinder.userData = {
        originalHeight: height,
        targetHeight: height,
        animationSpeed: 0.02
      };

      this.portfolioScene.add(cylinder);

      // Add floating labels
      this.createFloatingLabel(item.name, cylinder.position.clone().add(new THREE.Vector3(0, height + 1, 0)));
    });

    // Add lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    this.portfolioScene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0x21808d, 0.8);
    directionalLight.position.set(10, 10, 5);
    this.portfolioScene.add(directionalLight);
  }

  createFloatingLabel(text, position) {
    // Create simple geometric representation instead of text
    // This avoids font loading issues and maintains performance
    const geometry = new THREE.SphereGeometry(0.1, 8, 8);
    const material = new THREE.MeshBasicMaterial({ 
      color: 0xffffff,
      transparent: true,
      opacity: 0.8 
    });
    const sphere = new THREE.Mesh(geometry, material);
    sphere.position.copy(position);
    
    sphere.userData = {
      floatSpeed: 0.01,
      floatAmount: 0.5
    };
    
    this.portfolioScene.add(sphere);
  }

  initFloatingParticles() {
    const container = document.getElementById('particles-container');
    if (!container) return;

    // Create floating DOM particles for performance
    for (let i = 0; i < 15; i++) {
      const particle = document.createElement('div');
      particle.style.cssText = `
        position: absolute;
        width: 4px;
        height: 4px;
        background: linear-gradient(45deg, #21808d, #32b8c6);
        border-radius: 50%;
        opacity: 0.6;
        pointer-events: none;
        animation: float-${i % 3} ${5 + Math.random() * 5}s infinite ease-in-out;
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
      `;
      container.appendChild(particle);
    }

    // Add CSS animations for particles
    const style = document.createElement('style');
    style.textContent = `
      @keyframes float-0 {
        0%, 100% { transform: translateY(0px) translateX(0px); }
        25% { transform: translateY(-20px) translateX(10px); }
        50% { transform: translateY(-40px) translateX(-5px); }
        75% { transform: translateY(-20px) translateX(-10px); }
      }
      @keyframes float-1 {
        0%, 100% { transform: translateY(0px) translateX(0px) rotate(0deg); }
        33% { transform: translateY(-30px) translateX(15px) rotate(120deg); }
        66% { transform: translateY(-15px) translateX(-10px) rotate(240deg); }
      }
      @keyframes float-2 {
        0%, 100% { transform: translateY(0px) scale(1); }
        50% { transform: translateY(-25px) scale(1.2); }
      }
    `;
    document.head.appendChild(style);
  }

  startAnimationLoop() {
    const animate = () => {
      this.animationId = requestAnimationFrame(animate);
      
      // Animate background scene
      if (this.scene) {
        this.scene.traverse((object) => {
          if (object.userData.rotationSpeed) {
            object.rotation.x += object.userData.rotationSpeed.x;
            object.rotation.y += object.userData.rotationSpeed.y;
            object.rotation.z += object.userData.rotationSpeed.z;
          }
        });
        
        this.renderer.render(this.scene, this.camera);
      }

      // Animate portfolio scene
      if (this.portfolioScene) {
        this.portfolioScene.traverse((object) => {
          if (object.userData.floatSpeed) {
            object.position.y += Math.sin(Date.now() * object.userData.floatSpeed) * 0.01;
          }
        });
        
        this.portfolioRenderer.render(this.portfolioScene, this.portfolioCamera);
      }
    };
    
    animate();
  }

  handleResize() {
    if (this.camera && this.renderer) {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    const container = document.getElementById('portfolio-3d-container');
    if (container && this.portfolioCamera && this.portfolioRenderer) {
      this.portfolioCamera.aspect = container.clientWidth / container.clientHeight;
      this.portfolioCamera.updateProjectionMatrix();
      this.portfolioRenderer.setSize(container.clientWidth, container.clientHeight);
    }
  }

  destroy() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
    if (this.portfolioAnimationId) {
      cancelAnimationFrame(this.portfolioAnimationId);
    }
  }
}

// Initialize Three.js when the app loads
let threeJSManager = null;

// Add this to your existing DOM loaded event
document.addEventListener('DOMContentLoaded', function() {
  // Your existing DOM loaded code...
  
  // Initialize Three.js after a short delay to ensure all elements are rendered
  setTimeout(() => {
    threeJSManager = new ThreeJSManager();
    threeJSManager.init();
  }, 1000);
});

// Handle window resize
window.addEventListener('resize', () => {
  if (threeJSManager) {
    threeJSManager.handleResize();
  }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (threeJSManager) {
    threeJSManager.destroy();
  }
});
