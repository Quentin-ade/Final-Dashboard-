import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from concurrent.futures import ThreadPoolExecutor
import warnings
 
warnings.filterwarnings('ignore')
 
# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
 
st.set_page_config(
    page_title="Sovereign Capital Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
# Custom styling
st.markdown("""
    <style>
    body {
        background-color: #0f1419;
        color: #e2e8f0;
    }
    h1, h2, h3, h4 {
        color: #ffffff;
        font-weight: 700;
    }
    .metric-box {
        background: #1a202c;
        border-left: 3px solid #3b82f6;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
    }
    </style>
""", unsafe_allow_html=True)
 
# Stock universe
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
 
# Session state initialization
if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "AAPL"
if "universe_data" not in st.session_state:
    st.session_data = None
 
# HTTP session
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
 
# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
 
@st.cache_data(ttl=1800)
def fetch_stock_data(symbol):
    """Fetch stock data safely with fallbacks"""
    try:
        ticker = yf.Ticker(symbol, session=session)
        info = ticker.info
        fast_info = ticker.fast_info
        
        # Get price with multiple fallbacks
        price = None
        if 'currentPrice' in info:
            price = info['currentPrice']
        elif 'navPrice' in info:
            price = info['navPrice']
        elif hasattr(fast_info, 'get'):
            price = fast_info.get('last_price')
        
        if not price:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
            else:
                return None
        
        # Extract metrics with safe defaults
        fcf = info.get('freeCashflow') or info.get('operatingCashflow', 0) * 0.85
        shares = info.get('sharesOutstanding', 1)
        beta = info.get('beta', 1.0)
        pe = info.get('trailingPE') or info.get('forwardPE', 0)
        roe = info.get('returnOnEquity', 0.12)
        payout = info.get('payoutRatio', 0.20)
        
        return {
            "Ticker": symbol,
            "Name": info.get('longName', symbol),
            "Sector": info.get('sector', 'Unknown'),
            "Price": float(price) if price else 0,
            "FCF": float(fcf) if fcf else 0,
            "Shares": float(shares) if shares else 1,
            "Beta": float(beta) if beta else 1.0,
            "PE": float(pe) if pe else 0,
            "ROE": float(roe) if roe else 0.12,
            "Payout": float(payout) if payout else 0.20
        }
    except:
        return None
 
@st.cache_data(ttl=1800)
def load_all_stocks():
    """Load all stocks in parallel"""
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_stock_data, STOCK_UNIVERSE))
    
    valid_data = [r for r in results if r and r['Price'] > 0]
    
    if not valid_data:
        return pd.DataFrame()
    
    return pd.DataFrame(valid_data)
 
@st.cache_data(ttl=1800)
def fetch_indices():
    """Fetch market indices"""
    indices = {
        "S&P 500": "^GSPC",
        "NASDAQ-100": "^NDX",
        "FTSE 100": "^FTSE"
    }
    
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
 
def calculate_dcf(fcf, shares, wacc_pct, terminal_growth_pct, roe, payout):
    """Calculate DCF intrinsic value"""
    wacc = wacc_pct / 100.0
    terminal_g = terminal_growth_pct / 100.0
    
    if wacc <= terminal_g or shares <= 0:
        return 0.0
    
    # Sustainable growth rate
    sustainable_g = max(min(roe * (1 - payout), 0.18), 0.02)
    
    # Use minimum FCF if zero
    if fcf <= 0:
        fcf = shares * 2.0
    
    # Project 5 years
    pv_fcf = 0
    current_fcf = fcf
    
    for year in range(1, 6):
        growth = sustainable_g - ((sustainable_g - terminal_g) * (year / 5))
        current_fcf = current_fcf * (1 + growth)
        pv_fcf += current_fcf / ((1 + wacc) ** year)
    
    # Terminal value
    terminal_fcf = current_fcf * (1 + terminal_g)
    terminal_value = terminal_fcf / (wacc - terminal_g)
    pv_terminal = terminal_value / ((1 + wacc) ** 5)
    
    total_value = pv_fcf + pv_terminal
    intrinsic_value = total_value / shares
    
    return max(intrinsic_value, 0)
 
