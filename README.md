# 🏛️ Sovereign Capital Management Terminal

A professional, institutional-grade financial analysis dashboard built with Streamlit for stock valuation, screening, and portfolio recommendations.

## ✨ Features

### Core Functionality
- **📊 DCF Valuation Model**: Discounted cash flow analysis with customizable WACC and terminal growth rates
- **🔬 Multi-Factor Rating System**: Evaluates stocks based on valuation, volatility (Beta), and P/E multiples
- **📈 Stock Screening Tool**: Filter 100+ institutional stocks by verdict, sector, and rating
- **💼 Portfolio Recommendations**: Get investment recommendations based on your risk profile
- **💰 Position Sizing Calculator**: Calculate expected returns and position sizes
- **🧮 Valuation Sensitivity Analysis**: Stress-test valuations with different assumptions
- **📊 Interactive Charts**: 1-year price history with moving averages and volume

### Data Coverage
- **100+ High-Liquidity Equities** across sectors:
  - Technology & Semiconductors
  - Financials & Banking
  - Energy & Industrials
  - Healthcare & Pharma
  - Consumer & Defensive Stocks
- **Real-Time Market Data** from Yahoo Finance
- **Major Benchmark Indices**: S&P 500, NASDAQ-100, FTSE 100

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Install Dependencies

```bash
pip install streamlit yfinance pandas numpy plotly requests
```

### Step 2: Download the App

Save the `sovereign_capital_dashboard.py` file to your desired directory.

### Step 3: Run the App

```bash
streamlit run sovereign_capital_dashboard.py
```

The app will open in your default browser at `http://localhost:8501`

## 📖 User Guide

### Dashboard Controls (Sidebar)

#### 1. **Valuation Parameters**
- **WACC (4-16%)**: Discount rate for future cash flows
  - Higher = More conservative valuation
  - Typical range: 7-10% for established companies
  - Use higher for riskier companies
  
- **Terminal Growth Rate (0.5-4.5%)**: Long-term perpetual growth assumption
  - Typically matches GDP growth (2-3%)
  - Should be lower than long-term economic growth

#### 2. **Quick Stock Selection**
- Pre-loaded buttons for popular stocks (NVDA, LLY, MSFT)
- Click any button to instantly analyze that stock

#### 3. **Stock Search**
- Enter any ticker symbol (AAPL, GOOGL, JPM, etc.)
- Searches Yahoo Finance database

### Main Dashboard Features

#### Market Overview
- Real-time price and % change for major indices
- Helps contextualize individual stock performance

#### Stock Screening Tool
**Filter by:**
- **Verdict**: Strong Buy (🟢), Buy, Hold (🟡), Sell (🔴)
- **Sector**: Technology, Financials, Energy, Healthcare, Consumer
- **Rating**: 1-5 star minimum rating threshold

**Results Table Shows:**
- Current Price vs. DCF Intrinsic Value
- Implied Upside %: Expected return to intrinsic value
- Rating: Multi-factor quality score
- Beta: Volatility relative to market

#### Deep Dive Analysis

**Key Metrics Display:**
- **Current Price**: Latest stock price
- **DCF Value**: Intrinsic value based on DCF model
- **Upside Potential**: % gain to intrinsic value
- **Rating**: 1-5 star rating
- **Verdict**: Investment recommendation

**Position Sizing Calculator:**
- Input number of shares to buy
- Set your target exit price
- See total investment and expected ROI

**Price Chart:**
- 1-year candlestick chart
- 50-day and 200-day moving averages
- Volume bars below price chart

**Valuation Sensitivity Table:**
- Shows how valuation changes with ±1% WACC change
- Shows how valuation changes with ±0.5% terminal growth change
- Helps understand valuation range

#### Portfolio Recommendations

**Risk Profiles:**

1. **🛡️ Conservative**
   - Low volatility stocks (Beta ≤ 1.0)
   - Stable cash flows
   - Best for: Capital preservation, income investors
   - Example stocks: WMT, COST, PG

2. **⚖️ Balanced**
   - Moderate volatility (0.8 < Beta < 1.3)
   - Mix of growth and stability
   - Best for: Most investors
   - Example stocks: MSFT, GOOGL, JPM

3. **🚀 Aggressive**
   - High volatility (Beta > 1.2)
   - Growth potential
   - Best for: Risk-tolerant investors
   - Example stocks: NVDA, TSLA, CRM

## 📊 Understanding the Metrics

### DCF Intrinsic Value
**What it is:** Fair value based on projected future cash flows
- Discounted at your WACC rate
- Assumes 5-year explicit growth period
- Terminal value based on perpetual growth rate

**How to use:**
- If Current Price < DCF Value: Stock may be undervalued
- If Current Price > DCF Value: Stock may be overvalued
- Larger gap = More potential upside/downside

### Rating System (1-5 Stars)

Factors considered:
1. **Valuation (Max 2.0 pts)**
   - 2.0 pts: 35%+ margin of safety
   - 1.5 pts: 15-35% margin of safety
   - 1.0 pts: 0-15% margin of safety
   - 0.5 pts: -15% to 0% (slightly overvalued)

2. **Risk/Volatility (Max 1.5 pts)**
   - 1.5 pts: Low Beta (< 0.85)
   - 1.0 pts: Moderate Beta (0.85-1.20)
   - 0.5 pts: High Beta (1.20-1.60)

3. **Earnings Yield (Max 1.5 pts)**
   - 1.5 pts: Low P/E (< 16x)
   - 1.0 pts: Moderate P/E (16-28x)
   - 0.5 pts: High P/E (28-45x)

