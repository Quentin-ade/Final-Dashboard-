"""
Equity Research & Portfolio Analytics Terminal - Quentin Adeniran
------------------------------------------------
A single-file Streamlit application providing institutional-style
equity evaluation: live pricing, technical charts, fundamental
valuation, a lightweight DCF, and multi-asset portfolio analytics.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots

# --------------------------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Equity Research Terminal - Quentin Adeniran",
    page_icon="\U0001F4C8",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# GLOBAL STYLE — Goldman-style navy / ivory / gold palette
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=Inter:wght@400;500;600;700&display=swap');

    :root{
        --navy:#0B1F3A;
        --navy-2:#132A4D;
        --gold:#B7893F;
        --gold-soft:#D9B876;
        --ivory:#F7F5F0;
        --ink:#101826;
        --muted:#5B6472;
        --pos:#1E7A46;
        --neg:#B3261E;
        --line:#E4E0D6;
    }
    html, body, [class*="css"]{
        font-family:'Inter', sans-serif;
    }
    .stApp{
        background:var(--ivory);
    }
    section[data-testid="stSidebar"]{
        background:var(--navy);
    }
    section[data-testid="stSidebar"] *{
        color:#EDEFF3 !important;
    }
    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stNumberInput input{
        color:#101826 !important;
    }

    /* Header banner */
    .terminal-header{
        background:linear-gradient(120deg, var(--navy) 0%, var(--navy-2) 100%);
        border-radius:10px;
        padding:28px 34px;
        margin-bottom:22px;
        box-shadow:0 8px 24px rgba(11,31,58,0.25);
    }
    .terminal-header h1{
        font-family:'Source Serif 4', serif;
        color:#FBF9F3;
        font-size:32px;
        font-weight:700;
        margin:0 0 4px;
        letter-spacing:.01em;
    }
    .terminal-header p{
        color:var(--gold-soft);
        font-family:'Inter', sans-serif;
        font-size:13.5px;
        letter-spacing:.14em;
        text-transform:uppercase;
        margin:0;
    }

    /* KPI cards */
    .kpi-card{
        background:#FFFFFF;
        border:1px solid var(--line);
        border-left:4px solid var(--gold);
        border-radius:8px;
        padding:16px 18px;
        box-shadow:0 1px 2px rgba(16,24,38,0.04);
        height:100%;
    }
    .kpi-label{
        font-size:11px;
        letter-spacing:.1em;
        text-transform:uppercase;
        color:var(--muted);
        margin-bottom:6px;
    }
    .kpi-value{
        font-family:'Source Serif 4', serif;
        font-size:24px;
        font-weight:700;
        color:var(--ink);
    }
    .kpi-delta-pos{color:var(--pos); font-weight:600; font-size:13.5px;}
    .kpi-delta-neg{color:var(--neg); font-weight:600; font-size:13.5px;}

    /* Section titles */
    .section-title{
        font-family:'Source Serif 4', serif;
        font-size:20px;
        font-weight:700;
        color:var(--navy);
        border-bottom:2px solid var(--gold);
        padding-bottom:6px;
        margin:26px 0 14px;
    }

    .verdict-box{
        border-radius:8px;
        padding:18px 22px;
        font-size:14.5px;
        line-height:1.55;
        border:1px solid var(--line);
        background:#FFFFFF;
    }

    .stTabs [data-baseweb="tab-list"]{gap:6px;}
    .stTabs [data-baseweb="tab"]{
        background:#FFFFFF;
        border:1px solid var(--line);
        border-radius:6px 6px 0 0;
        padding:10px 18px;
        font-weight:600;
        color:var(--navy);
    }
    .stTabs [aria-selected="true"]{
        background:var(--navy) !important;
        color:#F7F5F0 !important;
    }

    footer{visibility:hidden;}
    #MainMenu{visibility:hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_TEMPLATE = "plotly_white"
NAVY = "#0B1F3A"
GOLD = "#B7893F"
POS = "#1E7A46"
NEG = "#B3261E"
GREY = "#8A93A3"

# --------------------------------------------------------------------------
# DATA HELPERS (cached — real-time-ish, refreshed every 5 minutes)
# --------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def load_price_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    date_col = "Date" if "Date" in df.columns else "Datetime"
    df = df.rename(columns={date_col: "Date"})
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_fundamentals(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).get_info()
    except Exception:
        info = {}
    return info or {}


def fmt_num(value, prefix="", suffix="", decimals=2, big=False):
    if value is None or value == "" or (isinstance(value, float) and np.isnan(value)):
        return "—"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "—"
    if big:
        for unit, div in [("T", 1e12), ("B", 1e9), ("M", 1e6)]:
            if abs(value) >= div:
                return f"{prefix}{value/div:,.{decimals}f}{unit}{suffix}"
        return f"{prefix}{value:,.{decimals}f}{suffix}"
    return f"{prefix}{value:,.{decimals}f}{suffix}"


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["SMA20"] = out["Close"].rolling(20).mean()
    out["SMA50"] = out["Close"].rolling(50).mean()
    out["SMA200"] = out["Close"].rolling(200).mean()

    delta = out["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out["RSI14"] = 100 - (100 / (1 + rs))

    ema12 = out["Close"].ewm(span=12, adjust=False).mean()
    ema26 = out["Close"].ewm(span=26, adjust=False).mean()
    out["MACD"] = ema12 - ema26
    out["MACD_SIGNAL"] = out["MACD"].ewm(span=9, adjust=False).mean()
    out["MACD_HIST"] = out["MACD"] - out["MACD_SIGNAL"]

    out["BB_MID"] = out["Close"].rolling(20).mean()
    bb_std = out["Close"].rolling(20).std()
    out["BB_UP"] = out["BB_MID"] + 2 * bb_std
    out["BB_DN"] = out["BB_MID"] - 2 * bb_std
    return out


def simple_dcf(fcf: float, growth: float, discount: float, terminal_growth: float,
                years: int, net_debt: float, shares_out: float):
    if fcf is None or fcf <= 0 or shares_out in (None, 0):
        return None
    cash_flows = []
    cf = fcf
    for _ in range(years):
        cf = cf * (1 + growth)
        cash_flows.append(cf)
    terminal_value = cash_flows[-1] * (1 + terminal_growth) / (discount - terminal_growth)
    pv = sum(cf / ((1 + discount) ** (i + 1)) for i, cf in enumerate(cash_flows))
    pv_terminal = terminal_value / ((1 + discount) ** years)
    enterprise_value = pv + pv_terminal
    equity_value = enterprise_value - (net_debt or 0)
    fair_value_per_share = equity_value / shares_out
    return {
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "fair_value_per_share": fair_value_per_share,
    }


# --------------------------------------------------------------------------
# SIDEBAR CONTROLS
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### \U0001F4CA  Terminal Controls")
    tickers_raw = st.text_input(
        "Watchlist (comma-separated tickers)",
        value="AAPL, MSFT, NVDA, JPM, GS",
    )
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    primary_ticker = st.selectbox("Primary equity for deep-dive", options=tickers or ["AAPL"])

    period = st.selectbox(
        "History window",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
        index=3,
    )
    interval = st.selectbox(
        "Bar interval",
        options=["1d", "1wk", "1mo"],
        index=0,
    )
    benchmark = st.text_input("Benchmark index", value="^GSPC")

    st.markdown("---")
    st.markdown("### \U0001F9EE DCF Assumptions")
    growth_rate = st.slider("FCF growth rate (yrs 1-5)", 0.0, 0.30, 0.08, 0.01)
    discount_rate = st.slider("Discount rate (WACC)", 0.04, 0.15, 0.09, 0.005)
    terminal_growth = st.slider("Terminal growth rate", 0.0, 0.05, 0.025, 0.0025)

    st.markdown("---")
    st.caption("Data via Yahoo Finance. Cached 5 min. For research / educational use — not investment advice.")

if not tickers:
    st.warning("Add at least one ticker in the sidebar to begin.")
    st.stop()

# --------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="terminal-header">
        <h1>Equity Research &amp; Portfolio Analytics Terminal</h1>
        <p>Live Pricing &nbsp;&bull;&nbsp; Technical Studies &nbsp;&bull;&nbsp; Fundamental Valuation &nbsp;&bull;&nbsp; Portfolio Risk</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# KPI ROW — primary ticker snapshot
# --------------------------------------------------------------------------
hist = load_price_history(primary_ticker, period="6mo", interval="1d")
info = load_fundamentals(primary_ticker)

if hist.empty:
    st.error(f"No price data returned for {primary_ticker}. Check the ticker symbol.")
    st.stop()

last_close = hist["Close"].iloc[-1]
prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else last_close
day_change = last_close - prev_close
day_change_pct = (day_change / prev_close * 100) if prev_close else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
kpi_data = [
    (k1, "Last Price", f"${last_close:,.2f}", day_change_pct),
    (k2, "Market Cap", fmt_num(info.get("marketCap"), prefix="$", big=True), None),
    (k3, "P/E (TTM)", fmt_num(info.get("trailingPE")), None),
    (k4, "Dividend Yield", fmt_num((info.get("dividendYield") or 0) * (1 if (info.get("dividendYield") or 0) > 1 else 100), suffix="%"), None),
    (k5, "Beta", fmt_num(info.get("beta")), None),
    (k6, "52-Wk Range", f"{fmt_num(info.get('fiftyTwoWeekLow'), prefix='$')} – {fmt_num(info.get('fiftyTwoWeekHigh'), prefix='$')}", None),
]
for col, label, value, delta in kpi_data:
    with col:
        delta_html = ""
        if delta is not None:
            cls = "kpi-delta-pos" if delta >= 0 else "kpi-delta-neg"
            arrow = "▲" if delta >= 0 else "▼"
            delta_html = f'<div class="{cls}">{arrow} {abs(delta):.2f}% today</div>'
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                {delta_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

# --------------------------------------------------------------------------
# TABS
# --------------------------------------------------------------------------
tab_overview, tab_deepdive, tab_valuation, tab_portfolio = st.tabs(
    ["\U0001F30D Market Overview", "\U0001F50E Equity Deep Dive", "\U0001F4B0 Valuation & DCF", "\U0001F4BC Portfolio Analytics"]
)

# ===================== TAB 1 — MARKET OVERVIEW ============================
with tab_overview:
    st.markdown('<div class="section-title">Relative Performance vs. Benchmark</div>', unsafe_allow_html=True)

    perf_frames = {}
    for t in tickers + ([benchmark] if benchmark else []):
        d = load_price_history(t, period=period, interval=interval)
        if not d.empty:
            d = d.set_index("Date")["Close"]
            perf_frames[t] = (d / d.iloc[0] - 1) * 100

    if perf_frames:
        perf_df = pd.DataFrame(perf_frames)
        fig = go.Figure()
        palette = [NAVY, GOLD, POS, "#6C5CE7", "#0984E3", "#D63031", "#00897B"]
        for i, col in enumerate(perf_df.columns):
            width = 3 if col == benchmark else 2
            dash = "dot" if col == benchmark else "solid"
            fig.add_trace(go.Scatter(
                x=perf_df.index, y=perf_df[col],
                name=col, mode="lines",
                line=dict(width=width, color=palette[i % len(palette)], dash=dash),
            ))
        fig.update_layout(
            template=PLOTLY_TEMPLATE, height=440,
            yaxis_title="Cumulative Return (%)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.markdown('<div class="section-title">Watchlist Snapshot</div>', unsafe_allow_html=True)
        rows = []
        for t in tickers:
            d = load_price_history(t, period="5d", interval="1d")
            fi = load_fundamentals(t)
            if d.empty:
                continue
            last = d["Close"].iloc[-1]
            prev = d["Close"].iloc[-2] if len(d) > 1 else last
            chg = (last - prev) / prev * 100 if prev else 0
            rows.append({
                "Ticker": t,
                "Name": fi.get("shortName", t),
                "Price": last,
                "Chg %": chg,
                "Mkt Cap": fmt_num(fi.get("marketCap"), prefix="$", big=True),
                "P/E": fmt_num(fi.get("trailingPE")),
                "Sector": fi.get("sector", "—"),
            })
        if rows:
            wl = pd.DataFrame(rows)
            st.dataframe(
                wl.style.format({"Price": "${:,.2f}", "Chg %": "{:+.2f}%"})
                  .map(lambda v: f"color: {POS}" if isinstance(v, (int, float)) and v >= 0 else f"color: {NEG}", subset=["Chg %"]),
                use_container_width=True, hide_index=True,
            )

    with c2:
        st.markdown('<div class="section-title">Correlation Matrix</div>', unsafe_allow_html=True)
        if perf_frames and len(perf_frames) > 1:
            corr = pd.DataFrame(perf_frames).pct_change().corr()
            fig_corr = go.Figure(data=go.Heatmap(
                z=corr.values, x=corr.columns, y=corr.columns,
                colorscale=[[0, "#B3261E"], [0.5, "#F7F5F0"], [1, NAVY]],
                zmin=-1, zmax=1, text=np.round(corr.values, 2), texttemplate="%{text}",
            ))
            fig_corr.update_layout(template=PLOTLY_TEMPLATE, height=360, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_corr, use_container_width=True)

# ===================== TAB 2 — EQUITY DEEP DIVE ============================
with tab_deepdive:
    ddf = load_price_history(primary_ticker, period=period, interval=interval)
    if ddf.empty:
        st.warning("No data for this ticker/period.")
    else:
        ind = compute_indicators(ddf)

        st.markdown(f'<div class="section-title">{primary_ticker} — Price, Volume &amp; Moving Averages</div>', unsafe_allow_html=True)
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True, row_heights=[0.55, 0.15, 0.3],
            vertical_spacing=0.04,
            specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}]],
        )
        fig.add_trace(go.Candlestick(
            x=ind["Date"], open=ind["Open"], high=ind["High"], low=ind["Low"], close=ind["Close"],
            name="Price", increasing_line_color=POS, decreasing_line_color=NEG,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(x=ind["Date"], y=ind["SMA20"], name="SMA 20", line=dict(color=GOLD, width=1.4)), row=1, col=1)
        fig.add_trace(go.Scatter(x=ind["Date"], y=ind["SMA50"], name="SMA 50", line=dict(color=NAVY, width=1.4)), row=1, col=1)
        fig.add_trace(go.Scatter(x=ind["Date"], y=ind["BB_UP"], name="BB Upper", line=dict(color=GREY, width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=ind["Date"], y=ind["BB_DN"], name="BB Lower", line=dict(color=GREY, width=1, dash="dot"), fill="tonexty", fillcolor="rgba(138,147,163,0.08)"), row=1, col=1)

        vol_colors = [POS if c >= o else NEG for o, c in zip(ind["Open"], ind["Close"])]
        fig.add_trace(go.Bar(x=ind["Date"], y=ind["Volume"], name="Volume", marker_color=vol_colors, opacity=0.6), row=2, col=1)

        fig.add_trace(go.Scatter(x=ind["Date"], y=ind["RSI14"], name="RSI(14)", line=dict(color="#6C5CE7", width=1.6)), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color=NEG, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color=POS, row=3, col=1)

        fig.update_layout(
            template=PLOTLY_TEMPLATE, height=760, showlegend=True,
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-title">MACD</div>', unsafe_allow_html=True)
        fig_macd = go.Figure()
        macd_colors = [POS if v >= 0 else NEG for v in ind["MACD_HIST"]]
        fig_macd.add_trace(go.Bar(x=ind["Date"], y=ind["MACD_HIST"], name="Histogram", marker_color=macd_colors, opacity=0.55))
        fig_macd.add_trace(go.Scatter(x=ind["Date"], y=ind["MACD"], name="MACD", line=dict(color=NAVY, width=1.6)))
        fig_macd.add_trace(go.Scatter(x=ind["Date"], y=ind["MACD_SIGNAL"], name="Signal", line=dict(color=GOLD, width=1.6)))
        fig_macd.update_layout(template=PLOTLY_TEMPLATE, height=280, margin=dict(l=10, r=10, t=10, b=10),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
        st.plotly_chart(fig_macd, use_container_width=True)

        # Technical read-out
        last_rsi = ind["RSI14"].iloc[-1]
        trend = "bullish" if ind["SMA20"].iloc[-1] > ind["SMA50"].iloc[-1] else "bearish"
        rsi_state = "overbought" if last_rsi > 70 else "oversold" if last_rsi < 30 else "neutral"
        st.markdown(
            f"""
            <div class="verdict-box">
            <b>Technical read:</b> {primary_ticker} is in a short-term <b>{trend}</b> posture
            (20-day SMA {'above' if trend=='bullish' else 'below'} 50-day SMA), with RSI(14) at
            <b>{last_rsi:.1f}</b> — currently <b>{rsi_state}</b>. This is a mechanical read of price
            action only and should be weighed alongside fundamentals below.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ===================== TAB 3 — VALUATION & DCF ============================
with tab_valuation:
    fi = load_fundamentals(primary_ticker)
    st.markdown(f'<div class="section-title">{primary_ticker} — Fundamental Snapshot</div>', unsafe_allow_html=True)

    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    fund_metrics = [
        (fcol1, "P/E (TTM)", fmt_num(fi.get("trailingPE"))),
        (fcol1, "Forward P/E", fmt_num(fi.get("forwardPE"))),
        (fcol2, "PEG Ratio", fmt_num(fi.get("pegRatio"))),
        (fcol2, "Price / Book", fmt_num(fi.get("priceToBook"))),
        (fcol3, "EV / EBITDA", fmt_num(fi.get("enterpriseToEbitda"))),
        (fcol3, "Profit Margin", fmt_num((fi.get("profitMargins") or 0) * 100, suffix="%")),
        (fcol4, "ROE", fmt_num((fi.get("returnOnEquity") or 0) * 100, suffix="%")),
        (fcol4, "Debt / Equity", fmt_num(fi.get("debtToEquity"))),
    ]
    for col, label, value in fund_metrics:
        with col:
            st.markdown(
                f"""<div class="kpi-card" style="margin-bottom:12px;">
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-value" style="font-size:19px;">{value}</div>
                    </div>""",
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-title">Discounted Cash Flow — Fair Value Estimate</div>', unsafe_allow_html=True)

    fcf = fi.get("freeCashflow")
    shares_out = fi.get("sharesOutstanding")
    net_debt = (fi.get("totalDebt") or 0) - (fi.get("totalCash") or 0)
    current_price = last_close if primary_ticker == primary_ticker else fi.get("currentPrice")

    dcf_result = simple_dcf(fcf, growth_rate, discount_rate, terminal_growth, 5, net_debt, shares_out)

    dcol1, dcol2 = st.columns([1, 1.4])
    with dcol1:
        if dcf_result:
            fair_value = dcf_result["fair_value_per_share"]
            upside = (fair_value / current_price - 1) * 100 if current_price else None
            verdict = "undervalued" if upside and upside > 0 else "overvalued"
            st.markdown(
                f"""
                <div class="kpi-card" style="border-left-color:{POS if (upside or 0) > 0 else NEG};">
                    <div class="kpi-label">DCF Fair Value / Share</div>
                    <div class="kpi-value">${fair_value:,.2f}</div>
                    <div class="{'kpi-delta-pos' if (upside or 0) > 0 else 'kpi-delta-neg'}">
                        {upside:+.1f}% vs. current price — appears {verdict}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(
                "5-year explicit free-cash-flow projection, Gordon-growth terminal value, "
                "discounted at the WACC set in the sidebar. Adjust growth/discount/terminal "
                "assumptions to stress-test the output."
            )
        else:
            st.info("Free cash flow or share count unavailable for this ticker — DCF cannot be computed.")

    with dcol2:
        if dcf_result and fcf:
            years = list(range(1, 6))
            proj = [fcf * (1 + growth_rate) ** y for y in years]
            fig_dcf = go.Figure()
            fig_dcf.add_trace(go.Bar(x=[f"Year {y}" for y in years], y=proj, marker_color=NAVY, name="Projected FCF"))
            fig_dcf.update_layout(template=PLOTLY_TEMPLATE, height=300, margin=dict(l=10, r=10, t=10, b=10),
                                   yaxis_title="Projected Free Cash Flow ($)")
            st.plotly_chart(fig_dcf, use_container_width=True)

    st.markdown('<div class="section-title">Analyst Price Targets</div>', unsafe_allow_html=True)
    tcol1, tcol2, tcol3 = st.columns(3)
    for col, label, key in [
        (tcol1, "Target Low", "targetLowPrice"),
        (tcol2, "Target Mean", "targetMeanPrice"),
        (tcol3, "Target High", "targetHighPrice"),
    ]:
        with col:
            st.markdown(
                f"""<div class="kpi-card">
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-value">{fmt_num(fi.get(key), prefix="$")}</div>
                    </div>""",
                unsafe_allow_html=True,
            )

# ===================== TAB 4 — PORTFOLIO ANALYTICS ==========================
with tab_portfolio:
    st.markdown('<div class="section-title">Portfolio Construction</div>', unsafe_allow_html=True)
    st.caption("Assign weights to each watchlist name (they will be normalised to sum to 100%).")

    weight_cols = st.columns(len(tickers))
    raw_weights = {}
    for col, t in zip(weight_cols, tickers):
        with col:
            raw_weights[t] = st.number_input(t, min_value=0.0, max_value=100.0, value=round(100/len(tickers), 1), step=1.0, key=f"w_{t}")

    total_w = sum(raw_weights.values()) or 1.0
    weights = {t: w / total_w for t, w in raw_weights.items()}

    price_frames = {}
    for t in tickers:
        d = load_price_history(t, period=period, interval=interval)
        if not d.empty:
            price_frames[t] = d.set_index("Date")["Close"]

    if price_frames:
        prices = pd.DataFrame(price_frames).dropna()
        returns = prices.pct_change().dropna()
        port_returns = returns.dot(pd.Series(weights))
        cum_port = (1 + port_returns).cumprod() - 1

        ann_return = port_returns.mean() * 252
        ann_vol = port_returns.std() * np.sqrt(252)
        sharpe = ann_return / ann_vol if ann_vol else np.nan

        pcol1, pcol2, pcol3, pcol4 = st.columns(4)
        for col, label, val in [
            (pcol1, "Annualised Return", f"{ann_return*100:,.2f}%"),
            (pcol2, "Annualised Volatility", f"{ann_vol*100:,.2f}%"),
            (pcol3, "Sharpe Ratio", f"{sharpe:,.2f}"),
            (pcol4, "Max Drawdown", f"{((1+port_returns).cumprod()/((1+port_returns).cumprod().cummax())-1).min()*100:,.2f}%"),
        ]:
            with col:
                st.markdown(
                    f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
                        <div class="kpi-value" style="font-size:20px;">{val}</div></div>""",
                    unsafe_allow_html=True,
                )

        gcol1, gcol2 = st.columns([1.5, 1])
        with gcol1:
            st.markdown('<div class="section-title">Cumulative Portfolio Return</div>', unsafe_allow_html=True)
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=cum_port.index, y=cum_port.values * 100, fill="tozeroy",
                                        line=dict(color=NAVY, width=2), fillcolor="rgba(11,31,58,0.10)", name="Portfolio"))
            fig_p.update_layout(template=PLOTLY_TEMPLATE, height=360, yaxis_title="Return (%)",
                                 margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_p, use_container_width=True)

        with gcol2:
            st.markdown('<div class="section-title">Allocation</div>', unsafe_allow_html=True)
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(weights.keys()), values=list(weights.values()),
                hole=0.55, marker=dict(colors=[NAVY, GOLD, POS, "#6C5CE7", "#0984E3", "#D63031", "#00897B"]),
            )])
            fig_pie.update_layout(template=PLOTLY_TEMPLATE, height=360, margin=dict(l=10, r=10, t=10, b=10),
                                   showlegend=True, legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown(
        """
        <div class="verdict-box" style="margin-top:10px;">
        <b>Disclosure:</b> All figures are generated from delayed/real-time public market data
        for research and educational purposes only. Nothing in this terminal constitutes
        investment advice or a recommendation to buy or sell any security.
        </div>
        """,
        unsafe_allow_html=True,
    )
