import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests

# 1. Page Configuration & Direct UI Styling
st.set_page_config(page_title="Institutional Equity Research Dashboard", layout="wide")

# Custom Institutional CSS Injector
st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #0b2545; color: white; border-radius: 6px; width: 100%; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: bold; color: #134074; }
    .reportview-container .main .block-container{ padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ AlphaForge: Institutional Equity Research & Valuation Engine")
st.markdown("Designed & Engineered by **Quentin Adeniran** | Cloud-Native Quantitative Architecture")
st.markdown("---")

# Initialize persistent selection via state architecture
if "active_ticker" not in st.session_state:
    st.session_state["active_ticker"] = "AAPL"

# 2. Resilient Live Data Fetching Layer (Bypasses Cloud Server IP Blocks)
custom_session = requests.Session()
custom_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
})

def fetch_institutional_market_data(ticker):
    try:
        stock = yf.Ticker(ticker, session=custom_session)
        hist_live = stock.history(period="5d", interval="15m")
        hist_yearly = stock.history(period="1y")
        
        if hist_yearly.empty:
            return None, None, None
            
        try:
            info = stock.info
            if not info or 'longName' not in info:
                info = {}
        except Exception:
            info = {}
            
        return info, hist_yearly, hist_live
    except Exception:
        return None, None, None

# 3. INTERACTIVE CONTROL PANEL (Sidebar Navigation)
st.sidebar.header("🕹️ Quantitative Controls")

# High-Yield Front Page Recommendations
st.sidebar.subheader("🔥 Top High-Conviction Picks")
rec_col1, rec_col2, rec_col3 = st.sidebar.columns(3)
if rec_col1.button("NVDA", help="Nvidia: Computational Monopolist"):
    st.session_state["active_ticker"] = "NVDA"
if rec_col2.button("MSFT", help="Microsoft: B2B Enterprise Moat"):
    st.session_state["active_ticker"] = "MSFT"
if rec_col3.button("AMZN", help="Amazon: AWS Dominance & Scaled Logistics"):
    st.session_state["active_ticker"] = "AMZN"

# Structured Sector Matrix
st.sidebar.subheader("📁 Sector Specialization Desks")
category = st.sidebar.selectbox("Select Asset Universe:", ["Technology & AI", "Bulge-Bracket Banking", "Energy & Global Infrastructure", "UK Market (FTSE 100)"])

if category == "Technology & AI":
    selected_cat_stock = st.sidebar.selectbox("Asset Select:", ["AAPL", "GOOGL", "TSLA", "META"])
    if st.sidebar.button("Load Tech Matrix"): st.session_state["active_ticker"] = selected_cat_stock
elif category == "Bulge-Bracket Banking":
    selected_cat_stock = st.sidebar.selectbox("Asset Select:", ["GS", "JPM", "MS", "BAC"])
    if st.sidebar.button("Load Banking Desk"): st.session_state["active_ticker"] = selected_cat_stock
elif category == "Energy & Global Infrastructure":
    selected_cat_stock = st.sidebar.selectbox("Asset Select:", ["XOM", "CVX", "CAT", "GE"])
    if st.sidebar.button("Load Infrastructure"): st.session_state["active_ticker"] = selected_cat_stock
elif category == "UK Market (FTSE 100)":
    selected_cat_stock = st.sidebar.selectbox("Asset Select:", ["BP.L", "VOD.L", "HSBA.L", "AZN.L"])
    if st.sidebar.button("Load FTSE Desktop"): st.session_state["active_ticker"] = selected_cat_stock

# Custom Core Search Engine (Binds 'Enter' key execution cleanly)
st.sidebar.subheader("🔍 Universal Asset Search")
with st.sidebar.form(key="search_form", clear_on_submit=False):
    search_input = st.text_input("Input Global Ticker + Press ENTER:", value=st.session_state["active_ticker"]).upper().strip()
    submit_button = st.form_submit_button(label="Execute Research")
    if submit_button and search_input:
        st.session_state["active_ticker"] = search_input

# Advanced User Input Variable Overrides
st.sidebar.subheader("🎛️ Strategic DCF Variables")
user_wacc = st.sidebar.slider("Weighted Average Cost of Capital (WACC %)", min_value=4.0, max_value=15.0, value=8.5, step=0.5)
user_pgr = st.sidebar.slider("Perpetual Growth Rate (%)", min_value=0.5, max_value=4.0, value=2.0, step=0.1)

# Execute Data Integration Layer
current_target_ticker = st.session_state["active_ticker"]
info, hist_data, hist_live = fetch_institutional_market_data(current_target_ticker)

if hist_data is None or hist_data.empty:
    st.error(f"❌ Resolution Mismatch: Ticker '{current_target_ticker}' failed to return data. Ensure correct regional extensions (e.g. .L for London Stock Exchange).")