**Total Rating:** Sum of all factors (1-5 stars)

### Beta
- **β = 1.0**: Stock moves with the market
- **β < 1.0**: Less volatile (defensive)
- **β > 1.0**: More volatile (aggressive)
- Used to adjust WACC for individual stocks

### P/E Ratio
- **Price ÷ Earnings per share**
- Lower = Potentially better value
- Higher = Market expects more growth
- Compare within same sector

### Implied Upside %
- Expected return from current price to DCF value
- Positive = Potential gain
- Negative = Potential loss

## 🎯 Investment Strategies

### Value Investing (Conservative)
1. Filter for High Rating (4+)
2. Look for High Implied Upside (15%+)
3. Choose Conservative risk profile
4. Focus on low Beta stocks

### Growth Investing (Aggressive)
1. Filter for Technology/Healthcare sectors
2. Accept higher Beta (1.2+)
3. Choose Aggressive risk profile
4. Look for 20%+ implied upside

### Balanced Approach
1. Use Balanced risk profile
2. Filter for Rating 3+
3. Mix of sectors
4. Target 10-15% implied upside
5. Diversify across 5-10 positions

## 🔧 Troubleshooting

### "Error loading market data"
- **Cause**: Internet connection or Yahoo Finance API issue
- **Solution**: 
  - Check internet connection
  - Restart the app (stop with Ctrl+C, run again)
  - Wait a few minutes and retry (API rate limits)

### Chart not displaying
- **Cause**: Insufficient historical data for ticker
- **Solution**: Use a major stock (AAPL, MSFT) instead

### Valuation seems too high/low
- **Cause**: Incorrect WACC or terminal growth assumptions
- **Solution**: 
  - Adjust WACC to match your required return
  - Review company fundamentals
  - Compare to historical P/E ratio

### Stock not found
- **Cause**: Invalid ticker symbol or stock delisted
- **Solution**: 
  - Double-check ticker spelling (Yahoo Finance format)
  - Try a different stock

## 📋 Key Formulas

### DCF Valuation
```
Intrinsic Value = (Sum of Discounted FCF) + (Discounted Terminal Value)
                  ÷ Shares Outstanding

Where:
- Discount Rate = WACC
- Terminal Value = (Final Year FCF × (1 + Terminal Growth)) / (WACC - Terminal Growth)
```

### Fundamental Growth Rate
```
Growth Rate = ROE × (1 - Payout Ratio)

Example:
- ROE = 20%, Payout = 30%
- Growth = 20% × 70% = 14% sustainable growth
```

### Margin of Safety
```
Margin of Safety % = (Intrinsic Value - Current Price) / Current Price × 100

Example:
- Intrinsic = $150, Price = $100
- MOS = ($150 - $100) / $100 = 50% safety margin
```

## 📚 Investment Education Resources

### Recommended Reading
- "The Intelligent Investor" - Benjamin Graham (Value investing fundamentals)
- "Security Analysis" - Graham & Dodd (Deep analysis techniques)
- "Valuation: Measuring and Managing the Value of Companies" - McKinsey

### Websites
- Investor.gov: SEC investor education
- Yahoo Finance: Free stock data and research
- Seeking Alpha: Stock analysis and discussions

## ⚠️ Important Disclaimers

1. **Educational Purpose Only**: This tool is for learning and research only
2. **Not Financial Advice**: Not a substitute for professional financial advice
3. **Past Performance**: Historical returns don't guarantee future results
4. **Data Accuracy**: Data sourced from Yahoo Finance; verify independently
5. **Model Limitations**: DCF models depend heavily on assumptions
6. **Diversification**: Always diversify your portfolio
7. **Risk Acknowledgment**: All investments carry risk including loss of principal

## 🔒 Data Privacy

- Your inputs (WACC, terminal growth) are NOT stored
- Search history NOT tracked
- No personal information collected
- All data comes from public Yahoo Finance API

## 🛠️ Technical Details

### Stack
- **Frontend**: Streamlit (Python web framework)
- **Data**: yfinance (Yahoo Finance API)
- **Charts**: Plotly (interactive visualization)
- **Computation**: pandas, numpy

### Performance
- Data cached for 30 minutes (TTL=1800)
- Parallel data fetching (25 concurrent workers)
- 100+ stocks loaded in ~10-15 seconds

### API Limits
- Yahoo Finance: No official rate limits (Best effort)
- Streamlit caching reduces API calls by 90%
- If throttled: Wait 30+ minutes before retry

## 📞 Support & Feedback

### Bug Reports
If you encounter errors:
1. Note the exact error message
2. Include the stock ticker and parameters used
3. Check if error reproduces with different stock
4. Share the full error trace

### Feature Requests
- Position allocation optimization
- Portfolio backtesting
- Options analysis
- Dividend tracking
- Tax-loss harvesting calculator

## 📈 Version History

### v2.0 (Current)
- ✅ Fixed all variable reference errors
- ✅ Corrected master_df creation
- ✅ Improved error handling
- ✅ Better tooltips and explanations
- ✅ Enhanced UI/UX
- ✅ Better code documentation
- ✅ Simplified filtering logic

### v1.0
- Initial release with DCF model
- Stock screening
- Basic visualization

## 📄 License

Open source for educational use. Modify and share freely with attribution.

---

**Happy investing! 🚀**

*Remember: The best investment is in yourself. Continue learning.*
