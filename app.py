import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from concurrent.futures import ThreadPoolExecutor
import warnings
from anthropic import Anthropic
 
warnings.filterwarnings('ignore')
 
# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
 
st.set_page_config(
    page_title="Sovereign Capital Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
st.markdown("""
    <style>
    body { background-color: #0f1419; color: #e2e8f0; }
    h1, h2, h3, h4 { color: #ffffff; font-weight: 700; }
    .chat-message { padding: 10px; margin: 5px 0; border-radius: 5px; }
    .user-message { background-color: #1e40af; text-align: right; }
    .ai-message { background-color: #064e3b; text-align: left; }
    </style>
""", unsafe_allow_html=True)
 
# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
 
STOCK_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL", "AMD",
    "NFLX", "CRM", "ADBE", "CSCO", "INTC", "QCOM", "TXN", "AMAT", "MU", "LRCX",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "V", "MA", "PYPL",
    "BLK", "BX", "KKR", "APO", "SCHW", "AIG", "MET", "PRU", "PGR", "TRV",
    "XOM", "CVX", "COP", "CAT", "GE", "HON", "UNP", "LMT", "RTX", "NOC",
    "BA", "DE", "MMM", "FDX", "UPS", "NSC", "CSX", "EMR",
    "LLY", "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "DHR", "ABT",
    "BMY", "AMGN", "GILD", "ISRG", "VRTX", "REGN", "MDT", "HCA",
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "EL", "CL", "PG",
    "KO", "PEP", "PM", "MO", "MDLZ", "BABA", "PDD"
]
 
# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════
 
if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "AAPL"
 
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
 
if "df" not in st.session_state:
    st.session_state.df = None
 
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
 
# ═══════════════════════════════════════════════════════════════════════════════
# AI CHATBOT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
 
def get_ai_client():
    """Initialize Anthropic client"""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        return Anthropic(api_key=api_key)
    except:
        return None
 
def format_stock_data_for_ai(df, ticker):
    """Format stock data for AI analysis"""
    if df is None or df.empty:
        return "No stock data available"
    
    ticker_data = df[df['Ticker'] == ticker]
    
    if ticker_data.empty:
        return f"No data found for {ticker}"
    
    row = ticker_data.iloc[0]
    
    data_summary = f"""
    Stock: {row['Name']} ({row['Ticker']})
    Sector: {row['Sector']}
    Current Price: ${row['Price']:.2f}
    DCF Intrinsic Value: ${row['DCF_Value']:.2f}
    Upside Potential: {row['Upside']:.1f}%
    Quality Rating: {row['Rating']:.1f}/5.0
    Investment Verdict: {row['Verdict']}
    Beta (Risk): {row['Beta']:.2f}x
    P/E Ratio: {row['PE']:.1f}x
    ROE: {row['ROE']:.2%}
    Payout Ratio: {row['Payout']:.2%}
    Free Cash Flow: ${row['FCF']:,.0f}
    """
    
    return data_summary.strip()
 
def get_ai_response(client, user_message, stock_data_context):
    """Get AI response from Claude"""
    try:
        # Build system prompt
        system_prompt = """You are an expert financial analyst and investment advisor. 
        You have access to real stock data and valuation models. Your role is to:
        
        1. Analyze stocks using fundamental analysis (DCF, P/E ratios, growth metrics)
        2. Provide investment recommendations based on financial metrics
        3. Explain valuation concepts clearly
        4. Help investors understand risk vs reward
        5. Suggest portfolio diversification strategies
        6. Answer questions about the stocks in the database
        
        Always:
        - Base recommendations on data and analysis
        - Explain your reasoning clearly
        - Mention risks alongside opportunities
        - Remind users to do their own research
        - Include specific metrics in your analysis
        
        Today's market context:
        The user has access to 100+ institutional stocks with real-time data and DCF valuations.
        """
        
        # Add conversation history
        messages = []
        
        # Add previous messages
        for msg in st.session_state.chat_history[-10:]:  # Keep last 10 messages
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message with context
        context_message = f"{user_message}\n\n[Stock Data Context]\n{stock_data_context}"
        messages.append({
            "role": "user",
            "content": context_message
        })
        
        # Get response
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )
        
        return response.content[0].text
    except Exception as e:
        return f"Error getting AI response: {str(e)}"
 
# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════════════════════
 
