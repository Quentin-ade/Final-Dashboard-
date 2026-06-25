
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
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════
 
if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "AAPL"
 
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
 
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
    except Exception as e:
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
        
        # Valuation
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
        
        # Risk
        if beta < 0.85:
            risk_score = 1.5
        elif beta <= 1.20:
            risk_score = 1.0
        elif beta <= 1.60:
            risk_score = 0.5
        else:
            risk_score = 0.0
        
        # Multiple
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
 
st.title("🏛️ Sovereign Capital Terminal")
st.markdown("Professional Investment Analysis Dashboard")
 
# Load data
with st.spinner("Loading market data..."):
    df = load_all_stocks()
    indices = fetch_indices()
 
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
 
# Display table without styling (NO background_gradient to avoid matplotlib error)
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
        
        # Sensitivity
        st.markdown("### 🧮 Valuation Sensitivity Analysis")
        st.write("How DCF valuation changes with different assumptions:")
        
        wacc_range = [wacc - 1, wacc, wacc + 1]
        growth_range = [terminal_growth - 0.5, terminal_growth, terminal_growth + 0.5]
        
        sensitivity_data = []
        for w in wacc_range:
            row = {}
            for g in growth_range:
                val = calculate_dcf(fcf, shares, w, g, roe, payout)
                row[f"Growth {g:.1f}%"] = f"${val:,.0f}"
            sensitivity_data.append(row)
        
        sens_df = pd.DataFrame(sensitivity_data, index=[f"WACC {w:.1f}%" for w in wacc_range])
        st.table(sens_df)
 
except Exception as e:
    st.error(f"❌ Error analyzing {st.session_state.active_ticker}: {str(e)}")
 
st.markdown("---")
 
# Portfolio recommendations
st.subheader("💼 Portfolio Recommendations")
 
col1, col2 = st.columns(2)
 
with col1:
    risk = st.selectbox(
        "Select Your Risk Profile:",
        ["🛡️ Conservative", "⚖️ Balanced", "🚀 Aggressive"]
    )
    min_return = st.slider("Minimum Expected Return (%):", 0, 50, 10, 1)
 
with col2:
    if risk == "🛡️ Conservative":
        recs = df[(df["Beta"] <= 1.0) & (df["Upside"] >= min_return)].nlargest(5, "Rating")
        strategy = "Low volatility with stable cash flows"
    elif risk == "⚖️ Balanced":
        recs = df[(df["Beta"] > 0.8) & (df["Beta"] <= 1.3) & (df["Upside"] >= min_return)].nlargest(5, "Upside")
        strategy = "Mix of growth and stability"
    else:
        recs = df[(df["Beta"] > 1.2) & (df["Upside"] >= min_return)].nlargest(5, "Upside")
        strategy = "High growth with higher volatility"
    
    st.info(f"**Strategy:** {strategy}")
 
if not recs.empty:
    rec_display = recs[["Ticker", "Name", "Price", "Upside", "Rating", "Verdict"]].copy()
    rec_display["Price"] = rec_display["Price"].apply(lambda x: f"${x:,.2f}")
    rec_display["Upside"] = rec_display["Upside"].apply(lambda x: f"{x:+.1f}%")
    rec_display["Rating"] = rec_display["Rating"].apply(lambda x: f"{x:.1f}⭐")
    
    st.dataframe(rec_display, use_container_width=True)
else:
    st.warning("⚠️ No stocks match your criteria. Try adjusting the minimum return or risk profile.")
 
st.markdown("---")
st.caption("📌 **Disclaimer:** For educational purposes only. Not financial advice. Always consult with a professional before investing.")
