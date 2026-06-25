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

# ==============================================================================
# 1. PAGE CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="Sovereign Capital Management Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
        background-color: #0f1419;
        color: #e2e8f0;
        scroll-behavior: smooth;
    }
    
    h1, h2, h3, h4, .stSubheader {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: #ffffff;
    }
    
    .premium-card {
        background: linear-gradient(135deg, #1a202c 0%, #111827 100%);
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .premium-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 8px 16px rgba(59, 130, 246, 0.15);
    }
    
    div[data-testid="stMetricValue"] {
        font-family: 'Courier New', monospace;
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #2d3748;
    }
    
    div.stButton > button {
        background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 500;
        transition: all 0.2s ease-in-out !important;
        width: 100%;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(37, 99, 235, 0.3);
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

# ==============================================================================
# 2. INSTITUTIONAL STOCK UNIVERSE (100+ HIGH-LIQUIDITY EQUITIES)
# ==============================================================================
INSTITUTIONAL_UNIVERSE = [
    # Technology & Semiconductors
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL", "AMD",
    "NFLX", "CRM", "ADBE", "CSCO", "INTC", "QCOM", "TXN", "AMAT", "MU", "LRCX",
    "ASML", "PANW", "SNOW", "PLTR", "NOW", "WDAY", "TEAM", "DDOG", "CRWD", "SQ",
    "INTU", "ANET", "MCHP", "MPWR", "NXPI", "KLAC",
    # Financials & Banking
    "JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "V", "MA", "PYPL",
    "BLK", "BX", "KKR", "APO", "SCHW", "AIG", "MET", "PRU", "PGR", "TRV",
    "CB", "MMC", "AON", "AJG", "COF",
    # Energy & Industrials
    "XOM", "CVX", "COP", "CAT", "GE", "HON", "UNP", "LMT", "RTX", "NOC",
    "BA", "DE", "MMM", "FDX", "UPS", "NSC", "CSX", "EMR",
    # Healthcare & Pharma
    "LLY", "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "DHR", "ABT",
    "BMY", "AMGN", "GILD", "ISRG", "VRTX", "REGN", "MDT", "HCA",
    # Consumer & Defensive
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "EL", "CL", "PG",
    "KO", "PEP", "PM", "MO", "MDLZ", "BABA", "PDD"
]

# ==============================================================================
# 3. SESSION STATE INITIALIZATION
# ==============================================================================
if "active_ticker" not in st.session_state:
    st.session_state["active_ticker"] = "AAPL"
if "user_name" not in st.session_state:
    st.session_state["user_name"] = "Investor"

# Setup custom HTTP session
custom_session = requests.Session()
custom_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# ==============================================================================
# 4. DATA FETCHING FUNCTIONS
# ==============================================================================
@st.cache_data(ttl=1800)
def fetch_stock_data(symbol):
    """Fetch comprehensive stock data for a single ticker."""
    try:
        tk = yf.Ticker(symbol, session=custom_session)
        fast = tk.fast_info
        info = tk.info

        # Get price with fallbacks
        price = fast.get('last_price') or info.get('currentPrice') or info.get('navPrice')
        if not price:
            hist = tk.history(period="1d")
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
            else:
                return None

        # Extract financial metrics
        fcf = info.get('freeCashflow') or info.get('operatingCashflow', 0.0) * 0.85
        shares = fast.get('shares') or info.get('sharesOutstanding') or 1.0
        beta = info.get('beta') or 1.0
        pe = info.get('trailingPE') or info.get('forwardPE') or 0.0
        roe = info.get('returnOnEquity') or 0.12
        payout = info.get('payoutRatio') or 0.20
        forward_eps = info.get('forwardEps') or (price / pe if pe > 0 else 1.0)

        return {
            "Ticker": symbol,
            "Name": info.get('longName', symbol),
            "Sector": info.get('sector', 'Global Markets'),
            "Price": float(price),
            "FCF": float(fcf),
            "Shares": float(shares),
            "Beta": float(beta),
            "PE": float(pe),
            "ROE": float(roe),
            "Payout": float(payout),
            "ForwardEPS": float(forward_eps)
        }
    except Exception as e:
        return None

@st.cache_data(ttl=1800)
def compile_universe(ticker_list):
    """Fetch all stock data concurrently."""
    compiled = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        results = executor.map(fetch_stock_data, ticker_list)
        for r in results:
            if r is not None and isinstance(r, dict):
                compiled.append(r)

    if not compiled:
        return pd.DataFrame(columns=[
            "Ticker", "Name", "Sector", "Price", "FCF",
            "Shares", "Beta", "PE", "ROE", "Payout", "ForwardEPS"
        ])

    return pd.DataFrame(compiled)

@st.cache_data(ttl=1800)
def fetch_benchmark_indices():
    """Fetch major market indices."""
    indices = {"S&P 500": "^GSPC", "NASDAQ-100": "^NDX", "FTSE 100": "^FTSE"}
    data = {}
    
    for name, sym in indices.items():
        try:
            tk = yf.Ticker(sym, session=custom_session)
            hist = tk.history(period="5d")
            if not hist.empty:
                close_p = hist['Close'].iloc[-1]
                prev_p = hist['Close'].iloc[-2]
                pct_chg = ((close_p - prev_p) / prev_p) * 100.0
                data[name] = (close_p, pct_chg)
        except Exception:
            data[name] = (0.0, 0.0)
    
    return data

# ==============================================================================
# 5. DCF VALUATION MODEL
# ==============================================================================
def calculate_dcf_intrinsic_value(fcf, shares, wacc_pct, terminal_growth_pct, roe, payout, periods=5):
    """
    Discounted Cash Flow Model
    Args:
        fcf: Free cash flow
        shares: Outstanding shares
        wacc_pct: Weighted average cost of capital (%)
        terminal_growth_pct: Terminal growth rate (%)
        roe: Return on equity
        payout: Payout ratio
        periods: Projection period (years)
    """
    wacc = wacc_pct / 100.0
    g_terminal = terminal_growth_pct / 100.0

    if wacc <= g_terminal:
        return 0.0

    # Fundamental growth rate based on retained earnings
    fundamental_g = max(min(roe * (1 - payout), 0.18), 0.03)

    discounted_fcf_sum = 0.0
    current_fcf = fcf if fcf > 0 else (shares * 2.50)

    # Stage 1: Explicit Projection (5 years)
    for t in range(1, periods + 1):
        # Linear step down toward terminal growth
        growth_factor = fundamental_g - ((fundamental_g - g_terminal) * (t / periods))
        current_fcf *= (1 + growth_factor)
        discounted_fcf_sum += current_fcf / ((1 + wacc) ** t)

    # Stage 2: Terminal Value
    terminal_value = (current_fcf * (1 + g_terminal)) / (wacc - g_terminal)
    discounted_terminal_value = terminal_value / ((1 + wacc) ** periods)

    implied_enterprise_value = discounted_fcf_sum + discounted_terminal_value
    return max(implied_enterprise_value / shares, 0.0)

# ==============================================================================
# 6. RATING SYSTEM
# ==============================================================================
def compute_investment_rating(price, intrinsic, beta, pe):
    """
    Multi-factor investment rating system
    Returns: (rating, verdict, reasoning)
    """
    if price <= 0:
        return 1.0, "EXCLUDED", ["Invalid price data"]

    margin_of_safety = ((intrinsic - price) / price) * 100.0
    score_cards = []

    # Factor 1: Valuation (Max 2.0 points)
    val_pts = 0.0
    if margin_of_safety >= 35.0:
        val_pts = 2.0
    elif margin_of_safety >= 15.0:
        val_pts = 1.5
    elif margin_of_safety >= 0.0:
        val_pts = 1.0
    elif margin_of_safety >= -15.0:
        val_pts = 0.5
    
    score_cards.append(f"Valuation: {margin_of_safety:.1f}% margin of safety â {val_pts} pts")

    # Factor 2: Volatility/Risk (Max 1.5 points)
    risk_pts = 0.0
    if beta < 0.85:
        risk_pts = 1.5
    elif beta <= 1.20:
        risk_pts = 1.0
    elif beta <= 1.60:
        risk_pts = 0.5
    
    score_cards.append(f"Risk (Beta {beta:.2f}x): {risk_pts} pts")

    # Factor 3: P/E Multiple (Max 1.5 points)
    multiple_pts = 0.0
    if 0 < pe <= 16.0:
        multiple_pts = 1.5
    elif 16.0 < pe <= 28.0:
        multiple_pts = 1.0
    elif 28.0 < pe <= 45.0:
        multiple_pts = 0.5
    
    score_cards.append(f"P/E Multiple ({pe:.1f}x): {multiple_pts} pts")

    final_rating = round(val_pts + risk_pts + multiple_pts, 1)
    final_rating = max(min(final_rating, 5.0), 1.0)

    # Investment Verdict
    if final_rating >= 4.2:
        verdict = "ð¢ STRONG BUY"
    elif final_rating >= 3.4:
        verdict = "ð¢ BUY"
    elif final_rating >= 2.4:
        verdict = "ð¡ HOLD"
    else:
        verdict = "ð´ SELL"

    return final_rating, verdict, score_cards

# ==============================================================================
# 7. SIDEBAR CONTROLS
# ==============================================================================
with st.sidebar:
    st.title("âï¸ Dashboard Controls")

    user_name = st.text_input("Your Name:", value=st.session_state["user_name"])
    st.session_state["user_name"] = user_name

    st.markdown("---")
    st.subheader("ð Valuation Parameters")

    wacc_input = st.slider(
        "WACC (Weighted Avg Cost of Capital) %",
        min_value=4.0,
        max_value=16.0,
        value=8.5,
        step=0.1,
        help="Discount rate for future cash flows. Higher = more conservative valuation"
    )

    pgr_input = st.slider(
        "Terminal Growth Rate %",
        min_value=0.5,
        max_value=4.5,
        value=2.2,
        step=0.1,
        help="Long-term perpetual growth rate. Typically matches GDP growth"
    )

    st.markdown("---")
    st.subheader("ð¯ Quick Stock Selection")

    col1, col2, col3 = st.columns(3)
    if col1.button("NVDA", use_container_width=True):
        st.session_state["active_ticker"] = "NVDA"
    if col2.button("LLY", use_container_width=True):
        st.session_state["active_ticker"] = "LLY"
    if col3.button("MSFT", use_container_width=True):
        st.session_state["active_ticker"] = "MSFT"

    st.markdown("---")
    st.subheader("ð Search Stock")

    with st.form(key="search_form"):
        ticker_input = st.text_input(
            "Enter Ticker Symbol:",
            value=st.session_state["active_ticker"],
            placeholder="e.g., AAPL"
        ).upper().strip()
        search_btn = st.form_submit_button("Search", use_container_width=True)

        if search_btn and ticker_input:
            st.session_state["active_ticker"] = ticker_input

# ==============================================================================
# 8. MAIN CONTENT AREA
# ==============================================================================
st.title("ðï¸ Sovereign Capital Management Terminal")
st.markdown(f"Welcome back, **{user_name}**! Let's find your next great investment.")

# Load universe data
with st.spinner("ð¥ Loading market data..."):
    universe_df = compile_universe(INSTITUTIONAL_UNIVERSE)
    benchmark_data = fetch_benchmark_indices()

if universe_df.empty:
    st.error("â Unable to load market data. Please check your internet connection and try again.")
    st.stop()

# ==============================================================================
# 9. DISPLAY MARKET OVERVIEW
# ==============================================================================
st.subheader("ð Market Overview")
b_cols = st.columns(len(benchmark_data))
for idx, (b_name, (b_val, b_chg)) in enumerate(benchmark_data.items()):
    b_cols[idx].metric(
        b_name,
        f"{b_val:,.0f}",
        f"{b_chg:+.2f}%",
        delta_color="normal"
    )

# ==============================================================================
# 10. CALCULATE VALUATIONS FOR ALL STOCKS
# ==============================================================================
master_df = universe_df.copy()

master_df["DCF Intrinsic Value"] = master_df.apply(
    lambda r: calculate_dcf_intrinsic_value(
        r["FCF"], r["Shares"], wacc_input, pgr_input, r["ROE"], r["Payout"]
    ),
    axis=1
)

master_df["Implied Upside %"] = (
    (master_df["DCF Intrinsic Value"] - master_df["Price"]) / master_df["Price"]
) * 100.0

# Calculate ratings
rating_results = master_df.apply(
    lambda r: compute_investment_rating(r["Price"], r["DCF Intrinsic Value"], r["Beta"], r["PE"]),
    axis=1
)

master_df["Rating"] = [p[0] for p in rating_results]
master_df["Verdict"] = [p[1] for p in rating_results]
master_df["Reasoning"] = [p[2] for p in rating_results]

# ==============================================================================
# 11. STOCK SCREENING INTERFACE
# ==============================================================================
st.markdown("---")
st.subheader("ð¬ Stock Screening Tool")

col1, col2, col3 = st.columns(3)

with col1:
    verdict_filter = st.multiselect(
        "Filter by Verdict:",
        options=sorted(master_df["Verdict"].unique()),
        default=sorted(master_df["Verdict"].unique())
    )

with col2:
    sector_filter = st.multiselect(
        "Filter by Sector:",
        options=sorted(master_df["Sector"].unique()),
        default=sorted(master_df["Sector"].unique())
    )

with col3:
    min_rating = st.slider("Minimum Rating:", 1.0, 5.0, 2.0, 0.1)

# Apply filters
filtered_df = master_df[
    (master_df["Verdict"].isin(verdict_filter)) &
    (master_df["Sector"].isin(sector_filter)) &
    (master_df["Rating"] >= min_rating)
].sort_values(by="Implied Upside %", ascending=False)

# Display filtered results
st.dataframe(
    filtered_df[[
        "Ticker", "Name", "Sector", "Price", "DCF Intrinsic Value",
        "Implied Upside %", "Rating", "Verdict", "Beta", "PE"
    ]].style.format({
        "Price": "${:,.2f}",
        "DCF Intrinsic Value": "${:,.2f}",
        "Implied Upside %": "{:+.1f}%",
        "Rating": "{:.1f}â­",
        "Beta": "{:.2f}x",
        "PE": "{:.1f}x"
    }).background_gradient(subset=["Implied Upside %"], cmap="RdYlGn", vmin=-50, vmax=50),
    use_container_width=True,
    height=400
)

# ==============================================================================
# 12. DEEP DIVE ANALYSIS FOR SELECTED STOCK
# ==============================================================================
st.markdown("---")
target = st.session_state["active_ticker"]
st.subheader(f"ð¬ Deep Dive Analysis: {target}")

try:
    target_tk = yf.Ticker(target, session=custom_session)
    history_short = target_tk.history(period="5d", interval="15m")
    history_long = target_tk.history(period="1y")
    target_info = target_tk.info

    if history_long.empty:
        st.error(f"â Could not retrieve data for {target}")
        st.stop()

    # Extract metrics
    spot_price = float(history_short['Close'].iloc[-1]) if not history_short.empty else float(
        history_long['Close'].iloc[-1])
    t_fcf = target_info.get('freeCashflow') or target_info.get('operatingCashflow', 0.0) * 0.85
    t_shares = target_tk.fast_info.get('shares') or target_info.get('sharesOutstanding') or 1.0
    t_beta = target_info.get('beta') or 1.0
    t_pe = target_info.get('trailingPE') or target_info.get('forwardPE') or 0.0
    t_roe = target_info.get('returnOnEquity') or 0.12
    t_payout = target_info.get('payoutRatio') or 0.20

    t_intrinsic = calculate_dcf_intrinsic_value(t_fcf, t_shares, wacc_input, pgr_input, t_roe, t_payout)
    t_rating, t_verdict, t_reasons = compute_investment_rating(spot_price, t_intrinsic, t_beta, t_pe)
    t_upside = ((t_intrinsic - spot_price) / spot_price) * 100.0

    # Display key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Current Price", f"${spot_price:,.2f}")
    col2.metric("DCF Value", f"${t_intrinsic:,.2f}")
    col3.metric("Upside Potential", f"{t_upside:+.1f}%")
    col4.metric("Rating", f"{t_rating:.1f}â­")
    col5.metric("Verdict", t_verdict)

    # Position size calculator
    st.markdown("### ð° Position Sizing Calculator")
    col1, col2, col3 = st.columns(3)

    with col1:
        shares_to_buy = st.number_input(
            "Number of Shares:",
            min_value=1.0,
            value=100.0,
            step=10.0
        )

    with col2:
        target_price = st.number_input(
            "Target Sell Price ($):",
            min_value=0.1,
            value=float(round(t_intrinsic, 2)),
            step=0.5
        )

    # Calculate position metrics
    total_cost = shares_to_buy * spot_price
    terminal_value = shares_to_buy * target_price
    roi = ((target_price - spot_price) / spot_price) * 100.0

    with col3:
        st.markdown(
            f"""
            **Investment Summary:**
            - **Total Investment:** ${total_cost:,.2f}
            - **Potential Return:** ${terminal_value:,.2f}
            - **Expected ROI:** {roi:+.1f}%
            """
        )

    # Chart
    st.markdown("### ð Price Chart & Moving Averages")

    history_long['SMA50'] = history_long['Close'].rolling(window=50).mean()
    history_long['SMA200'] = history_long['Close'].rolling(window=200).mean()

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3]
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=history_long.index,
            open=history_long['Open'],
            high=history_long['High'],
            low=history_long['Low'],
            close=history_long['Close'],
            name="Price"
        ),
        row=1, col=1
    )

    # Moving Averages
    fig.add_trace(
        go.Scatter(x=history_long.index, y=history_long['SMA50'], name="50-MA", line=dict(color='orange', width=1)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=history_long.index, y=history_long['SMA200'], name="200-MA", line=dict(color='red', width=1)),
        row=1, col=1
    )

    # Volume
    fig.add_trace(
        go.Bar(x=history_long.index, y=history_long['Volume'], name="Volume", marker_color='#3b82f6'),
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
    st.markdown("### ð Investment Rating Breakdown")
    for reason in t_reasons:
        st.info(f"â {reason}")

    # Valuation sensitivity
    st.markdown("### ð§® Valuation Sensitivity Analysis")
    st.write("How your DCF valuation changes with different assumptions:")

    wacc_range = [wacc_input - 1.0, wacc_input, wacc_input + 1.0]
    pgr_range = [pgr_input - 0.5, pgr_input, pgr_input + 0.5]

    sensitivity_data = []
    for w in wacc_range:
        row = {}
        for p in pgr_range:
            val = calculate_dcf_intrinsic_value(t_fcf, t_shares, w, p, t_roe, t_payout)
            row[f"{p:.1f}%"] = f"${val:,.2f}"
        sensitivity_data.append(row)

    sensitivity_df = pd.DataFrame(sensitivity_data, index=[f"{w:.1f}%" for w in wacc_range])
    st.table(sensitivity_df)

except Exception as e:
    st.error(f"â Error analyzing {target}: {str(e)}")

# ==============================================================================
# 13. PORTFOLIO RECOMMENDATIONS
# ==============================================================================
st.markdown("---")
st.subheader("ð¼ Portfolio Recommendations")

col1, col2 = st.columns(2)

with col1:
    risk_profile = st.selectbox(
        "Select Your Risk Profile:",
        ["ð¡ï¸ Conservative", "âï¸ Balanced", "ð Aggressive"]
    )

    min_return = st.slider("Minimum Expected Return (%):", 0.0, 50.0, 10.0, 1.0)

with col2:
    if risk_profile == "ð¡ï¸ Conservative":
        rec_df = master_df[
            (master_df["Beta"] <= 1.0) &
            (master_df["Implied Upside %"] >= min_return)
        ].sort_values(by="Rating", ascending=False).head(5)
        strategy_txt = "Low-volatility stocks with stable cash flows and strong downside protection"

    elif risk_profile == "âï¸ Balanced":
        rec_df = master_df[
            (master_df["Beta"] > 0.8) &
            (master_df["Beta"] <= 1.3) &
            (master_df["Implied Upside %"] >= min_return)
        ].sort_values(by="Implied Upside %", ascending=False).head(5)
        strategy_txt = "Mix of growth and stability with reasonable risk-adjusted returns"

    else:  # Aggressive
        rec_df = master_df[
            (master_df["Beta"] > 1.2) &
            (master_df["Implied Upside %"] >= min_return)
        ].sort_values(by="Implied Upside %", ascending=False).head(5)
        strategy_txt = "High-growth potential stocks with higher volatility"

    st.info(f"**Strategy:** {strategy_txt}")

if not rec_df.empty:
    st.dataframe(
        rec_df[["Ticker", "Name", "Price", "Implied Upside %", "Rating", "Verdict"]].style.format({
            "Price": "${:,.2f}",
            "Implied Upside %": "{:+.1f}%",
            "Rating": "{:.1f}â­"
        }),
        use_container_width=True
    )
else:
    st.warning("â ï¸ No stocks match your criteria. Try adjusting the minimum return or risk profile.")

st.markdown("---")
st.caption(
    "ð **Disclaimer:** This tool is for educational purposes only. Always conduct your own research "
    "and consult with a financial advisor before making investment decisions."
)
f)
        st.caption("Strategic Indicator: Review how systemic capital changes or growth shocks alter target valuation profiles.")
else:
    st.warning("⚠️ High Volume Pipeline Warning: Selected asset currently reports structural historical pricing blockages.")
