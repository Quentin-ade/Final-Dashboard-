import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# --- BULLETPROOF FIX: Force Yahoo Finance to accept Streamlit Cloud Server Requests ---
import requests
# Creating a dummy browser header stops Yahoo from blocking the cloud IP
custom_session = requests.Session()
custom_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
})

# 1. Page Configuration and Styling
st.set_page_config(page_title="Institutional Equity Research Dashboard", layout="wide")
st.title("📊 Institutional Equity Research & Automated Valuation Engine")
st.markdown("Developed by **Quentin Adeniran** | Cloud-Hosted Financial Tool")
st.markdown("---")

# 2. Sidebar Configuration for Inputs
st.sidebar.header("🕹️ Control Panel")
ticker_input = st.sidebar.text_input("Enter Ticker Symbol (e.g., AAPL, MSFT, TSLA):", value="AAPL").upper().strip()

# Set up historical date ranges
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=365) # 1 Year of historical data

# 3. Data Fetching Layer with Error Catching
@st.cache_data(ttl=3600)  # Cache data for 1 hour to optimize performance
def fetch_financial_data(ticker):
    try:
        # Pass our custom browser session into yfinance to bypass IP rate limits
        stock = yf.Ticker(ticker, session=custom_session)
        # Verify ticker validity by checking if history is empty
        hist = stock.history(start=start_date, end=end_date)
        if hist.empty:
            return None, None
        return stock, hist
    except Exception:
        return None, None

stock_obj, hist_data = fetch_financial_data(ticker_input)

if stock_obj is None or hist_data is None or hist_data.empty:
    st.error(f"❌ Error: Ticker '{ticker_input}' could not be resolved or returned empty data. Please check the symbol and try again.")
else:
    # Extract structural metadata safely
    try:
        info = stock_obj.info
    except Exception:
        info = {}

    company_name = info.get('longName', ticker_input)
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')
    summary = info.get('longBusinessSummary', 'No summary available.')

    # 4. Top-Level Metric Dashboard (KPI Blocks)
    st.subheader(f"🏢 Corporate Overview: {company_name}")
    st.caption(f"**Sector:** {sector} | **Industry:** {industry}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Extract live data points with safe default fallbacks
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or (hist_data['Close'].iloc[-1] if not hist_data.empty else 0.0)
    target_price = info.get('targetMedianPrice', 0.0)
    pe_ratio = info.get('trailingPE', 0.0)
    forward_pe = info.get('forwardPE', 0.0)
    market_cap = info.get('marketCap', 0.0)

    col1.metric("Current Price", f"${current_price:,.2f}" if current_price else "N/A")
    col2.metric("Target Price (Median)", f"${target_price:,.2f}" if target_price else "N/A")
    col3.metric("Trailing P/E Ratio", f"{pe_ratio:.2f}x" if pe_ratio else "N/A")
    col4.metric("Market Capitalization", f"${market_cap:,.0f}" if market_cap else "N/A")

    st.markdown("---")

    # 5. Core Layout Split: Charting & Algorithmic Analysis
    left_chart_col, right_metrics_col = st.columns(2)

    with left_chart_col:
        st.subheader("📈 1-Year Historical Performance (Close Price)")
        # Plot cleanly using Streamlit's native interactive line chart
        chart_df = hist_data[['Close']].copy()
        st.line_chart(chart_df, height=350)
        
        with st.expander("📝 View Business Description"):
            st.write(summary)

    with right_metrics_col:
        st.subheader("🛡️ Algorithmic Valuation Signals")
        
        # Scoring System
        signals = []
        
        # Signal 1: Valuation Check
        if pe_ratio and forward_pe:
            if forward_pe < pe_ratio:
                signals.append(("✅ Forward Multiples", "Forward P/E is lower than Trailing P/E, signaling projected earnings growth."))
            else:
                signals.append(("⚠️ Valuation Compression", "Forward P/E is higher than Trailing P/E, indicating flat or shrinking earnings expansion."))
        else:
            signals.append(("🟡 Multiples Missing", "Insufficient P/E data available to gauge valuation trajectory lines."))
        
        # Signal 2: Target Analyst Upside Check
        if target_price and current_price:
            upside = ((target_price - current_price) / current_price) * 100
            if upside > 10:
                signals.append(("✅ Consensus Upside", f"Wall Street consensus indicates a {upside:.1f}% potential upside from current levels."))
            elif upside < -5:
                signals.append(("🚨 Consensus Downside", f"Stock trades at a {abs(upside):.1f}% premium above Wall Street median targets."))
            else:
                signals.append(("🟡 Fairly Valued", f"Consensus price target sits within a neutral range ({upside:.1f}% variation)."))

        # Signal 3: Operational Liquidity / Health Check
        quick_ratio = info.get('quickRatio')
        if quick_ratio:
            if quick_ratio >= 1.0:
                signals.append(("✅ Liquidity Cushion", f"Quick Ratio of {quick_ratio:.2f} proves strong short-term liquidity to match liabilities."))
            else:
                signals.append(("⚠️ Working Capital Stress", f"Quick Ratio of {quick_ratio:.2f} falls below 1.0, signaling tight near-term liquidity."))
        else:
            signals.append(("🟡 Liquidity Unreported", "Quick ratio parameters not made available by current financial feeds."))

        # Display compiled execution blocks
        for title, desc in signals:
            st.markdown(f"**{title}**")
            if "✅" in title:
                st.info(desc)
            elif "⚠️" in title or "🟡" in title:
                st.warning(desc)
            else:
                st.error(desc)

    st.markdown("---")
    st.caption("Data provided automatically via Yahoo Finance API wrapper. Real-time updates cached locally.")
