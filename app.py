import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import requests
from concurrent.futures import ThreadPoolExecutor

# 1. PAGE CONFIGURATION & ARCHITECTURAL VISUAL STYLING
st.set_page_config(page_title="Institutional Equity Research Terminal", layout="wide")

# High-Performance UI Theme & CSS Injection (Animations + Cards)
st.markdown("""
    <style>
    @import url('https://googleapis.com');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d1117;
        color: #c9d1d9;
        scroll-behavior: smooth;
    }
    
    /* Institutional Premium Typography */
    h1, h2, h3, .stSubheader {
        font-family: 'Inter', sans-serif;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    
    /* Fade-in Scroll Animation for Cards */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animated-card {
        animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
        background: linear-gradient(145deg, #161b22, #0f141c);
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }
    
    .animated-card:hover {
        transform: translateY(-4px);
        border-color: #58a6ff;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }
    
    /* Streamlit Metric Overrides */
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 28px !important;
        font-weight: 700;
        color: #58a6ff !important;
    }
    
    /* Sidebar Overrides */
    .css-1cpxqw2, [data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid #21262d;
    }
    
    /* Interactive Button Animations */
    div.stButton > button {
        background: linear-gradient(180deg, #1f6feb 0%, #10529b 100%) !important;
        color: #ffffff !important;
        border: 1px solid #388bfd !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 12px rgba(56, 139, 253, 0.4);
        background: #1f6feb !important;
    }
    
    /* Dataframe view customizations */
    .dataframe {
        border-collapse: collapse;
        font-size: 13px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Quentin Adeniran: Sovereign Equity Research & Valuation Engine")
st.markdown("Designed & Engineered by **Quentin Adeniran** | Quant-Institutional Scale Risk Modeling")
st.markdown("---")

# Global Session Instantiation
custom_session = requests.Session()
custom_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
})

# State initialization
if "active_ticker" not in st.session_state:
    st.session_state["active_ticker"] = "AAPL"

# 2. DEFINITIVE ASSET UNIVERSE DEPLOYMENT (100+ High-Liquidity Global Tickers)
INSTITUTIONAL_UNIVERSE = [
    # Technology / Infrastructure / Software
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL", "AMD", 
    "NFLX", "CRM", "ADBE", "CSCO", "INTC", "QCOM", "TXN", "AMAT", "MU", "LRCX",
    "ASML", "PANW", "SNOW", "PLTR", "NOW", "WDAY", "TEAM", "DDOG", "CRWD", "SQ",
    # Financial Clusters & Global Networks
    "JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "V", "MA", "PYPL", 
    "BLK", "BX", "KKR", "APO", "SCHW", "UBS", "HSBA.L", "BARC.L", "LLOY.L", "NWG.L",
    # Energy, Defense & Global Industrials
    "XOM", "CVX", "SHEL.L", "BP.L", "COP", "CAT", "GE", "HON", "UNP", "LMT", 
    "RTX", "NOC", "BA", "DE", "MMM", "FEDEX", "UPS", "NSC", "CSX", "EMR",
    # Healthcare & Secular Growth Pharma
    "LLY", "NVO", "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "DHR", "ABT", 
    "BMY", "AMGN", "GILD", "ISRG", "VRTX", "REGN", "MDT", "AZN.L", "GSK.L", "HCA",
    # Consumer Discretionary & Defensive Moats
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "EL", "CL", "PG", 
    "KO", "PEP", "PM", "MO", "MDLZ", "MC.PA", "OR.PA", "RMS.PA", "BABA", "PDD"
]

# 3. HIGH-SPEED PARALLEL MULTI-THREAD DATA PIPELINE
@st.cache_data(ttl=1800)
def process_single_asset_metrics(symbol):
    try:
        tk = yf.Ticker(symbol, session=custom_session)
        # Pull light framework profile metrics efficiently
        fast_info = tk.fast_info
        info = tk.info
        
        live_p = fast_info.get('last_price') or info.get('currentPrice') or info.get('navPrice')
        if not live_p:
            hist = tk.history(period="1d")
            if not font_size: # Fallback to history check
                pass
            if not hist.empty:
                live_p = float(hist['Close'].iloc[-1])
            else:
                return None
        
        fcf = info.get('freeCashflow') or info.get('operatingCashflow', 0.0) * 0.8
        shares = fast_info.get('shares') or info.get('sharesOutstanding') or 1.0
        beta = info.get('beta') or 1.0
        pe = info.get('trailingPE') or 0.0
        name = info.get('longName', symbol)
        sector = info.get('sector', 'Global Universe')
        
        return {
            "Ticker": symbol, "Name": name, "Sector": sector, "Price": live_p,
            "FCF": fcf, "Shares": shares, "Beta": beta, "PE": pe,
            "ConsensusTarget": info.get('targetMedianPrice') or info.get('targetMeanPrice') or live_p
        }
    except Exception:
        return None

@st.cache_data(ttl=1800)
def batch_compile_institutional_universe(ticker_list):
    compiled = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(process_single_asset_metrics, ticker_list)
        for r in results:
            if r is not None:
                compiled.append(r)
    return pd.DataFrame(compiled)

# 4. QUANTITATIVE MODELING FUNCTIONS (DCF, Star Rating, Assessment Logic)
def evaluate_intrinsic_dcf(fcf, shares, wacc_pct, pgr_pct, projection_years=5):
    wacc = wacc_pct / 100.0
    g = pgr_pct / 100.0
    if wacc <= g: 
        return 0.0
        
    # Baseline growth assumption step down structure
    growth_rates = [0.12, 0.10, 0.08, 0.07, 0.06]
    projected_fcf = []
    current_fcf = fcf if fcf > 0 else 500000000.0 # Institutional proxy floor
    
    # Discrete projection interval
    for year in range(projection_years):
        current_fcf *= (1 + growth_rates[year])
        discount_factor = (1 + wacc) ** (year + 1)
        projected_fcf.append(current_fcf / discount_factor)
        
    # Terminal phase capitalisation
    terminal_value = (current_fcf * (1 + g)) / (wacc - g)
    discountED_terminal_value = terminal_value / ((1 + wacc) ** projection_years)
    
    enterprise_value = sum(projected_fcf) + discountED_terminal_value
    implied_per_share = enterprise_value / shares
    return max(implied_per_share, 0.0)

def generate_investment_allocation_profile(price, intrinsic_value, beta, pe):
    if price <= 0:
        return 0.0, "Execution Exception", "CRITICAL ERROR"
        
    upside_pct = ((intrinsic_value - price) / price) * 100.0
    
    # Quintessential Multivariable Allocation Score Engine
    base_score = 2.5
    # Margin of Safety modifiers
    if upside_pct > 40: base_score += 1.5
    elif upside_pct > 15: base_score += 0.8
    elif upside_pct < -10: base_score -= 1.5
    elif upside_pct < 0: base_score -= 0.5
    
    # Financial risk adjustments
    if beta > 1.5: base_score -= 0.4
    if beta < 0.9: base_score += 0.3
    if 0 < pe < 15: base_score += 0.4
    elif pe > 45: base_score -= 0.5
    
    star_rating = round(min(max(base_score, 0.0), 5.0), 1)
    
    # Structural Verdict matrix
    if star_rating >= 4.2:
        verdict = "STRONG ALLOCATION"
        rationale = "Asymmetrical margin of safety with robust underlying free cash flow yield relative to cost of capital."
    elif star_rating >= 3.4:
        verdict = "REASONABLE BLENDED RISK"
        rationale = "Value expansion target matches systemic capital costs. Construct position standard risk-weighting."
    elif star_rating >= 2.3:
        verdict = "HOLD / NEUTRAL HOLDING"
        rationale = "Asset priced near operational efficiency equilibrium. Lacks compelling capital expansion delta."
    else:
        verdict = "SPECULATIVE / RISK EXPOSURE"
        rationale = "Potential terminal value compression or premium pricing over-extension. Avoid long-side exposure."
        
    return star_rating, verdict, rationale

# 5. SIDEBAR NAVIGATION & VARIABLE SYSTEM INTERACTION
st.sidebar.header("🕹️ Quantitative Capital Controls")

st.sidebar.subheader("🎛️ Macro Model Adjustments")
user_wacc = st.sidebar.slider("Weighted Average Cost of Capital (WACC %)", min_value=4.0, max_value=15.0, value=8.5, step=0.1)
user_pgr = st.sidebar.slider("Perpetual Growth Rate (%)", min_value=0.5, max_value=4.0, value=2.2, step=0.1)

st.sidebar.subheader("🔥 Top High-Conviction Alpha Desks")
rec_col1, rec_col2, rec_col3 = st.sidebar.columns(3)
if rec_col1.button("NVDA", help="Nvidia Computational Monopolist"): st.session_state["active_ticker"] = "NVDA"
if rec_col2.button("LLY", help="Eli Lilly Structural Pharma Moat"): st.session_state["active_ticker"] = "LLY"
if rec_col3.button("CPNG", help="Coupang Regional Logistics Consolidation"): st.session_state["active_ticker"] = "CPNG"

# Interactive Desk Selection Matrix
st.sidebar.subheader("📁 Asset Universe Segregation")
category = st.sidebar.selectbox("Select Desk Stream:", ["Technology & Generative AI", "Bulge-Bracket Banking Desk", "Energy & Heavy Infrastructure", "UK Markets (LSE)"])

if category == "Technology & Generative AI":
    selected_cat_stock = st.sidebar.selectbox("Asset Select:", ["AAPL", "GOOGL", "TSLA", "META", "ADBE", "INTU"])
    if st.sidebar.button("Load Sector Pipeline"): 
        st.session_state["active_ticker"] = selected_cat_stock
elif category == "Bulge-Bracket Banking Desk":
    selected_cat_stock = st.sidebar.selectbox("Asset Select:", ["GS", "JPM", "MS", "BAC", "BX", "BLK"])
    if st.sidebar.button("Load Banking Workspace"): 
        st.session_state["active_ticker"] = selected_cat_stock
elif category == "Energy & Heavy Infrastructure":
    selected_cat_stock = st.sidebar.selectbox("Asset Select:", ["XOM", "CVX", "CAT", "GE", "DE"])
    if st.sidebar.button("Load Infrastructure Workspace"): 
        st.session_state["active_ticker"] = selected_cat_stock
elif category == "UK Markets (LSE)":
    selected_cat_stock = st.sidebar.selectbox("Asset Select:", ["BP.L", "SHEL.L", "HSBA.L", "AZN.L", "GSK.L"])
    if st.sidebar.button("Load Sovereign EMEA Desk"): 
        st.session_state["active_ticker"] = selected_cat_stock

st.sidebar.subheader("🔍 Custom Execution Query")
with st.sidebar.form(key="search_form", clear_on_submit=False):
    search_input = st.text_input("Input Global Ticker (Yahoo Code Structure):", value=st.session_state["active_ticker"]).upper().strip()
    submit_button = st.form_submit_button(label="Execute Engine Matrix")
    if submit_button and search_input:
        st.session_state["active_ticker"] = search_input

# 6. PIPELINE PROCESSING WORKFLOW
with st.spinner("Compiling Sovereign Institutional Datasets & Valuation Vectors..."):
    universe_df = batch_compile_institutional_universe(INSTITUTIONAL_UNIVERSE)

# Compute Model Outputs across the compiled universe array
if not universe_df.empty:
    universe_df["DCF Intrinsic Price"] = universe_df.apply(
        lambda r: evaluate_intrinsic_dcf(r["FCF"], r["Shares"], user_wacc, user_pgr), axis=1
    )
    universe_df["Model Upside %"] = ((universe_df["DCF Intrinsic Price"] - universe_df["Price"]) / universe_df["Price"]) * 100.0
    
    ratings_outputs = universe_df.apply(
        lambda r: generate_investment_allocation_profile(r["Price"], r["DCF Intrinsic Price"], r["Beta"], r["PE"]), axis=1
    )
    
    # Map raw lists safely from multivariable generator
    universe_df["Star Rating"] = [ro[0] for ro in ratings_outputs]
    universe_df["Strategic Verdict"] = [ro[1] for ro in ratings_outputs]
    universe_df["Analytical Rationale"] = [ro[2] for ro in ratings_outputs]

# 7. MAIN INTERACTIVE MONITOR DISPLAY LAYOUT
st.markdown("<div class='animated-card'><h3>⚡ Sovereign Alpha Matrix Terminal (100+ Enterprise List)</h3></div>", unsafe_allow_html=True)

# Profitability Filtering Segment Layout
filter_c1, filter_c2, filter_c3 = st.columns(3)
with filter_c1:
    verdict_filter = st.multiselect("Filter by Hedge Fund Allocation Strategy:", options=list(universe_df["Strategic Verdict"].unique()), default=list(universe_df["Strategic Verdict"].unique()))
with filter_c2:
    min_stars = st.slider("Minimum Portfolio Star Allocation:", 0.0, 5.0, 1.5, 0.1)
with filter_c3:
    sector_filter = st.multiselect("Filter Global Sector Desk:", options=list(universe_df["Sector"].unique()), default=list(universe_df["Sector"].unique()))

# Apply filters
filtered_universe = universe_df[
    (universe_df["Strategic Verdict"].isin(verdict_filter)) &
    (universe_df["Star Rating"] >= min_stars) &
    (universe_df["Sector"].isin(sector_filter))
].sort_values(by="Model Upside %", ascending=False)

# Render Custom Analytical View Pipeline Display
st.dataframe(
    filtered_universe[["Ticker", "Name", "Sector", "Price", "DCF Intrinsic Price", "Model Upside %", "Star Rating", "Strategic Verdict", "Beta", "PE"]].style.format({
        "Price": "${:,.2f}", "DCF Intrinsic Price": "${:,.2f}", "Model Upside %": "{:,.1f}%", "Star Rating": "⭐ {:} / 5.0", "Beta": "{:,.2f}x", "PE": "{:,.1f}x"
    }),
    use_container_width=True, height=380
)

# 8. SINGULAR TARGET DEEP DIVE RESEARCH MATRIX VIEW
current_target_ticker = st.session_state["active_ticker"]
st.markdown(f"---")
st.markdown(f"<div class='animated-card'><h2>📊 Deep-Dive Quantitative Analysis Desk: {current_target_ticker}</h2></div>", unsafe_allow_html=True)

try:
    stock_obj = yf.Ticker(current_target_ticker, session=custom_session)
    hist_live = stock_obj.history(period="5d", interval="15m")
    hist_yearly = stock_obj.history(period="1y")
    info_dict = stock_obj.info
except Exception:
    st.error(f"Failed loading metrics deep dive for target symbol {current_target_ticker}.")
    st.stop()

if not hist_yearly.empty:
    target_live_p = float(hist_live['Close'].iloc[-1]) if not hist_live.empty else float(hist_yearly['Close'].iloc[-1])
    target_fcf = info_dict.get('freeCashflow') or info_dict.get('operatingCashflow', 0.0) * 0.8
    target_shares = stock_obj.fast_info.get('shares') or info_dict.get('sharesOutstanding') or 1.0
    target_beta = info_dict.get('beta') or 1.0
    target_pe = info_dict.get('trailingPE') or 0.0
    
    # Calculate Singular DCF Outputs
    target_dcf_val = evaluate_intrinsic_dcf(target_fcf, target_shares, user_wacc, user_pgr)
    target_star, target_verdict, target_rationale = generate_investment_allocation_profile(target_live_p, target_dcf_val, target_beta, target_pe)
    
    # High Density Metric Display Row
    metric_cols = st.columns(5)
    metric_cols.metric("Spot Execution Price", f"${target_live_p:,.2f}")
    metric_cols.metric("DCF Intrinsic Fair Price", f"${target_dcf_val:,.2f}")
    metric_cols.metric("Model Variance Implied Delta", f"{((target_dcf_val - target_live_p)/target_live_p)*100:,.1f}%")
    metric_cols.metric("Hedge Fund Star Allocation", f"{target_star} / 5.0 Stars")
    metric_cols.metric("Trailing Valuation Multiplier", f"{target_pe:.1f}x" if target_pe > 0 else "N/A")
    
    # Comprehensive Strategy Summary Card Section
    st.markdown(f"""
    <div class='animated-card'>
        <h4 style='color:#58a6ff; margin-top:0;'>🛡️ Execution Profile Verdict: {target_verdict}</h4>
        <p style='font-size:15px; line-height:1.6;'><b>Institutional Risk Assessment Context:</b> {target_rationale}</p>
        <p style='font-size:12px; color:#8b949e;'>Model Parameters Deployed: WACC={user_wacc}% | Perpetual Growth Rate (g)={user_pgr}% | Historical System Trailing Risk Beta Coefficient={target_beta}x</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Split Layout for Technical Graphics and Executive Summary Text
    canvas_left, canvas_right = st.columns(2)
    with canvas_left:
        st.subheader("📈 Time Series Close Value Visual Grid")
        time_frame = st.radio("Toggle Metric Visualization Frame Horizon:", ["1-Year Historical Close Track", "5-Day High-Density Intraday Stream"], horizontal=True)
        if time_frame == "1-Year Historical Close Track" or hist_live.empty:
            st.line_chart(hist_yearly[['Close']], height=320, use_container_width=True)
            export_df_node = hist_yearly
        else:
            st.line_chart(hist_live[['Close']], height=320, use_container_width=True)
            export_df_node = hist_live
            
        csv_bin = export_df_node.to_csv().encode('utf-8')
        st.download_button(
            label="📥 Export Frame Time-Series Grid (CSV)", data=csv_bin,
            file_name=f"{current_target_ticker}_institutional_export.csv", mime="text/csv"
        )
        
    with canvas_right:
        st.subheader("📋 Executive Strategic Asset Overview Projections")
        st.write(info_dict.get('longBusinessSummary', 'No asset prospectus metadata structural file synchronized with public data endpoints.'))
else:
    st.error("System Resolution Mismatch: Selected execution asset vector timed out. Re-evaluate parameters or modify ticker target structure context.")