def get_rating(price, intrinsic, beta, pe):
    """Calculate investment rating (1-5 stars)"""
    if price <= 0:
        return 1.0, "EXCLUDED", []
    
    mos = ((intrinsic - price) / price) * 100
    
    # Valuation score (max 2.0)
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
    
    # Risk score (max 1.5)
    if beta < 0.85:
        risk_score = 1.5
    elif beta <= 1.20:
        risk_score = 1.0
    elif beta <= 1.60:
        risk_score = 0.5
    else:
        risk_score = 0.0
    
    # Multiple score (max 1.5)
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
        f"Beta: {beta:.2f}x",
        f"P/E Ratio: {pe:.1f}x"
    ]
    
    return rating, verdict, reasons
 
# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
 
with st.sidebar:
    st.title("⚙️ Controls")
    
    wacc = st.slider(
        "WACC (%)",
        4.0, 16.0, 8.5, 0.1,
        help="Discount rate for cash flows"
    )
    
    terminal_growth = st.slider(
        "Terminal Growth (%)",
        0.5, 4.5, 2.2, 0.1,
        help="Long-term growth rate"
    )
    
    st.markdown("---")
    st.subheader("🎯 Quick Picks")
    
    col1, col2, col3 = st.columns(3)
    if col1.button("NVDA", use_container_width=True):
        st.session_state.active_ticker = "NVDA"
    if col2.button("LLY", use_container_width=True):
        st.session_state.active_ticker = "LLY"
    if col3.button("MSFT", use_container_width=True):
        st.session_state.active_ticker = "MSFT"
    
    st.markdown("---")
    st.subheader("🔍 Search Stock")
    
    with st.form("search_form"):
        ticker_input = st.text_input(
            "Ticker:",
            st.session_state.active_ticker,
            placeholder="AAPL"
        ).upper().strip()
        if st.form_submit_button("Search", use_container_width=True):
            if ticker_input:
                st.session_state.active_ticker = ticker_input
 
# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
 
st.title("🏛️ Sovereign Capital Terminal")
st.markdown("Professional investment analysis dashboard")
 
# Load data
with st.spinner("Loading market data..."):
    df = load_all_stocks()
    indices = fetch_indices()
 
if df.empty:
    st.error("❌ Unable to load stock data. Check internet connection.")
    st.stop()
 
# Add calculations
df["DCF_Value"] = df.apply(
    lambda r: calculate_dcf(r["FCF"], r["Shares"], wacc, terminal_growth, r["ROE"], r["Payout"]),
    axis=1
)
 
df["Upside_%"] = ((df["DCF_Value"] - df["Price"]) / df["Price"] * 100).round(2)
 
rating_data = df.apply(
    lambda r: get_rating(r["Price"], r["DCF_Value"], r["Beta"], r["PE"]),
    axis=1
)
 
df["Rating"] = rating_data.apply(lambda x: x[0])
df["Verdict"] = rating_data.apply(lambda x: x[1])
 
# Display indices
st.subheader("📈 Market Overview")
cols = st.columns(len(indices))
for col, (name, (value, change)) in zip(cols, indices.items()):
    col.metric(name, f"{value:,.0f}", f"{change:+.2f}%")
 
st.markdown("---")
 
# Screening
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
 
# Filter data
filtered = df[
    (df["Verdict"].isin(verdicts)) &
    (df["Sector"].isin(sectors)) &
    (df["Rating"] >= min_rating)
].sort_values("Upside_%", ascending=False)
 
# Display table
st.dataframe(
    filtered[[
        "Ticker", "Name", "Sector", "Price", "DCF_Value",
        "Upside_%", "Rating", "Verdict", "Beta", "PE"
    ]].style.format({
        "Price": "${:,.2f}",
        "DCF_Value": "${:,.2f}",
        "Upside_%": "{:+.1f}%",
        "Rating": "{:.1f}⭐",
        "Beta": "{:.2f}x",
        "PE": "{:.1f}x"
    }).background_gradient(
        subset=["Upside_%"],
        cmap="RdYlGn",
        vmin=-50,
        vmax=50
    ),
    use_container_width=True,
    height=400
)
 
st.markdown("---")
 
# Deep dive
st.subheader(f"🔬 Analysis: {st.session_state.active_ticker}")
 