@st.cache_data(ttl=1800)
def fetch_stock_data(symbol):
    """Fetch single stock data"""
    try:
        ticker = yf.Ticker(symbol, session=session)
        info = ticker.info
        
        # Price
        price = info.get('currentPrice')
        if not price:
            price = info.get('navPrice')
        if not price:
            try:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
            except:
                price = None
        
        if not price or price <= 0:
            return None
        
        # Metrics
        fcf = info.get('freeCashflow')
        if not fcf:
            fcf = info.get('operatingCashflow', 0)
            if fcf:
                fcf = fcf * 0.85
        if not fcf:
            fcf = 0
        
        shares = info.get('sharesOutstanding')
        if not shares:
            shares = 1
        
        beta = info.get('beta', 1.0)
        if not beta:
            beta = 1.0
        
        pe = info.get('trailingPE')
        if not pe:
            pe = info.get('forwardPE')
        if not pe:
            pe = 0
        
        roe = info.get('returnOnEquity', 0.12)
        if not roe:
            roe = 0.12
        
        payout = info.get('payoutRatio', 0.20)
        if not payout:
            payout = 0.20
        
        return {
            "Ticker": symbol,
            "Name": info.get('longName', symbol),
            "Sector": info.get('sector', 'Unknown'),
            "Price": float(price),
            "FCF": float(fcf),
            "Shares": float(shares),
            "Beta": float(beta),
            "PE": float(pe),
            "ROE": float(roe),
            "Payout": float(payout)
        }
    except:
        return None
 
@st.cache_data(ttl=1800)
def load_all_stocks():
    """Load all stocks"""
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_stock_data, STOCK_UNIVERSE))
    
    valid_data = [r for r in results if r is not None and r.get('Price', 0) > 0]
    
    if not valid_data:
        return pd.DataFrame()
    
    return pd.DataFrame(valid_data)
 
@st.cache_data(ttl=1800)
def fetch_indices():
    """Fetch market indices"""
    indices = {"S&P 500": "^GSPC", "NASDAQ-100": "^NDX", "FTSE 100": "^FTSE"}
    results = {}
    
    for name, symbol in indices.items():
        try:
            ticker = yf.Ticker(symbol, session=session)
            hist = ticker.history(period="5d")
            if not hist.empty:
                last = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change = ((last - prev) / prev) * 100
                results[name] = (last, change)
        except:
            results[name] = (0, 0)
    
    return results
 
# ═══════════════════════════════════════════════════════════════════════════════
# CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════════
 
def calculate_dcf(fcf, shares, wacc_pct, terminal_growth_pct, roe, payout):
    """Calculate DCF intrinsic value"""
    try:
        wacc = wacc_pct / 100.0
        terminal_g = terminal_growth_pct / 100.0
        
        if wacc <= terminal_g or shares <= 0:
            return 0.0
        
        sustainable_g = max(min(roe * (1 - payout), 0.18), 0.02)
        
        if fcf <= 0:
            fcf = shares * 2.0
        
        pv_fcf = 0
        current_fcf = fcf
        
        for year in range(1, 6):
            growth = sustainable_g - ((sustainable_g - terminal_g) * (year / 5))
            current_fcf = current_fcf * (1 + growth)
            pv_fcf += current_fcf / ((1 + wacc) ** year)
        
        terminal_fcf = current_fcf * (1 + terminal_g)
        terminal_value = terminal_fcf / (wacc - terminal_g)
        pv_terminal = terminal_value / ((1 + wacc) ** 5)
        
        total_value = pv_fcf + pv_terminal
        intrinsic_value = total_value / shares
        
        return max(intrinsic_value, 0)
    except:
        return 0.0
 
def get_rating(price, intrinsic, beta, pe):
    """Calculate rating"""
    try:
        if price <= 0:
            return 1.0, "EXCLUDED", []
        
        mos = ((intrinsic - price) / price) * 100
        
        if mos >= 35:
            val_score = 2.0
        elif mos >= 15:
            val_score = 1.5
        elif mos >= 0:
            val_score = 1.0
        elif mos >= -15:
            val_score = 0.5
        else:
            val_score = 0.0
        
        if beta < 0.85:
            risk_score = 1.5
        elif beta <= 1.20:
            risk_score = 1.0
        elif beta <= 1.60:
            risk_score = 0.5
        else:
            risk_score = 0.0
        
        if pe > 0 and pe <= 16:
            mult_score = 1.5
        elif pe <= 28:
            mult_score = 1.0
        elif pe <= 45:
            mult_score = 0.5
        else:
            mult_score = 0.0
        
        total = val_score + risk_score + mult_score
        rating = max(min(total, 5.0), 1.0)
        
        if rating >= 4.2:
            verdict = "🟢 STRONG BUY"
        elif rating >= 3.4:
            verdict = "🟢 BUY"
        elif rating >= 2.4:
            verdict = "🟡 HOLD"
        else:
            verdict = "🔴 SELL"
        
        reasons = [
            f"Margin of Safety: {mos:.1f}%",
            f"Beta Risk: {beta:.2f}x",
            f"P/E Multiple: {pe:.1f}x"
        ]
        
        return rating, verdict, reasons
    except:
        return 1.0, "ERROR", []
 
# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════
 
with st.sidebar:
    st.title("⚙️ Dashboard Controls")
    
    wacc = st.slider(
        "WACC (%)",
        min_value=4.0,
        max_value=16.0,
        value=8.5,
        step=0.1,
        help="Discount rate for cash flows"
    )
    
    terminal_growth = st.slider(
        "Terminal Growth (%)",
        min_value=0.5,
        max_value=4.5,
        value=2.2,
        step=0.1,
        help="Long-term growth rate"
    )
    
    st.markdown("---")
    st.subheader("🎯 Quick Picks")
    
    col1, col2, col3 = st.columns(3)
    if col1.button("NVDA", use_container_width=True):
        st.session_state.active_ticker = "NVDA"
        st.rerun()
    if col2.button("LLY", use_container_width=True):
        st.session_state.active_ticker = "LLY"
        st.rerun()
    if col3.button("MSFT", use_container_width=True):
        st.session_state.active_ticker = "MSFT"
        st.rerun()
    
    st.markdown("---")
    st.subheader("🔍 Search Stock")
    
    with st.form("search_form"):
        ticker_input = st.text_input(
            "Ticker:",
            value=st.session_state.active_ticker,
            placeholder="AAPL"
        ).upper().strip()
        
        if st.form_submit_button("Search", use_container_width=True):
            if ticker_input:
                st.session_state.active_ticker = ticker_input
                st.rerun()
 
# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
 
st.title("🏛️ Sovereign Capital Terminal + 🤖 AI Advisor")
st.markdown("Professional Investment Analysis Dashboard with AI Stock Recommendations")
 
# Load data
with st.spinner("Loading market data..."):
    df = load_all_stocks()
    indices = fetch_indices()
    st.session_state.df = df
 
if df.empty:
    st.error("❌ Unable to load stock data. Please check your internet connection and try again.")
    st.stop()
 
# Calculate valuations
df["DCF_Value"] = df.apply(
    lambda r: calculate_dcf(r["FCF"], r["Shares"], wacc, terminal_growth, r["ROE"], r["Payout"]),
    axis=1
)
 
df["Upside"] = df.apply(
    lambda r: ((r["DCF_Value"] - r["Price"]) / r["Price"] * 100) if r["Price"] > 0 else 0,
    axis=1
)
 
rating_results = df.apply(
    lambda r: get_rating(r["Price"], r["DCF_Value"], r["Beta"], r["PE"]),
    axis=1
)
 
df["Rating"] = rating_results.apply(lambda x: x[0])
df["Verdict"] = rating_results.apply(lambda x: x[1])
df["Reasons"] = rating_results.apply(lambda x: x[2])
 
# Display indices
st.subheader("📈 Market Overview")
cols = st.columns(len(indices))
for idx, (col, (name, (value, change))) in enumerate(zip(cols, indices.items())):
    col.metric(name, f"{value:,.0f}", f"{change:+.2f}%")
 
st.markdown("---")
 
# Create two columns for main content and chatbot
col_main, col_chat = st.columns([2, 1])
 
