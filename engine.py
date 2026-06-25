import yfinance as yf
import pandas as pd
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor

# Unified 100+ Global Asset Universe Definition
INSTITUTIONAL_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL", "AMD", 
    "NFLX", "CRM", "ADBE", "CSCO", "INTC", "QCOM", "TXN", "AMAT", "MU", "LRCX",
    "ASML", "PANW", "SNOW", "PLTR", "NOW", "WDAY", "TEAM", "DDOG", "CRWD", "SQ",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "V", "MA", "PYPL", 
    "BLK", "BX", "KKR", "APO", "SCHW", "UBS", "HSBA.L", "BARC.L", "LLOY.L", "NWG.L",
    "XOM", "CVX", "SHEL.L", "BP.L", "COP", "CAT", "GE", "HON", "UNP", "LMT", 
    "RTX", "NOC", "BA", "DE", "MMM", "FDX", "UPS", "NSC", "CSX", "EMR",
    "LLY", "NVO", "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "DHR", "ABT", 
    "BMY", "AMGN", "GILD", "ISRG", "VRTX", "REGN", "MDT", "AZN.L", "GSK.L", "HCA",
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "EL", "CL", "PG", 
    "KO", "PEP", "PM", "MO", "MDLZ", "MC.PA", "OR.PA", "RMS.PA", "BABA", "PDD"
]

custom_session = requests.Session()
custom_session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

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
        roe = info.get('returnOnEquity') or 0.12 
        payout = info.get('payoutRatio') or 0.20
        
        return {
            "Ticker": symbol, "Name": info.get('longName', symbol),
            "Sector": info.get('sector', 'Global Universe'), "Price": float(price),
            "FCF": float(fcf), "Shares": float(shares), "Beta": float(beta), "PE": float(pe),
            "ROE": float(roe), "Payout": float(payout)
        }
    except Exception:
        return None

def process_full_universe(ticker_list):
    """Executes parallel compilation across the target security universe."""
    compiled = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        results = executor.map(fetch_asset_metrics, ticker_list)
        for r in results:
            if r is not None:
                compiled.append(r)
    return pd.DataFrame(compiled)

def run_multistage_dcf(fcf, shares, wacc_pct, pgr_pct, roe, payout, periods=5):
    """Computes a multi-stage Free Cash Flow Discount model utilizing fundamental reinvestment."""
    wacc = wacc_pct / 100.0
    g_terminal = pgr_pct / 100.0
    if wacc <= g_terminal: 
        return 0.0
        
    fundamental_g = max(min(roe * (1 - payout), 0.18), 0.03)
    discounted_fcf_sum = 0.0
    current_fcf = fcf if fcf > 0 else (shares * 2.50)
    
    for t in range(1, periods + 1):
        growth_factor = fundamental_g - ((fundamental_g - g_terminal) * (t / periods))
        current_fcf *= (1 + growth_factor)
        discounted_fcf_sum += current_fcf / ((1 + wacc) ** t)
        
    terminal_val = (current_fcf * (1 + g_terminal)) / (wacc - g_terminal)
    discounted_tv = terminal_val / ((1 + wacc) ** periods)
    
    return max((discounted_fcf_sum + discounted_tv) / shares, 0.0)

def compute_institutional_rating(price, intrinsic, beta, pe):
    """Deconstructs asset metrics to produce a multi-factor transparent risk rating."""
    if price <= 0:
        return 1.0, "EXCLUDED", ["Asset exhibits negative execution price foundations."]
        
    margin_of_safety = ((intrinsic - price) / price) * 100.0
    score_cards = []
    
    val_pts = 0.0
    if margin_of_safety >= 35.0: val_pts = 2.0
    elif margin_of_safety >= 15.0: val_pts = 1.5
    elif margin_of_safety >= 0.0: val_pts = 1.0
    elif margin_of_safety >= -15.0: val_pts = 0.5
    score_cards.append(f"Valuation Premium Matrix: Implied Margin of Safety of {margin_of_safety:.1f}% yields {val_pts} points.")
    
    risk_pts = 0.0
    if beta < 0.85: risk_pts = 1.5
    elif beta <= 1.20: risk_pts = 1.0
    elif beta <= 1.60: risk_pts = 0.5
    score_cards.append(f"Systematic Capital Protection: Asset Beta of {beta:.2f}x contributes {risk_pts} points.")
    
    multiple_pts = 0.0
    if 0 < pe <= 16.0: multiple_pts = 1.5
    elif 16.0 < pe <= 28.0: multiple_pts = 1.0
    elif 28.0 < pe <= 45.0: multiple_pts = 0.5
    score_cards.append(f"Earnings Yield Multiplier: Trailing P/E Multiple of {pe:.1f}x adds {multiple_pts} points.")
    
    final_rating = max(min(round(val_pts + risk_pts + multiple_pts, 1), 5.0), 1.0)
    
    if final_rating >= 4.2: verdict = "ASYMMETRIC BUY"
    elif final_rating >= 3.4: verdict = "ACCUMULATE RISK-WEIGHTED"
    elif final_rating >= 2.4: verdict = "HOLD / NEUTRAL HOLDING"
    else: verdict = "UNDERWEIGHT / REDUCE EXPOSURE"
         
    return final_rating, verdict, score_cards