try:
    ticker = yf.Ticker(st.session_state.active_ticker, session=session)
    hist = ticker.history(period="1y")
    info = ticker.info
    
    if hist.empty:
        st.error(f"No data for {st.session_state.active_ticker}")
    else:
        # Get latest price
        price = float(hist['Close'].iloc[-1])
        
        # Get metrics
        fcf = info.get('freeCashflow', 0)
        shares = info.get('sharesOutstanding', 1)
        beta = info.get('beta', 1.0)
        pe = info.get('trailingPE', 0)
        roe = info.get('returnOnEquity', 0.12)
        payout = info.get('payoutRatio', 0.20)
        
        # Calculate DCF
        intrinsic = calculate_dcf(fcf, shares, wacc, terminal_growth, roe, payout)
        rating, verdict, reasons = get_rating(price, intrinsic, beta, pe)
        upside = ((intrinsic - price) / price * 100) if price > 0 else 0
        
        # Display metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Current Price", f"${price:,.2f}")
        col2.metric("DCF Value", f"${intrinsic:,.2f}")
        col3.metric("Upside", f"{upside:+.1f}%")
        col4.metric("Rating", f"{rating:.1f}⭐")
        col5.metric("Verdict", verdict)
        
        # Position calculator
        st.markdown("### 💰 Position Sizing")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            shares_buy = st.number_input("Shares:", 1, 10000, 100, 10)
        
        with col2:
            target = st.number_input("Target Price ($):", 0.01, 1000.0, float(round(intrinsic, 2)), 1.0)
        
        with col3:
            cost = shares_buy * price
            terminal = shares_buy * target
            roi = ((target - price) / price * 100) if price > 0 else 0
            
            st.markdown(f"""
            **Investment:**
            - Total Cost: ${cost:,.2f}
            - Terminal Value: ${terminal:,.2f}
            - Expected ROI: {roi:+.1f}%
            """)
        
        # Chart
        st.markdown("### 📊 Price Chart")
        
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
                name="50-MA",
                line=dict(color='orange')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['SMA200'],
                name="200-MA",
                line=dict(color='red')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=hist.index, y=hist['Volume'], name="Volume", marker_color='#3b82f6'),
            row=2, col=1
        )
        
        fig.update_layout(
            template="plotly_dark",
            height=500,
            hovermode="x unified",
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Rating breakdown
        st.markdown("### 📋 Rating Details")
        for reason in reasons:
            st.info(f"✓ {reason}")
        
        # Sensitivity
        st.markdown("### 🧮 Sensitivity Analysis")
        st.write("How valuation changes with different assumptions:")
        
        wacc_range = [wacc - 1, wacc, wacc + 1]
        growth_range = [terminal_growth - 0.5, terminal_growth, terminal_growth + 0.5]
        
        sensitivity_data = []
        for w in wacc_range:
            row = {}
            for g in growth_range:
                val = calculate_dcf(fcf, shares, w, g, roe, payout)
                row[f"G:{g:.1f}%"] = f"${val:,.0f}"
            sensitivity_data.append(row)
        
        sens_df = pd.DataFrame(sensitivity_data, index=[f"W:{w:.1f}%" for w in wacc_range])
        st.table(sens_df)
 
except Exception as e:
    st.error(f"Error: {str(e)}")
 
st.markdown("---")
 
# Portfolio recommendations
st.subheader("💼 Recommendations")
 
col1, col2 = st.columns(2)
 
with col1:
    risk = st.selectbox(
        "Risk Profile:",
        ["🛡️ Conservative", "⚖️ Balanced", "🚀 Aggressive"]
    )
    min_return = st.slider("Min Return (%):", 0, 50, 10, 1)
 
with col2:
    if risk == "🛡️ Conservative":
        recs = df[(df["Beta"] <= 1.0) & (df["Upside_%"] >= min_return)].nlargest(5, "Rating")
        strategy = "Low volatility with stable cash flows"
    elif risk == "⚖️ Balanced":
        recs = df[(df["Beta"] > 0.8) & (df["Beta"] <= 1.3) & (df["Upside_%"] >= min_return)].nlargest(5, "Upside_%")
        strategy = "Mix of growth and stability"
    else:
        recs = df[(df["Beta"] > 1.2) & (df["Upside_%"] >= min_return)].nlargest(5, "Upside_%")
        strategy = "High growth with higher volatility"
    
    st.info(f"**Strategy:** {strategy}")
 
if not recs.empty:
    st.dataframe(
        recs[["Ticker", "Name", "Price", "Upside_%", "Rating", "Verdict"]].style.format({
            "Price": "${:,.2f}",
            "Upside_%": "{:+.1f}%",
            "Rating": "{:.1f}⭐"
        }),
        use_container_width=True
    )
else:
    st.warning("No stocks match criteria. Adjust filters.")
 
st.markdown("---")
st.caption("📌 Disclaimer: For educational purposes only. Not financial advice. Always consult a professional.")