with col_main:
    # Stock screening
    st.subheader("🔬 Stock Screening")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        verdicts = st.multiselect(
            "Filter by Verdict:",
            sorted(df["Verdict"].unique()),
            default=sorted(df["Verdict"].unique())
        )
    
    with col2:
        sectors = st.multiselect(
            "Filter by Sector:",
            sorted(df["Sector"].unique()),
            default=sorted(df["Sector"].unique())
        )
    
    with col3:
        min_rating = st.slider("Min Rating:", 1.0, 5.0, 2.0, 0.1)
    
    # Filter
    filtered = df[
        (df["Verdict"].isin(verdicts)) &
        (df["Sector"].isin(sectors)) &
        (df["Rating"] >= min_rating)
    ].sort_values("Upside", ascending=False).copy()
    
    # Display table
    display_df = filtered[["Ticker", "Name", "Sector", "Price", "DCF_Value", "Upside", "Rating", "Verdict", "Beta", "PE"]].copy()
    
    display_df["Price"] = display_df["Price"].apply(lambda x: f"${x:,.2f}")
    display_df["DCF_Value"] = display_df["DCF_Value"].apply(lambda x: f"${x:,.2f}")
    display_df["Upside"] = display_df["Upside"].apply(lambda x: f"{x:+.1f}%")
    display_df["Rating"] = display_df["Rating"].apply(lambda x: f"{x:.1f}⭐")
    display_df["Beta"] = display_df["Beta"].apply(lambda x: f"{x:.2f}x")
    display_df["PE"] = display_df["PE"].apply(lambda x: f"{x:.1f}x")
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    st.markdown("---")
    
    # Deep dive
    st.subheader(f"🔬 Analysis: {st.session_state.active_ticker}")
    
    try:
        ticker = yf.Ticker(st.session_state.active_ticker, session=session)
        hist = ticker.history(period="1y")
        info = ticker.info
        
        if hist.empty:
            st.error(f"❌ No data available for {st.session_state.active_ticker}")
        else:
            price = float(hist['Close'].iloc[-1])
            fcf = info.get('freeCashflow', 0)
            shares = info.get('sharesOutstanding', 1)
            beta = info.get('beta', 1.0)
            pe = info.get('trailingPE', info.get('forwardPE', 0))
            roe = info.get('returnOnEquity', 0.12)
            payout = info.get('payoutRatio', 0.20)
            
            intrinsic = calculate_dcf(fcf, shares, wacc, terminal_growth, roe, payout)
            rating, verdict, reasons = get_rating(price, intrinsic, beta, pe)
            upside = ((intrinsic - price) / price * 100) if price > 0 else 0
            
            # Metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Current Price", f"${price:,.2f}")
            col2.metric("DCF Value", f"${intrinsic:,.2f}")
            col3.metric("Upside", f"{upside:+.1f}%")
            col4.metric("Rating", f"{rating:.1f}⭐")
            col5.metric("Verdict", verdict)
            
            # Position calculator
            st.markdown("### 💰 Position Sizing Calculator")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                shares_buy = st.number_input("Number of Shares:", min_value=1.0, value=100.0, step=10.0)
            
            with col2:
                target_price = st.number_input("Target Price ($):", min_value=0.1, value=float(round(intrinsic, 2)), step=1.0)
            
            cost = shares_buy * price
            terminal = shares_buy * target_price
            roi = ((target_price - price) / price * 100) if price > 0 else 0
            
            with col3:
                st.info(f"**Total Investment:** ${cost:,.2f}\n\n**Terminal Value:** ${terminal:,.2f}\n\n**Expected ROI:** {roi:+.1f}%")
            
            # Chart
            st.markdown("### 📊 Price Chart (1-Year)")
            
            hist['SMA50'] = hist['Close'].rolling(50).mean()
            hist['SMA200'] = hist['Close'].rolling(200).mean()
            
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.08,
                row_heights=[0.7, 0.3]
            )
            
            fig.add_trace(
                go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'],
                    name="Price"
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['SMA50'],
                    name="50-Day MA",
                    line=dict(color='orange', width=2)
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['SMA200'],
                    name="200-Day MA",
                    line=dict(color='red', width=2)
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Bar(
                    x=hist.index,
                    y=hist['Volume'],
                    name="Volume",
                    marker=dict(color='#3b82f6')
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                template="plotly_dark",
                height=500,
                hovermode="x unified",
                xaxis_rangeslider_visible=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Rating details
            st.markdown("### 📋 Investment Rating Details")
            for reason in reasons:
                st.info(f"✓ {reason}")
    
    except Exception as e:
        st.error(f"❌ Error analyzing {st.session_state.active_ticker}: {str(e)}")
 
with col_chat:
    st.subheader("🤖 AI Stock Advisor")
    
    # Check API key
    client = get_ai_client()
    
    if not client:
        st.warning("⚠️ API Key Not Found\n\n1. Get key: https://console.anthropic.com\n2. Create `.streamlit/secrets.toml`\n3. Add: `ANTHROPIC_API_KEY = \"sk-...\"`\n4. Restart app")
    else:
        st.info("✓ AI advisor ready! Ask about stocks below.")
        
        # Chat history display
        with st.container(height=400, border=True):
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**AI:** {message['content']}")
        
        # Chat input
        user_input = st.text_input(
            "Ask about stocks:",
            placeholder="e.g., Should I buy AAPL? Compare NVDA vs MSFT",
            key="chat_input"
        )
        
        if user_input:
            # Get stock context
            ticker = st.session_state.active_ticker
            stock_context = format_stock_data_for_ai(df, ticker)
            
            # Add user message
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Get AI response
            with st.spinner("AI thinking..."):
                ai_response = get_ai_response(client, user_input, stock_context)
            
            # Add AI response
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            st.rerun()
 
st.markdown("---")
st.caption("📌 **Disclaimer:** For educational purposes only. Not financial advice. Always consult with a professional before investing.")
