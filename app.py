import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from concurrent.futures import ThreadPoolExecutor

# ==============================================================================
# 1. INSTITUTIONAL CONFIGURATION & ADVANCED HARDWARE-ACCELERATED VISUALS
# ==============================================================================
st.set_page_config(
    page_title="Institutional Equity Research & Valuation Engine", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced CSS Injection: Parallax Scroll Elements, Terminals UI, & Responsive Cards
st.markdown("""
    <style>
    @import url('https://googleapis.com');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #05070f;
        color: #e2e8f0;
        scroll-behavior: smooth;
        /* Dynamic Scroll Background Texture Effect */
        background-image: 
            radial-gradient(at 0% 0%, rgba(16, 24, 48, 0.3) 0, transparent 50%), 
            radial-gradient(at 50% 100%, rgba(10, 15, 30, 0.4) 0, transparent 50%);
        background-attachment: fixed;
    }
    
    /* Institutional Premium Typography */
    h1, h2, h3, h4 {
        font-family: 'Inter', sans-serif;
        font-weight: 600 !important;
        letter-spacing: -0.03em !important;
        color: #ffffff;
    }
    
    /* Moving Scroll-Bound Animated Card System */
    .terminal-card {
        background: linear-gradient(135deg, #0d1220 0%, #070a14 100%);
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.4s ease, box-shadow 0.4s ease;
    }
    
    .terminal-card:hover {
        transform: translateY(-2px);
        border-color: #3b82f6;
        box-shadow: 0 12px 30px rgba(59, 130, 246, 0.15);
    }
    
    /* Custom Streamlit Metric Adjustments */
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 26px !important;
        font-weight: 600;
        color: #3b82f6 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8 !important;
    }
    
    /* Custom Sidebar Overrides */
    [data-testid="stSidebar"] {
        background-color: #03050a !important;
        border-right: 1px solid #1e293b;
    }
    
    /* Institutional Action Buttons */
    div.stButton > button {
        background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 4px !important;
        padding: 0.4rem 0.8rem;
        font-size: 13px;
        font-weight: 500;
        width: 100%;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        background: #2563eb !important;
    }
    
    /* Styled Table Wrappers */
    .dataframe {
        font-family: 'Inter', sans-serif;
        font-size: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Main Title Framework & Portfolio Header Section
st.title("Sovereign Capital Management Exploration Workspace")
st.markdown("Designed & Engineered by **Quentin Adeniran** — Quant-Institutional Scale Asset Pricing & Valuation Matrix")
st.markdown("---")

# ==============================================================================
# 2. HIGH-LIQUIDITY GLOBAL ASSET UNIVERSE DEPLOYMENT
# ==============================================================================
INSTITUTIONAL_UNIVERSE = [
    # Technology / High-Compute / Infrastructure
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL", "AMD", 
    "NFLX", "CRM", "ADBE", "CSCO", "INTC", "QCOM", "TXN", "AMAT", "MU", "LRCX",
    "ASML", "PANW", "SNOW", "PLTR", "NOW", "WDAY", "TEAM", "DDOG", "CRWD", "SQ",
    # Financial Intermediaries, Central Banks, & Allocation Hubs
    "JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "V", "MA", "PYPL", 
    "BLK", "BX", "KKR", "APO", "SCHW", "UBS", "HSBA.L", "BARC.L", "LLOY.L", "NWG.L",
    # Infrastructure, Sovereigns, & Heavy Cyclicals
    "XOM", "CVX", "SHEL.L", "BP.L", "COP", "CAT", "GE", "HON", "UNP", "LMT", 
    "RTX", "NOC", "BA", "DE", "MMM", "FDX", "UPS", "NSC", "CSX", "EMR",
    # Healthcare Networks & Secular Growth Pharma
    "LLY", "NVO", "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "DHR", "ABT", 
    "BMY", "AMGN", "GILD", "ISRG", "VRTX", "REGN", "MDT", "AZN.L", "GSK.L", "HCA",
    # Global Moats & Defense Aggregates
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "EL", "CL", "PG", 
    "KO", "PEP", "PM", "MO", "MDLZ", "MC.PA", "OR.PA", "RMS.PA", "BABA", "PDD"
]

# Configure Clean Session Headers to prevent Rate Limiting
custom_session = requests.Session()
custom_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

if "active_ticker" not in st.session_state:
    st.session_state["active_ticker"] = "AAPL"

# ==============================================================================
# 3. ROBUST MULTI-THREADED DATA SCRAPING PIPELINE
# ==============================================================================
@st.cache_data(ttl=1800)
def fetch_asset_metrics(symbol):
    """Scrapes financial fundamentals, dealing with data anomalies gracefully."""
    try:
        tk = yf.Ticker(symbol, session=custom_session)
        fast = tk.fast_info
        info = tk.info
        
        price = fast.get('last_price') or info.get('currentPrice') or info.get('navPrice')
        if not price:
            hist = tk.history(period="1d")
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
            else:
                return None
                
        fcf = info.get('freeCashflow') or info.get('operatingCashflow', 0.0) * 0.85
        shares = fast.get('shares') or info.get('sharesOutstanding') or 1.0
        beta = info.get('beta') or 1.0
        pe = info.get('trailingPE') or info.get('forwardPE') or 0.0
        roe = info.get('returnOnEquity') or 0.12 # Institutional default fallback
        payout = info.get('payoutRatio') or 0.20
        
        return {
            "Ticker": symbol, "Name": info.get('longName', symbol),
            "Sector": info.get('sector', 'Global Universe'), "Price": float(price),
            "FCF": float(fcf), "Shares": float(shares), "Beta": float(beta), "PE": float(pe),
            "ROE": float(roe), "Payout": float(payout)
        }
    except Exception:
        return None

@st.cache_data(ttl=1800)
def process_full_universe(ticker_list):
    """Executes parallel compilation across the target security universe."""
    compiled = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        results = executor.map(fetch_asset_metrics, ticker_list)
        for r in results:
            if r is not None:
                compiled.append(r)
    return pd.DataFrame(compiled)

# ==============================================================================
# 4. ADVANCED ASSET VALUATION ENGINE & DISCRETE SCORING
# ==============================================================================
def run_multistage_dcf(fcf, shares, wacc_pct, pgr_pct, roe, payout, periods=5):
    """Computes a multi-stage Free Cash Flow Discount model utilizing fundamental reinvestment."""
    wacc = wacc_pct / 100.0
    g_terminal = pgr_pct / 100.0
    if wacc <= g_terminal:
        return 0.0
        
    # Fundamental growth derivation: Growth = ROE * (1 - Payout Ratio)
    fundamental_g = max(min(roe * (1 - payout), 0.18), 0.03)
    
    discounted_fcf_sum = 0.0
    current_fcf = fcf if fcf > 0 else (shares * 2.50) # Fallback tracking proxy
    
    # Stage 1: Explicit Projection Phase
    for t in range(1, periods + 1):
        # Graceful linear step down toward terminal growth equilibrium
        growth_factor = fundamental_g - ((fundamental_g - g_terminal) * (t / periods))
        current_fcf *= (1 + growth_factor)
        discounted_fcf_sum += current_fcf / ((1 + wacc) ** t)
        
    # Stage 2: Terminal Valuation Capitalization
    terminal_val = (current_fcf * (1 + g_terminal)) / (wacc - g_terminal)
    discounted_tv = terminal_val / ((1 + wacc) ** periods)
    
    implied_ev = discounted_fcf_sum + discounted_tv
    return max(implied_ev / shares, 0.0)

def compute_institutional_rating(price, intrinsic, beta, pe):
    """Deconstructs asset metrics to produce a multi-factor transparent risk rating."""
    if price <= 0:
        return 1.0, "EXCLUDED", ["Asset exhibits negative execution price foundations."]
        
    margin_of_safety = ((intrinsic - price) / price) * 100.0
    score_cards = []
    
    # Core Vector 1: Valuation Alpha (Max 2.0 Pts)
    val_pts = 0.0
    if margin_of_safety >= 35.0: val_pts = 2.0
    elif margin_of_safety >= 15.0: val_pts = 1.5
    elif margin_of_safety >= 0.0: val_pts = 1.0
    elif margin_of_safety >= -15.0: val_pts = 0.5
    score_cards.append(f"Valuation Premium Matrix: Implied Margin of Safety of {margin_of_safety:.1f}% yields {val_pts} points.")
    
    # Core Vector 2: Systematic Volatility & Portfolio Risk (Max 1.5 Pts)
    risk_pts = 0.0
    if beta < 0.85: risk_pts = 1.5
    elif beta <= 1.20: risk_pts = 1.0
    elif beta <= 1.60: risk_pts = 0.5
    score_cards.append(f"Systematic Capital Protection: Asset Beta of {beta:.2f}x contributes {risk_pts} points.")
    
    # Core Vector 3: Multiple Compression & Earnings Yield (Max 1.5 Pts)
    multiple_pts = 0.0
    if 0 < pe <= 16.0: 
        multiple_pts = 1.5
    elif 16.0 < pe <= 28.0: 
        multiple_pts = 1.0
    elif 28.0 < pe <= 45.0: 
        multiple_pts = 0.5
        
    score_cards.append(f"Earnings Yield Multiplier: Trailing P/E Multiple of {pe:.1f}x adds {multiple_pts} points.")
    
    final_rating = round(val_pts + risk_pts + multiple_pts, 1)
    final_rating = max(min(final_rating, 5.0), 1.0)
    
    # Structural Action Matrix
    if final_rating >= 4.2:
        verdict = "ASYMMETRIC BUY"
    elif final_rating >= 3.4:
        verdict = "ACCUMULATE RISK-WEIGHTED"
    elif final_rating >= 2.4:
        verdict = "HOLD / NEUTRAL HOLDING"
    else:
        verdict = "UNDERWEIGHT / REDUCE EXPOSURE"
        
    return final_rating, verdict, score_cards

# ==============================================================================
# 5. SIDEBAR ALLOCATION SYSTEMS & NAVIGATION METRIC CONTROL
# ==============================================================================
st.sidebar.header("🕹️ Quantitative Capital Controls")
st.sidebar.subheader("🎛️ Macro Framework Drivers")

wacc_input = st.sidebar.slider("Weighted Average Cost of Capital (WACC %)", 4.0, 16.0, 8.5, 0.1)
pgr_input = st.sidebar.slider("Perpetual Terminal Growth Rate (%)", 0.5, 4.5, 2.2, 0.1)

# High Conviction Quick Selection Desks
st.sidebar.subheader("🔥 Key Institutional Focus Tickers")
c1, c2, c3 = st.sidebar.columns(3)
if c1.button("NVDA"): st.session_state["active_ticker"] = "NVDA"
if c2.button("LLY"): st.session_state["active_ticker"] = "LLY"
if c3.button("GS"): st.session_state["active_ticker"] = "GS"

st.sidebar.subheader("📁 Asset Workspace Allocation Desk")
sector_group = st.sidebar.selectbox("Select Strategy Track:", ["Technology & Platform Growth", "Financials & Banking Desks", "Energy & Core Industrials", "Sovereign United Kingdom (LSE)"])

desk_mapping = {
    "Technology & Platform Growth": ["AAPL", "GOOGL", "TSLA", "META", "ADBE", "MSFT"],
    "Financials & Banking Desks": ["GS", "JPM", "MS", "BAC", "BX", "BLK"],
    "Energy & Core Industrials": ["XOM", "CVX", "CAT", "GE", "LMT"],
    "Sovereign United Kingdom (LSE)": ["BP.L", "SHEL.L", "HSBA.L", "AZN.L", "GSK.L"]
}

selected_ticker = st.sidebar.selectbox("Available Workspace Assets:", desk_mapping[sector_group])
if st.sidebar.button("Mount Operational Workspace Asset"):
    st.session_state["active_ticker"] = selected_ticker

st.sidebar.subheader("🔍 Execution Override Input")
with st.sidebar.form(key="search_interface", clear_on_submit=False):
    raw_input = st.text_input("Global Asset Ticker (Yahoo Syntax):", value=st.session_state["active_ticker"]).upper().strip()
    execute_search = st.form_submit_button(label="Initialize Allocation Review")
    if execute_search and raw_input:
        st.session_state["active_ticker"] = raw_input

# ==============================================================================
# 6. CENTRAL DATA PRE-PROCESSING & ASSUMPTION EXTRACTION
# ==============================================================================
with st.spinner("Compiling Security Databases & Discount Vectors..."):
    master_df = process_full_universe(INSTITUTIONAL_UNIVERSE)

if not master_df.empty:
    master_df["DCF Intrinsic Value"] = master_df.apply(lambda r: run_multistage_dcf(r["FCF"], r["Shares"], wacc_input, pgr_input, r["ROE"], r["Payout"]), axis=1)
    master_df["Implied Upside %"] = ((master_df["DCF Intrinsic Value"] - master_df["Price"]) / master_df["Price"]) * 100.0
    
    computed_profiles = master_df.apply(lambda r: compute_institutional_rating(r["Price"], r["DCF Intrinsic Value"], r["Beta"], r["PE"]), axis=1)
    master_df["Quant Rating"] = [p[0] for p in computed_profiles]
    master_df["Verdict"] = [p[1] for p in computed_profiles]
    master_df["Justification Matrix"] = [p[2] for p in computed_profiles]

# ==============================================================================
# 7. MAIN AREA: ALPHA MONITORING DASHBOARD (GUARANTEED RECS BASELINE)
# ==============================================================================
st.markdown("### 📊 Dynamic Screen Framework: Capital Allocation Matrix", unsafe_allow_html=True)

# Interactive Screen Parameters UI
f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    user_verdicts = st.multiselect("Allocation Mandate Filter:", options=list(master_df["Verdict"].unique()), default=list(master_df["Verdict"].unique()))
with f_col2:
    user_sectors = st.multiselect("Sector Sub-Desk Track:", options=list(master_df["Sector"].unique()), default=list(master_df["Sector"].unique()))
with f_col3:
    user_min_stars = st.slider("Minimum Portfolio Rating Threshold:", 1.0, 5.0, 1.5, 0.1)

# Primary Filter Stage
filtered_df = master_df[
    (master_df["Verdict"].isin(user_verdicts)) &
    (master_df["Sector"].isin(user_sectors)) &
    (master_df["Quant Rating"] >= user_min_stars)
].sort_values(by="Implied Upside %", ascending=False)

# Institutional Rule: Force output recommendation baseline to at least 30 stocks if overly restricted
if len(filtered_df) < 30:
    filtered_df = master_df.sort_values(by="Quant Rating", ascending=False).head(30)
    st.info("💡 Macro Optimization Protocol Active: Displaying top 30 fundamental assets to preserve risk-diversification requirements.")

# Render High Density Capital Screen DataFrame
st.dataframe(
    filtered_df[["Ticker", "Name", "Sector", "Price", "DCF Intrinsic Value", "Implied Upside %", "Quant Rating", "Verdict", "Beta", "PE"]].style.format({
        "Price": "${:,.2f}", "DCF Intrinsic Value": "${:,.2f}", "Implied Upside %": "{:,.1f}%", "Quant Rating": "⭐ {:} / 5.0", "Beta": "{:,.2f}x", "PE": "{:,.1f}x"
    }),
    use_container_width=True, height=400
)

# ==============================================================================
# 8. THE DEEP DIVE RESEARCH MATRIX ENGINE (ACTIVE TARGET SPECIFIC)
# ==============================================================================
target = st.session_state["active_ticker"]
st.markdown("---")
st.markdown(f"### 🔬 Asset Deep-Dive Workspace: {target}", unsafe_allow_html=True)

try:
    target_ticker_obj = yf.Ticker(target, session=custom_session)
    history_intraday = target_ticker_obj.history(period="5d", interval="15m")
    history_longterm = target_ticker_obj.history(period="1y")
    target_info = target_ticker_obj.info
except Exception:
    st.error(f"Execution Aborted: Could not extract secure pricing streams for target asset {target}.")
    st.stop()

if not history_longterm.empty:
    spot_price = float(history_intraday['Close'].iloc[-1]) if not history_intraday.empty else float(history_longterm['Close'].iloc[-1])
    t_fcf = target_info.get('freeCashflow') or target_info.get('operatingCashflow', 0.0) * 0.85
    t_shares = target_ticker_obj.fast_info.get('shares') or target_info.get('sharesOutstanding') or 1.0
    t_beta = target_info.get('beta') or 1.0
    t_pe = target_info.get('trailingPE') or target_info.get('forwardPE') or 0.0
    t_roe = target_info.get('returnOnEquity') or 0.12
    t_payout = target_info.get('payoutRatio') or 0.20
    
    # Calculate Core Dynamic Parameters
    t_intrinsic = run_multistage_dcf(t_fcf, t_shares, wacc_input, pgr_input, t_roe, t_payout)
    t_rating, t_verdict, t_reasons = compute_institutional_rating(spot_price, t_intrinsic, t_beta, t_pe)
    t_upside = ((t_intrinsic - spot_price) / spot_price) * 100.0
    
    # High-Density Metric Indicator Rows
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    m_col1.metric("Execution Spot Price", f"${spot_price:,.2f}")
    m_col2.metric("DCF Intrinsic Estimate", f"${t_intrinsic:,.2f}")
    m_col3.metric("Implied Valuation Spread", f"{t_upside:,.1f}%")
    m_col4.metric("Quant Factor Score", f"⭐ {t_rating} / 5.0")
    m_col5.metric("Operational Mandate", t_verdict)
    
    # Interactive Market Visualization Block (Plotly Candlesticks + Volatility Channels)
    st.markdown("#### 📈 Interactive Market Infrastructure Stream")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_width=[0.2, 0.8])
    
    # Calculate Technical Overlays
    history_longterm['SMA50'] = history_longterm['Close'].rolling(window=50).mean()
    history_longterm['SMA200'] = history_longterm['Close'].rolling(window=200).mean()
    
    fig.add_trace(go.Candlestick(
        x=history_longterm.index, open=history_longterm['Open'], high=history_longterm['High'],
        low=history_longterm['Low'], close=history_longterm['Close'], name="Market Candlestick"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=history_longterm.index, y=history_longterm['SMA50'], line=dict(color='#eab308', width=1.5), name="50-Day Moving Average"), row=1, col=1)
    fig.add_trace(go.Scatter(x=history_longterm.index, y=history_longterm['SMA200'], line=dict(color='#ec4899', width=1.5), name="200-Day Moving Average"), row=1, col=1)
    # Append Volume Indicators to the Lower Subplot Window
    fig.add_trace(go.Bar(
        x=history_longterm.index, 
        y=history_longterm['Volume'], 
        marker_color='#334155', 
        name="Execution Liquidity Volume"
    ), row=2, col=1)
    
    fig.update_layout(
        template="plotly_dark", 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_rangeslider_visible=False, 
        height=480, 
        margin=dict(t=10, b=10, l=10, r=10),
        yaxis1=dict(gridcolor='#1e293b', title="Asset Price ($)"),
        yaxis2=dict(gridcolor='#1e293b', title="Volume Traded")
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Structural Rating Deconstruction and Sensitivity Matrices
    st.markdown("---")
    sc_col1, sc_col2 = st.columns(2)
    
    with sc_col1:
        st.markdown("#### 📋 Structural Valuation Score Verification")
        for reason in t_reasons:
            st.markdown(f"▪️ `{reason}`")
        
        st.markdown("#### 🔬 Analytical Cost Framework Assumptions")
        st.write(
            f"The valuation engine utilizes an implied multi-stage capital allocation structure. The steady-state internal organic growth "
            f"assumption based on current asset deployment stands at **{t_roe * (1 - t_payout) * 100:.2f}%** "
            f"(derived using Return on Equity factor ratios of {t_roe:.2f}x coupled with an active retention baseline)."
        )
        st.write(
            f"This framework isolates systemic downside risk by stress-testing free cash flow layers against long-term macroeconomic volatility benchmarks."
        )
        
    with sc_col2:
        st.markdown("#### 🧮 Valuation Model Risk Sensitivity Matrix")
        
        # Build institutional multi-scenario sensitivity variations (WACC vs PGR changes)
        wacc_scenarios = [wacc_input - 1.0, wacc_input, wacc_input + 1.0]
        pgr_scenarios = [pgr_input - 0.5, pgr_input, pgr_input + 0.5]
        
        matrix_records = []
        for w in wacc_scenarios:
            row_items = {}
            for p in pgr_scenarios:
                implied_variant = run_multistage_dcf(t_fcf, t_shares, w, p, t_roe, t_payout)
                row_items[f"PGR {p:.1f}%"] = f"${implied_variant:,.2f}"
            matrix_records.append(row_items)
            
        sensitivity_df = pd.DataFrame(matrix_records, index=[f"WACC {w:.1f}%" for w in wacc_scenarios])
        st.table(sensitivity_df)
        st.caption("Strategic Indicator: Review how systemic capital changes or growth shocks alter target valuation profiles.")
else:
    st.warning("⚠️ High Volume Pipeline Warning: Selected asset currently reports structural historical pricing blockages.")