else:
    # 4. DATA PROCESSING & EXTRACT DATA MATRIX
    company_name = info.get('longName', current_target_ticker)
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')
    summary = info.get('longBusinessSummary', 'No detailed operational prospectus uploaded to public listings feed.')

    # Live spot price logic fallback
    if hist_live is not None and not hist_live.empty:
        live_price = float(hist_live['Close'].iloc[-1])
    else:
        live_price = float(hist_data['Close'].iloc[-1])

    target_price = info.get('targetMedianPrice') or info.get('targetMeanPrice') or 0.0
    pe_ratio = info.get('trailingPE') or 0.0
    market_cap = info.get('marketCap') or 0.0
    beta = info.get('beta') or 1.0
    free_cash_flow = info.get('freeCashflow') or info.get('operatingCashflow', 0.0) * 0.8 # Fallback proxy calculation

    # Active Workspace Meta Banner
    st.subheader(f"🏢 Active Desk Coverage: {company_name} ({current_target_ticker})")
    st.caption(f"**Sector Cluster:** {sector} | **Industry Track:** {industry} | **System Feed Status:** Live, 15m Delayed In-Day")

    # High-Density Metric Dashboard Blocks
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Execution Price", f"${live_price:,.2f}" if live_price > 0 else "N/A")
    m2.metric("Wall St. Target Consensus", f"${target_price:,.2f}" if target_price > 0 else "N/A")
    m3.metric("Trailing P/E Multiple", f"{pe_ratio:.2f}x" if pe_ratio > 0 else "N/A")
    m4.metric("Market Capitalization", f"${market_cap:,.0f}" if market_cap > 0 else "N/A")
    st.markdown("---")

    # 5. INDUSTRIAL BLOCK SPLIT: Analytics vs Valuation Engine
    left_layout, right_layout = st.columns(2)

    with left_layout:
        st.subheader("📈 Quantitative Performance Canvas")
        time_view = st.radio("Toggle Horizon Filter View:", ["1-Year Historical Close", "5-Day High-Density Intraday Portfolio Feed"], horizontal=True)
        
        if time_view == "1-Year Historical Close" or hist_live is None or hist_live.empty:
            st.line_chart(hist_data[['Close']], height=350, use_container_width=True)
            active_df_export = hist_data
        else:
            st.line_chart(hist_live[['Close']], height=350, use_container_width=True)
            active_df_export = hist_live

        # Outperformance Feature 1: Professional CSV Data Exporter Module
        csv_data = active_df_export.to_csv().encode('utf-8')
        st.download_button(
            label="📥 Export Clean Time-Series Data (CSV)",
            data=csv_data,
            file_name=f"{current_target_ticker}_institutional_export.csv",
            mime="text/csv"
        )
        
        with st.expander("📝 View Full Strategic Asset Profile Summary"):
            st.write(summary)

    with right_layout:
        st.subheader("🛡️ Algorithmic Valuation Signals")
        
        # Outperformance Feature 2: Mathematical DCF Intrinsic Value Estimation Model
        # Formula: Intrinsic Value = (FCF * (1 + PGR)) / (WACC - PGR)
        if free_cash_flow and free_cash_flow > 0 and market_cap > 0:
            shares_outstanding = market_cap / live_price
            wacc_decimal = user_wacc / 100
            pgr_decimal = user_pgr / 100
            
            if wacc_decimal > pgr_decimal:
                intrinsic_firm_value = (free_cash_flow * (1 + pgr_decimal)) / (wacc_decimal - pgr_decimal)
                dcf_intrinsic_price = intrinsic_firm_value / shares_outstanding
                dcf_variance = ((dcf_intrinsic_price - live_price) / live_price) * 100
                
                st.markdown(f"**📊 Quantitative DCF Fair Value Output: `${dcf_intrinsic_price:,.2f}`**")
                if dcf_variance > 0:
                    st.success(f"Model indicates asset is currently undervalued by **{dcf_variance:.1f}%** relative to structural cash generation capability.")
                else:
                    st.error(f"Model indicates asset trades at a structural premium of **{abs(dcf_variance):.1f}%** above calculated cash values.")
            else:
                st.warning("Calculation stalled: WACC parameters must remain strictly greater than the Perpetual Growth Rate.")
        else:
            st.markdown("**📊 Quantitative DCF Fair Value Output:**")
            st.info("Intrinsic metrics unmapped: Asset balance sheet registers irregular trailing free cash flow lines.")

        st.markdown("---")
        
        # Signal Generation Logic Pipeline
        signals = []
        forward_pe = info.get('forwardPE', 0.0)

        # Signal 1: Beta Risk Mapping (Market Volatility Factor)
        if beta:
            if beta > 1.2:
                signals.append(("🚨 High Systematic Risk Profile", f"Asset Beta sits at {beta:.2f}. Expect heightened volatility relative to broader market indexing movements."))
            elif beta < 0.8:
                signals.append(("✅ Defensive Hedging Asset", f"Asset Beta registers at {beta:.2f}. Demonstrates non-correlated resilience profiles ideal for volatility mitigation."))
            else:
