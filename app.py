"""
Equity Research & Portfolio Analytics Terminal — v2
-----------------------------------------------------
Single-file Streamlit application:
  1. Market Overview       — relative performance, correlation
  2. Equity Deep Dive       — candlesticks, SMA/Bollinger, RSI, MACD
  3. Valuation & DCF        — fundamentals + two-stage DCF with sensitivity grid
  4. Factor Screener        — multi-factor quant score & ranked ideas across a universe
  5. Portfolio Lab          — search & build a portfolio, CAPM expected return,
                               Monte Carlo return simulation, Monte Carlo efficient frontier

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

IMPORTANT: This is a research / educational tool. Nothing it outputs is
investment advice. All model outputs are only as good as their inputs and
assumptions — always sanity-check before relying on any figure here.
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
    page_title="Equity Research Terminal",
    page_icon="\U0001F4C8",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# GLOBAL STYLE
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=Inter:wght@400;500;600;700&display=swap');

    :root{
        --navy:#0B1F3A; --navy-2:#132A4D; --gold:#B7893F; --gold-soft:#D9B876;
        --ivory:#F7F5F0; --ink:#101826; --muted:#5B6472;
        --pos:#1E7A46; --neg:#B3261E; --line:#E4E0D6;
    }
    html, body, [class*="css"]{ font-family:'Inter', sans-serif; }
    .stApp{ background:var(--ivory); }
    section[data-testid="stSidebar"]{ background:var(--navy); }
    section[data-testid="stSidebar"] *{ color:#EDEFF3 !important; }
    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stNumberInput input{ color:#101826 !important; }

    .terminal-header{
        background:linear-gradient(120deg, var(--navy) 0%, var(--navy-2) 100%);
        border-radius:10px; padding:28px 34px; margin-bottom:22px;
        box-shadow:0 8px 24px rgba(11,31,58,0.25);
    }
    .terminal-header h1{
        font-family:'Source Serif 4', serif; color:#FBF9F3; font-size:32px;
        font-weight:700; margin:0 0 4px; letter-spacing:.01em;
    }
    .terminal-header p{
        color:var(--gold-soft); font-size:13.5px; letter-spacing:.14em;
        text-transform:uppercase; margin:0;
    }

    .kpi-card{
        background:#FFFFFF; border:1px solid var(--line); border-left:4px solid var(--gold);
        border-radius:8px; padding:16px 18px; box-shadow:0 1px 2px rgba(16,24,38,0.04); height:100%;
    }
    .kpi-label{ font-size:11px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); margin-bottom:6px; }
    .kpi-value{ font-family:'Source Serif 4', serif; font-size:24px; font-weight:700; color:var(--ink); }
    .kpi-delta-pos{ color:var(--pos); font-weight:600; font-size:13.5px; }
    .kpi-delta-neg{ color:var(--neg); font-weight:600; font-size:13.5px; }

    .section-title{
        font-family:'Source Serif 4', serif; font-size:20px; font-weight:700; color:var(--navy);
        border-bottom:2px solid var(--gold); padding-bottom:6px; margin:26px 0 14px;
    }
    .verdict-box{
        border-radius:8px; padding:18px 22px; font-size:14.5px; line-height:1.55;
        border:1px solid var(--line); background:#FFFFFF;
    }
    .rank-pill{
        display:inline-block; min-width:26px; text-align:center; padding:2px 8px;
        border-radius:12px; background:var(--navy); color:#fff; font-weight:700; font-size:12px;
        margin-right:8px;
    }
    .score-bar-bg{ background:#EDEAE0; border-radius:6px; height:10px; width:100%; overflow:hidden; }
    .score-bar-fill{ height:10px; border-radius:6px; }

    .stTabs [data-baseweb="tab-list"]{ gap:6px; }
    .stTabs [data-baseweb="tab"]{
        background:#FFFFFF; border:1px solid var(--line); border-radius:6px 6px 0 0;
        padding:10px 16px; font-weight:600; color:var(--navy);
    }
    .stTabs [aria-selected="true"]{ background:var(--navy) !important; color:#F7F5F0 !important; }

    footer{visibility:hidden;} #MainMenu{visibility:hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_TEMPLATE = "plotly_white"
NAVY, GOLD, POS, NEG, GREY = "#0B1F3A", "#B7893F", "#1E7A46", "#B3261E", "#8A93A3"
PALETTE = [NAVY, GOLD, POS, "#6C5CE7", "#0984E3", "#D63031", "#00897B", "#E17055"]

DEFAULT_UNIVERSE = (
    "AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, AVGO, "
    "JPM, GS, BAC, MS, V, MA, "
    "JNJ, PFE, UNH, LLY, "
    "XOM, CVX, "
    "PG, KO, PEP, WMT, HD, COST, "
    "DIS, NFLX, ADBE, CRM, ORCL, INTC, AMD"
)

# --------------------------------------------------------------------------
# DATA HELPERS
# --------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def load_price_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
    except Exception:
        return pd.DataFrame()
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


@st.cache_data(ttl=600, show_spinner=False)
def load_fcf_estimate(ticker: str):
    """Best-effort free cash flow: prefer the cash-flow statement
    (Operating CF - CapEx) over the sometimes-stale `info` field."""
    try:
        cf = yf.Ticker(ticker).cashflow
        if cf is not None and not cf.empty:
            for row in ("Free Cash Flow", "FreeCashFlow"):
                if row in cf.index:
                    vals = cf.loc[row].dropna()
                    if len(vals):
                        return float(vals.iloc[0])
            ocf = capex = None
            for row in ("Operating Cash Flow", "Total Cash From Operating Activities"):
                if row in cf.index:
                    v = cf.loc[row].dropna()
                    if len(v):
                        ocf = float(v.iloc[0])
                        break
            for row in ("Capital Expenditure", "Capital Expenditures"):
                if row in cf.index:
                    v = cf.loc[row].dropna()
                    if len(v):
                        capex = float(v.iloc[0])
                        break
            if ocf is not None and capex is not None:
                return ocf + capex  # capex is typically reported negative
    except Exception:
        pass
    info = load_fundamentals(ticker)
    return info.get("freeCashflow")


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
    gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
    avg_gain, avg_loss = gain.rolling(14).mean(), loss.rolling(14).mean()
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


# ---- Two-stage DCF with a fading growth rate + sensitivity grid -----------
def two_stage_dcf(fcf, growth_y1, discount, terminal_growth, net_debt, shares_out, years=5):
    if not fcf or fcf <= 0 or not shares_out:
        return None
    growths = np.linspace(growth_y1, terminal_growth, years)  # fades to terminal
    cfs, cf = [], fcf
    for g in growths:
        cf = cf * (1 + g)
        cfs.append(cf)
    if discount <= terminal_growth:
        return None
    terminal_value = cfs[-1] * (1 + terminal_growth) / (discount - terminal_growth)
    pv = sum(c / ((1 + discount) ** (i + 1)) for i, c in enumerate(cfs))
    pv_terminal = terminal_value / ((1 + discount) ** years)
    ev = pv + pv_terminal
    equity_value = ev - (net_debt or 0)
    return {
        "enterprise_value": ev,
        "equity_value": equity_value,
        "fair_value_per_share": equity_value / shares_out,
        "projected_fcf": cfs,
    }


def dcf_sensitivity_grid(fcf, growth_y1, terminal_growth, net_debt, shares_out,
                          discount_range, terminal_range):
    grid = np.zeros((len(discount_range), len(terminal_range)))
    for i, d in enumerate(discount_range):
        for j, t in enumerate(terminal_range):
            res = two_stage_dcf(fcf, growth_y1, d, t, net_debt, shares_out)
            grid[i, j] = res["fair_value_per_share"] if res else np.nan
    return grid


# ---- Factor scoring ---------------------------------------------------
def zscore(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    mu, sd = s.mean(skipna=True), s.std(skipna=True)
    if not sd or np.isnan(sd) or sd == 0:
        return pd.Series(0.0, index=series.index)
    return (s - mu) / sd


@st.cache_data(ttl=600, show_spinner=False)
def build_factor_table(universe: tuple) -> pd.DataFrame:
    rows = []
    for t in universe:
        fi = load_fundamentals(t)
        hist = load_price_history(t, period="1y", interval="1d")
        mom_6m = np.nan
        if not hist.empty and len(hist) > 126:
            mom_6m = hist["Close"].iloc[-1] / hist["Close"].iloc[-126] - 1
        elif not hist.empty:
            mom_6m = hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1
        rows.append({
            "Ticker": t,
            "Name": fi.get("shortName", t),
            "Sector": fi.get("sector", "—"),
            "Price": fi.get("currentPrice") or (hist["Close"].iloc[-1] if not hist.empty else np.nan),
            "P/E": fi.get("trailingPE"),
            "Fwd P/E": fi.get("forwardPE"),
            "P/B": fi.get("priceToBook"),
            "EV/EBITDA": fi.get("enterpriseToEbitda"),
            "RevGrowth": fi.get("revenueGrowth"),
            "EarnGrowth": fi.get("earningsGrowth"),
            "ROE": fi.get("returnOnEquity"),
            "ProfitMargin": fi.get("profitMargins"),
            "DebtEquity": fi.get("debtToEquity"),
            "Beta": fi.get("beta"),
            "Mom6M": mom_6m,
            "MktCap": fi.get("marketCap"),
        })
    return pd.DataFrame(rows)


def score_universe(df: pd.DataFrame, w_value, w_growth, w_quality, w_momentum, w_health) -> pd.DataFrame:
    d = df.copy()
    # Value: lower multiples => better => negate the z-score
    z_pe = -zscore(d["P/E"].fillna(d["P/E"].median()))
    z_pb = -zscore(d["P/B"].fillna(d["P/B"].median()))
    z_ev = -zscore(d["EV/EBITDA"].fillna(d["EV/EBITDA"].median()))
    d["ValueScore"] = (z_pe + z_pb + z_ev) / 3

    z_rev = zscore(d["RevGrowth"].fillna(d["RevGrowth"].median()))
    z_earn = zscore(d["EarnGrowth"].fillna(d["EarnGrowth"].median()))
    d["GrowthScore"] = (z_rev + z_earn) / 2

    z_roe = zscore(d["ROE"].fillna(d["ROE"].median()))
    z_margin = zscore(d["ProfitMargin"].fillna(d["ProfitMargin"].median()))
    d["QualityScore"] = (z_roe + z_margin) / 2

    d["MomentumScore"] = zscore(d["Mom6M"].fillna(d["Mom6M"].median()))

    d["HealthScore"] = -zscore(d["DebtEquity"].fillna(d["DebtEquity"].median()))

    w_sum = max(w_value + w_growth + w_quality + w_momentum + w_health, 1e-9)
    d["CompositeScore"] = (
        w_value * d["ValueScore"] + w_growth * d["GrowthScore"] +
        w_quality * d["QualityScore"] + w_momentum * d["MomentumScore"] +
        w_health * d["HealthScore"]
    ) / w_sum
    return d.sort_values("CompositeScore", ascending=False).reset_index(drop=True)


def score_to_pct(score_series: pd.Series) -> pd.Series:
    """Map composite z-scores onto an intuitive 0-100 scale for display."""
    lo, hi = score_series.min(), score_series.max()
    if hi - lo < 1e-9:
        return pd.Series(50.0, index=score_series.index)
    return (score_series - lo) / (hi - lo) * 100


# --------------------------------------------------------------------------
# SIDEBAR
# --------------------------------------------------------------------------
if "custom_universe" not in st.session_state:
    st.session_state.custom_universe = set()

with st.sidebar:
    st.markdown("### \U0001F4CA Terminal Controls")
    tickers_raw = st.text_input("Watchlist (comma-separated tickers)", value="AAPL, MSFT, NVDA, JPM, GS")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    primary_ticker = st.selectbox("Primary equity for deep-dive", options=tickers or ["AAPL"])

    period = st.selectbox("History window", options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)
    interval = st.selectbox("Bar interval", options=["1d", "1wk", "1mo"], index=0)
    benchmark = st.text_input("Benchmark index", value="^GSPC")

    st.markdown("---")
    st.markdown("### \U0001F9EE DCF Assumptions")
    growth_rate = st.slider("FCF growth rate — Year 1", 0.0, 0.35, 0.10, 0.01)
    discount_rate = st.slider("Discount rate (WACC)", 0.04, 0.16, 0.09, 0.005)
    terminal_growth = st.slider("Terminal growth rate", 0.0, 0.05, 0.025, 0.0025)

    st.markdown("---")
    st.markdown("### \U0001F3AF Factor Weights (Screener)")
    w_value = st.slider("Value weight", 0.0, 3.0, 1.0, 0.1)
    w_growth = st.slider("Growth weight", 0.0, 3.0, 1.0, 0.1)
    w_quality = st.slider("Quality weight", 0.0, 3.0, 1.0, 0.1)
    w_momentum = st.slider("Momentum weight", 0.0, 3.0, 1.0, 0.1)
    w_health = st.slider("Balance-sheet health weight", 0.0, 3.0, 0.5, 0.1)

    st.markdown("---")
    st.markdown("### \U0001F4B5 Capital Market Assumptions")
    risk_free = st.number_input("Risk-free rate (%)", value=4.3, step=0.1) / 100
    equity_risk_premium = st.number_input("Equity risk premium (%)", value=5.0, step=0.1) / 100

    st.markdown("---")
    st.caption("Data via Yahoo Finance, cached 5–10 min. Research / educational use — not investment advice.")

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
        <p>Live Pricing &nbsp;&bull;&nbsp; Technical Studies &nbsp;&bull;&nbsp; Fundamental Valuation
        &nbsp;&bull;&nbsp; Factor Screening &nbsp;&bull;&nbsp; Portfolio Simulation</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# KPI ROW
# --------------------------------------------------------------------------
hist = load_price_history(primary_ticker, period="6mo", interval="1d")
info = load_fundamentals(primary_ticker)

if hist.empty:
    st.error(f"No price data returned for {primary_ticker}. Check the ticker symbol.")
    st.stop()

last_close = hist["Close"].iloc[-1]
prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else last_close
day_change_pct = ((last_close - prev_close) / prev_close * 100) if prev_close else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
div_yield_raw = info.get("dividendYield") or 0
div_yield = div_yield_raw if div_yield_raw > 1 else div_yield_raw * 100
kpi_data = [
    (k1, "Last Price", f"${last_close:,.2f}", day_change_pct),
    (k2, "Market Cap", fmt_num(info.get("marketCap"), prefix="$", big=True), None),
    (k3, "P/E (TTM)", fmt_num(info.get("trailingPE")), None),
    (k4, "Dividend Yield", fmt_num(div_yield, suffix="%"), None),
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
            f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>{delta_html}</div>""",
            unsafe_allow_html=True,
        )

# --------------------------------------------------------------------------
# TABS
# --------------------------------------------------------------------------
tab_overview, tab_deepdive, tab_valuation, tab_screener, tab_portfolio = st.tabs(
    ["\U0001F30D Market Overview", "\U0001F50E Equity Deep Dive", "\U0001F4B0 Valuation & DCF",
     "\U0001F9EA Factor Screener", "\U0001F4BC Portfolio Lab"]
)

# ===================== TAB 1 — MARKET OVERVIEW ============================
with tab_overview:
    st.markdown('<div class="section-title">Relative Performance vs. Benchmark</div>', unsafe_allow_html=True)
    perf_frames = {}
    for t in tickers + ([benchmark] if benchmark else []):
        d = load_price_history(t, period=period, interval=interval)
        if not d.empty:
            s = d.set_index("Date")["Close"]
            perf_frames[t] = (s / s.iloc[0] - 1) * 100

    if perf_frames:
        perf_df = pd.DataFrame(perf_frames)
        fig = go.Figure()
        for i, col in enumerate(perf_df.columns):
            width = 3 if col == benchmark else 2
            dash = "dot" if col == benchmark else "solid"
            fig.add_trace(go.Scatter(x=perf_df.index, y=perf_df[col], name=col, mode="lines",
                                      line=dict(width=width, color=PALETTE[i % len(PALETTE)], dash=dash)))
        fig.update_layout(template=PLOTLY_TEMPLATE, height=440, yaxis_title="Cumulative Return (%)",
                           hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                           margin=dict(l=10, r=10, t=10, b=10))
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
            last, prev = d["Close"].iloc[-1], (d["Close"].iloc[-2] if len(d) > 1 else d["Close"].iloc[-1])
            chg = (last - prev) / prev * 100 if prev else 0
            rows.append({"Ticker": t, "Name": fi.get("shortName", t), "Price": last, "Chg %": chg,
                         "Mkt Cap": fmt_num(fi.get("marketCap"), prefix="$", big=True),
                         "P/E": fmt_num(fi.get("trailingPE")), "Sector": fi.get("sector", "—")})
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
                colorscale=[[0, NEG], [0.5, "#F7F5F0"], [1, NAVY]], zmin=-1, zmax=1,
                text=np.round(corr.values, 2), texttemplate="%{text}"))
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
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.55, 0.15, 0.3], vertical_spacing=0.04)
        fig.add_trace(go.Candlestick(x=ind["Date"], open=ind["Open"], high=ind["High"], low=ind["Low"], close=ind["Close"],
                                      name="Price", increasing_line_color=POS, decreasing_line_color=NEG), row=1, col=1)
        fig.add_trace(go.Scatter(x=ind["Date"], y=ind["SMA20"], name="SMA 20", line=dict(color=GOLD, width=1.4)), row=1, col=1)
        fig.add_trace(go.Scatter(x=ind["Date"], y=ind["SMA50"], name="SMA 50", line=dict(color=NAVY, width=1.4)), row=1, col=1)
        fig.add_trace(go.Scatter(x=ind["Date"], y=ind["BB_UP"], name="BB Upper", line=dict(color=GREY, width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=ind["Date"], y=ind["BB_DN"], name="BB Lower", line=dict(color=GREY, width=1, dash="dot"),
                                  fill="tonexty", fillcolor="rgba(138,147,163,0.08)"), row=1, col=1)
        vol_colors = [POS if c >= o else NEG for o, c in zip(ind["Open"], ind["Close"])]
        fig.add_trace(go.Bar(x=ind["Date"], y=ind["Volume"], name="Volume", marker_color=vol_colors, opacity=0.6), row=2, col=1)
        fig.add_trace(go.Scatter(x=ind["Date"], y=ind["RSI14"], name="RSI(14)", line=dict(color="#6C5CE7", width=1.6)), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color=NEG, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color=POS, row=3, col=1)
        fig.update_layout(template=PLOTLY_TEMPLATE, height=760, showlegend=True, xaxis_rangeslider_visible=False,
                           legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0), margin=dict(l=10, r=10, t=10, b=10))
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

        last_rsi = ind["RSI14"].iloc[-1]
        trend = "bullish" if ind["SMA20"].iloc[-1] > ind["SMA50"].iloc[-1] else "bearish"
        rsi_state = "overbought" if last_rsi > 70 else "oversold" if last_rsi < 30 else "neutral"
        st.markdown(
            f"""<div class="verdict-box"><b>Technical read:</b> {primary_ticker} is in a short-term
            <b>{trend}</b> posture (20-day SMA {'above' if trend=='bullish' else 'below'} 50-day SMA),
            with RSI(14) at <b>{last_rsi:.1f}</b> — currently <b>{rsi_state}</b>. Mechanical price read
            only; weigh alongside the fundamentals and factor score elsewhere in this terminal.</div>""",
            unsafe_allow_html=True,
        )

# ===================== TAB 3 — VALUATION & DCF ============================
with tab_valuation:
    fi = load_fundamentals(primary_ticker)
    st.markdown(f'<div class="section-title">{primary_ticker} — Fundamental Snapshot</div>', unsafe_allow_html=True)
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    fund_metrics = [
        (fcol1, "P/E (TTM)", fmt_num(fi.get("trailingPE"))), (fcol1, "Forward P/E", fmt_num(fi.get("forwardPE"))),
        (fcol2, "PEG Ratio", fmt_num(fi.get("pegRatio"))), (fcol2, "Price / Book", fmt_num(fi.get("priceToBook"))),
        (fcol3, "EV / EBITDA", fmt_num(fi.get("enterpriseToEbitda"))),
        (fcol3, "Profit Margin", fmt_num((fi.get("profitMargins") or 0) * 100, suffix="%")),
        (fcol4, "ROE", fmt_num((fi.get("returnOnEquity") or 0) * 100, suffix="%")),
        (fcol4, "Debt / Equity", fmt_num(fi.get("debtToEquity"))),
    ]
    for col, label, value in fund_metrics:
        with col:
            st.markdown(f"""<div class="kpi-card" style="margin-bottom:12px;">
                <div class="kpi-label">{label}</div><div class="kpi-value" style="font-size:19px;">{value}</div></div>""",
                unsafe_allow_html=True)

    st.markdown('<div class="section-title">Two-Stage DCF — Fair Value Estimate</div>', unsafe_allow_html=True)
    fcf = load_fcf_estimate(primary_ticker)
    shares_out = fi.get("sharesOutstanding")
    net_debt = (fi.get("totalDebt") or 0) - (fi.get("totalCash") or 0)
    current_price = fi.get("currentPrice") or last_close

    dcf_result = two_stage_dcf(fcf, growth_rate, discount_rate, terminal_growth, net_debt, shares_out)

    dcol1, dcol2 = st.columns([1, 1.4])
    with dcol1:
        if dcf_result:
            fair_value = dcf_result["fair_value_per_share"]
            upside = (fair_value / current_price - 1) * 100 if current_price else None
            verdict = "undervalued" if (upside or 0) > 0 else "overvalued"
            st.markdown(
                f"""<div class="kpi-card" style="border-left-color:{POS if (upside or 0) > 0 else NEG};">
                    <div class="kpi-label">DCF Fair Value / Share</div>
                    <div class="kpi-value">${fair_value:,.2f}</div>
                    <div class="{'kpi-delta-pos' if (upside or 0) > 0 else 'kpi-delta-neg'}">
                        {upside:+.1f}% vs. current price — appears {verdict}</div></div>""",
                unsafe_allow_html=True,
            )
            st.caption(
                "Free cash flow is pulled from the cash-flow statement (Operating CF − CapEx) where "
                "available, with the `info` field as a fallback. Growth fades linearly from the Year-1 "
                "rate to your terminal growth rate over 5 years, then a Gordon-growth terminal value is "
                "discounted at your WACC."
            )
        else:
            st.info("Free cash flow or share count unavailable for this ticker — DCF cannot be computed.")

    with dcol2:
        if dcf_result:
            years = list(range(1, 6))
            fig_dcf = go.Figure()
            fig_dcf.add_trace(go.Bar(x=[f"Year {y}" for y in years], y=dcf_result["projected_fcf"],
                                      marker_color=NAVY, name="Projected FCF"))
            fig_dcf.update_layout(template=PLOTLY_TEMPLATE, height=300, margin=dict(l=10, r=10, t=10, b=10),
                                   yaxis_title="Projected Free Cash Flow ($)")
            st.plotly_chart(fig_dcf, use_container_width=True)

    if fcf and shares_out:
        st.markdown('<div class="section-title">Sensitivity — Fair Value vs. WACC &amp; Terminal Growth</div>', unsafe_allow_html=True)
        disc_range = np.round(np.linspace(max(discount_rate - 0.03, 0.04), discount_rate + 0.03, 7), 4)
        term_range = np.round(np.linspace(max(terminal_growth - 0.015, 0.0), terminal_growth + 0.015, 7), 4)
        grid = dcf_sensitivity_grid(fcf, growth_rate, terminal_growth, net_debt, shares_out, disc_range, term_range)
        fig_sens = go.Figure(data=go.Heatmap(
            z=grid, x=[f"{t*100:.2f}%" for t in term_range], y=[f"{d*100:.2f}%" for d in disc_range],
            colorscale=[[0, NEG], [0.5, "#F7F5F0"], [1, POS]],
            text=np.round(grid, 1), texttemplate="$%{text}",
        ))
        fig_sens.update_layout(template=PLOTLY_TEMPLATE, height=380, margin=dict(l=10, r=10, t=10, b=10),
                                xaxis_title="Terminal Growth Rate", yaxis_title="WACC / Discount Rate")
        st.plotly_chart(fig_sens, use_container_width=True)

    st.markdown('<div class="section-title">Analyst Price Targets</div>', unsafe_allow_html=True)
    tcol1, tcol2, tcol3 = st.columns(3)
    for col, label, key in [(tcol1, "Target Low", "targetLowPrice"), (tcol2, "Target Mean", "targetMeanPrice"),
                             (tcol3, "Target High", "targetHighPrice")]:
        with col:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
                <div class="kpi-value">{fmt_num(fi.get(key), prefix="$")}</div></div>""", unsafe_allow_html=True)

# ===================== TAB 4 — FACTOR SCREENER =============================
with tab_screener:
    st.markdown('<div class="section-title">Universe</div>', unsafe_allow_html=True)
    st.caption("Edit this list to screen any set of tickers. Larger lists take longer to load (uncached).")
    universe_raw = st.text_area("Screening universe (comma-separated)", value=DEFAULT_UNIVERSE, height=80)
    universe = tuple(sorted(set(t.strip().upper() for t in universe_raw.split(",") if t.strip())))

    with st.spinner(f"Pulling fundamentals for {len(universe)} names…"):
        factor_df = build_factor_table(universe)
    scored = score_universe(factor_df, w_value, w_growth, w_quality, w_momentum, w_health)
    scored["Rank"] = scored.index + 1
    scored["ScorePct"] = score_to_pct(scored["CompositeScore"])

    st.markdown('<div class="section-title">Highest-Ranked Ideas — Composite Quant Score</div>', unsafe_allow_html=True)
    st.markdown(
        """<div class="verdict-box" style="margin-bottom:14px;">
        This ranks the universe on a blended <b>Value / Growth / Quality / Momentum / Balance-sheet
        health</b> score built from each stock's standing relative to the peer set you defined above
        (z-scores), weighted by the sliders in the sidebar. It is a systematic screen, not a
        recommendation — always research a name fully (and consider risk tolerance, diversification,
        and current holdings) before acting on it.</div>""",
        unsafe_allow_html=True,
    )

    top_n = st.slider("Show top N", 3, min(20, len(scored)), min(10, len(scored)))
    for _, row in scored.head(top_n).iterrows():
        pct = max(0, min(100, row["ScorePct"]))
        bar_color = POS if pct >= 60 else GOLD if pct >= 40 else NEG
        cols = st.columns([0.5, 2.4, 1.1, 1.1, 1.1, 1.1, 2])
        cols[0].markdown(f'<span class="rank-pill">{int(row["Rank"])}</span>', unsafe_allow_html=True)
        cols[1].markdown(f"**{row['Ticker']}** — {row['Name']}<br><span style='color:{GREY};font-size:12px'>{row['Sector']}</span>", unsafe_allow_html=True)
        cols[2].markdown(f"P/E<br>**{fmt_num(row['P/E'])}**", unsafe_allow_html=True)
        cols[3].markdown(f"Rev Gr.<br>**{fmt_num((row['RevGrowth'] or 0)*100, suffix='%')}**", unsafe_allow_html=True)
        cols[4].markdown(f"ROE<br>**{fmt_num((row['ROE'] or 0)*100, suffix='%')}**", unsafe_allow_html=True)
        cols[5].markdown(f"6M Mom.<br>**{fmt_num((row['Mom6M'] or 0)*100, suffix='%')}**", unsafe_allow_html=True)
        cols[6].markdown(
            f"""<div class="score-bar-bg"><div class="score-bar-fill" style="width:{pct:.0f}%;background:{bar_color};"></div></div>
            <span style="font-size:12px;color:{GREY}">Score: {pct:.0f}/100</span>""",
            unsafe_allow_html=True,
        )
        st.markdown("<hr style='margin:6px 0;border-color:#E4E0D6;'>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Factor Radar — Top 5</div>', unsafe_allow_html=True)
    top5 = scored.head(5)
    fig_radar = go.Figure()
    categories = ["Value", "Growth", "Quality", "Momentum", "Health"]
    for i, (_, r) in enumerate(top5.iterrows()):
        vals = [r["ValueScore"], r["GrowthScore"], r["QualityScore"], r["MomentumScore"], r["HealthScore"]]
        fig_radar.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=categories + [categories[0]],
                                             fill="toself", name=r["Ticker"], line=dict(color=PALETTE[i % len(PALETTE)])))
    fig_radar.update_layout(template=PLOTLY_TEMPLATE, height=440,
                             polar=dict(radialaxis=dict(visible=True)),
                             margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown('<div class="section-title">Full Screen Results</div>', unsafe_allow_html=True)
    display_cols = ["Rank", "Ticker", "Name", "Sector", "Price", "P/E", "EV/EBITDA", "RevGrowth",
                     "ROE", "DebtEquity", "Mom6M", "CompositeScore"]
    show_df = scored[display_cols].rename(columns={
        "RevGrowth": "Rev Growth", "DebtEquity": "Debt/Equity", "Mom6M": "6M Momentum", "CompositeScore": "Composite Z"
    })
    st.dataframe(
        show_df.style.format({
            "Price": "${:,.2f}", "P/E": "{:,.1f}", "EV/EBITDA": "{:,.1f}",
            "Rev Growth": "{:+.1%}", "ROE": "{:+.1%}", "Debt/Equity": "{:,.1f}",
            "6M Momentum": "{:+.1%}", "Composite Z": "{:+.2f}",
        }),
        use_container_width=True, hide_index=True, height=420,
    )

# ===================== TAB 5 — PORTFOLIO LAB ================================
with tab_portfolio:
    st.markdown('<div class="section-title">Search &amp; Build Your Portfolio</div>', unsafe_allow_html=True)

    search_add = st.text_input("Search for a ticker to add (press Enter)", value="", key="ticker_search")
    if search_add:
        st.session_state.custom_universe.add(search_add.strip().upper())

    pool = sorted(set(tickers) | set(universe) | st.session_state.custom_universe)
    default_selection = [t for t in tickers if t in pool] or pool[:5]
    selected = st.multiselect("Selected holdings", options=pool, default=default_selection)

    if not selected:
        st.info("Select at least one ticker above to build a portfolio.")
    else:
        st.caption("Set weights (auto-normalised to 100%).")
        weight_cols = st.columns(min(len(selected), 6) or 1)
        raw_weights = {}
        for i, t in enumerate(selected):
            with weight_cols[i % len(weight_cols)]:
                raw_weights[t] = st.number_input(t, min_value=0.0, max_value=100.0,
                                                  value=round(100 / len(selected), 1), step=1.0, key=f"pw_{t}")
        total_w = sum(raw_weights.values()) or 1.0
        weights = {t: w / total_w for t, w in raw_weights.items()}

        price_frames, betas = {}, {}
        for t in selected:
            d = load_price_history(t, period="2y", interval="1d")
            if not d.empty:
                price_frames[t] = d.set_index("Date")["Close"]
            fi_t = load_fundamentals(t)
            betas[t] = fi_t.get("beta") or 1.0

        if price_frames:
            prices = pd.DataFrame(price_frames).dropna()
            returns = prices.pct_change().dropna()
            w_series = pd.Series(weights).reindex(returns.columns).fillna(0)

            port_returns = returns.dot(w_series)
            ann_return_hist = port_returns.mean() * 252
            ann_vol = port_returns.std() * np.sqrt(252)
            sharpe = (ann_return_hist - risk_free) / ann_vol if ann_vol else np.nan
            cum_port = (1 + port_returns).cumprod() - 1
            drawdown = ((1 + port_returns).cumprod() / (1 + port_returns).cumprod().cummax() - 1).min()

            capm_returns = {t: risk_free + betas[t] * equity_risk_premium for t in selected}
            port_capm_return = sum(weights[t] * capm_returns[t] for t in selected)

            st.markdown('<div class="section-title">Portfolio Statistics</div>', unsafe_allow_html=True)
            pcol1, pcol2, pcol3, pcol4, pcol5 = st.columns(5)
            for col, label, val in [
                (pcol1, "Historical Ann. Return", f"{ann_return_hist*100:,.2f}%"),
                (pcol2, "CAPM Expected Return", f"{port_capm_return*100:,.2f}%"),
                (pcol3, "Ann. Volatility", f"{ann_vol*100:,.2f}%"),
                (pcol4, "Sharpe Ratio", f"{sharpe:,.2f}"),
                (pcol5, "Max Drawdown", f"{drawdown*100:,.2f}%"),
            ]:
                with col:
                    st.markdown(f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
                        <div class="kpi-value" style="font-size:19px;">{val}</div></div>""", unsafe_allow_html=True)

            gcol1, gcol2 = st.columns([1.5, 1])
            with gcol1:
                st.markdown('<div class="section-title">Cumulative Historical Return</div>', unsafe_allow_html=True)
                fig_p = go.Figure()
                fig_p.add_trace(go.Scatter(x=cum_port.index, y=cum_port.values * 100, fill="tozeroy",
                                            line=dict(color=NAVY, width=2), fillcolor="rgba(11,31,58,0.10)", name="Portfolio"))
                fig_p.update_layout(template=PLOTLY_TEMPLATE, height=340, yaxis_title="Return (%)",
                                     margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_p, use_container_width=True)
            with gcol2:
                st.markdown('<div class="section-title">Allocation</div>', unsafe_allow_html=True)
                fig_pie = go.Figure(data=[go.Pie(labels=list(weights.keys()), values=list(weights.values()),
                                                  hole=0.55, marker=dict(colors=PALETTE))])
                fig_pie.update_layout(template=PLOTLY_TEMPLATE, height=340, margin=dict(l=10, r=10, t=10, b=10),
                                       showlegend=True, legend=dict(orientation="h", y=-0.15))
                st.plotly_chart(fig_pie, use_container_width=True)

            # ---------------- Monte Carlo return projection ----------------
            st.markdown('<div class="section-title">Monte Carlo Return Projection</div>', unsafe_allow_html=True)
            st.caption(
                "Simulates thousands of possible future paths using the portfolio's historical daily "
                "mean and covariance (correlated across holdings via Cholesky decomposition), then "
                "compounds forward. This is a statistical projection based on the recent past — not a "
                "forecast or guarantee of future performance."
            )
            mc1, mc2, mc3 = st.columns(3)
            horizon_years = mc1.slider("Horizon (years)", 1, 10, 5)
            n_sims = mc2.slider("Simulations", 200, 5000, 1500, 100)
            initial_investment = mc3.number_input("Initial investment ($)", value=10000, step=1000, min_value=100)

            mu_daily = returns.mean().values
            cov_daily = returns.cov().values
            try:
                L = np.linalg.cholesky(cov_daily + np.eye(len(mu_daily)) * 1e-12)
            except np.linalg.LinAlgError:
                L = np.linalg.cholesky(cov_daily + np.eye(len(mu_daily)) * 1e-6)

            n_days = int(horizon_years * 252)
            rng = np.random.default_rng(42)
            w_vec = w_series.values

            sim_paths = np.zeros((n_sims, n_days))
            for s in range(n_sims):
                z = rng.standard_normal((n_days, len(mu_daily)))
                correlated = z @ L.T + mu_daily
                daily_port_ret = correlated @ w_vec
                sim_paths[s] = np.cumprod(1 + daily_port_ret)

            sim_values = sim_paths * initial_investment
            pct5 = np.percentile(sim_values, 5, axis=0)
            pct25 = np.percentile(sim_values, 25, axis=0)
            pct50 = np.percentile(sim_values, 50, axis=0)
            pct75 = np.percentile(sim_values, 75, axis=0)
            pct95 = np.percentile(sim_values, 95, axis=0)
            x_days = np.arange(1, n_days + 1) / 252

            fig_mc = go.Figure()
            fig_mc.add_trace(go.Scatter(x=x_days, y=pct95, line=dict(width=0), showlegend=False, hoverinfo="skip"))
            fig_mc.add_trace(go.Scatter(x=x_days, y=pct5, fill="tonexty", fillcolor="rgba(11,31,58,0.08)",
                                         line=dict(width=0), name="5th–95th percentile"))
            fig_mc.add_trace(go.Scatter(x=x_days, y=pct75, line=dict(width=0), showlegend=False, hoverinfo="skip"))
            fig_mc.add_trace(go.Scatter(x=x_days, y=pct25, fill="tonexty", fillcolor="rgba(183,137,63,0.18)",
                                         line=dict(width=0), name="25th–75th percentile"))
            fig_mc.add_trace(go.Scatter(x=x_days, y=pct50, line=dict(color=NAVY, width=2.4), name="Median path"))
            fig_mc.update_layout(template=PLOTLY_TEMPLATE, height=420, xaxis_title="Years",
                                  yaxis_title="Portfolio Value ($)", margin=dict(l=10, r=10, t=10, b=10),
                                  legend=dict(orientation="h", y=1.05))
            st.plotly_chart(fig_mc, use_container_width=True)

            final_vals = sim_values[:, -1]
            prob_loss = (final_vals < initial_investment).mean() * 100
            mres1, mres2, mres3, mres4 = st.columns(4)
            for col, label, val in [
                (mres1, f"Median value @ {horizon_years}y", f"${np.median(final_vals):,.0f}"),
                (mres2, "5th percentile (bear)", f"${pct5[-1]:,.0f}"),
                (mres3, "95th percentile (bull)", f"${pct95[-1]:,.0f}"),
                (mres4, "Probability of loss", f"{prob_loss:.1f}%"),
            ]:
                with col:
                    st.markdown(f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
                        <div class="kpi-value" style="font-size:19px;">{val}</div></div>""", unsafe_allow_html=True)

            # ---------------- Monte Carlo efficient frontier ----------------
            st.markdown('<div class="section-title">Risk / Return Map — Random Portfolio Search</div>', unsafe_allow_html=True)
            st.caption(
                "5,000 random long-only weight combinations across your selected holdings, plotted by "
                "annualised return and volatility. The gold star is the highest-Sharpe combination found; "
                "the navy diamond is your current weighting."
            )
            n_rand = 5000
            rand_weights = rng.dirichlet(np.ones(len(selected)), size=n_rand)
            mu_ann = returns.mean().values * 252
            cov_ann = returns.cov().values * 252
            rand_rets = rand_weights @ mu_ann
            rand_vols = np.sqrt(np.einsum('ij,jk,ik->i', rand_weights, cov_ann, rand_weights))
            rand_sharpe = (rand_rets - risk_free) / rand_vols

            best_idx = int(np.argmax(rand_sharpe))
            best_w = rand_weights[best_idx]

            fig_ef = go.Figure()
            fig_ef.add_trace(go.Scatter(x=rand_vols * 100, y=rand_rets * 100, mode="markers",
                                         marker=dict(size=5, color=rand_sharpe, colorscale="Tealrose",
                                                     colorbar=dict(title="Sharpe"), showscale=True),
                                         name="Random portfolios"))
            fig_ef.add_trace(go.Scatter(x=[rand_vols[best_idx] * 100], y=[rand_rets[best_idx] * 100], mode="markers",
                                         marker=dict(size=18, color=GOLD, symbol="star", line=dict(width=1, color=NAVY)),
                                         name="Max Sharpe (found)"))
            fig_ef.add_trace(go.Scatter(x=[ann_vol * 100], y=[ann_return_hist * 100], mode="markers",
                                         marker=dict(size=16, color=NAVY, symbol="diamond", line=dict(width=1, color="#fff")),
                                         name="Your portfolio"))
            fig_ef.update_layout(template=PLOTLY_TEMPLATE, height=460, xaxis_title="Annualised Volatility (%)",
                                  yaxis_title="Annualised Return (%)", margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_ef, use_container_width=True)

            st.markdown('<div class="section-title">Suggested Higher-Sharpe Weighting (Search Result)</div>', unsafe_allow_html=True)
            best_df = pd.DataFrame({"Ticker": selected, "Suggested Weight": best_w * 100,
                                     "Your Weight": [weights[t] * 100 for t in selected]})
            st.dataframe(best_df.style.format({"Suggested Weight": "{:.1f}%", "Your Weight": "{:.1f}%"}),
                         use_container_width=True, hide_index=True)

    st.markdown(
        """<div class="verdict-box" style="margin-top:14px;">
        <b>Disclosure:</b> All figures are generated from delayed/real-time public market data for
        research and educational purposes only. Historical returns, CAPM estimates, and Monte Carlo
        simulations rely on backward-looking data and simplifying assumptions (e.g. normally distributed
        returns, stable correlations) that will not hold exactly in the future. Nothing in this terminal
        constitutes investment advice or a recommendation to buy or sell any security.</div>""",
        unsafe_allow_html=True,
    )
