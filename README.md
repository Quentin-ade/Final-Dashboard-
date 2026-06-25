# Sovereign Equity Research & Portfolio Optimization Terminal

**Architect & Software Engineer:** Quentin Adeniran  
**Target Infrastructure:** Multi-Factor Risk Matrixing, Dynamic Capital Sizing, and Quantitative Asset Allocation

---

## 🏛️ System Summary & Structural Integrity
This repository contains a high-utility, interactive financial terminal designed to model global equities, cross-asset benchmarks, and risk-bucketed investment portfolios. Engineered with parallel multi-threaded concurrency models via Python, the system scrapes real-time metrics across 100+ high-liquidity international tickers. It allows buy-side analysts or asset managers to input unique user profiles, simulate share/warrant position sizing configurations, and run asset tracking against real-time benchmark index feeds ($S\&P 500$, $NASDAQ 100$, $FTSE 100$).

### 🔬 Methodological Finance Innovations
* **Personalised Strategy Profiling:** Automatically parses financial metrics to dynamically sort assets into unique risk buckets matching explicit user criteria (Conservative, Balanced, or Aggressive Expansion tracks).
* **Capital Position Sizing Simulator:** Embeds an execution calculator evaluating exact cash commitments, intrinsic dollar distributions, and user-defined target return percentages on live spot inputs.
* **Organic Capital Growth Vector:** Calculates early-stage cash distributions utilizing firm-specific structural metrics ($\text{Growth} = \text{ROE} \times (1 - \text{Payout Ratio})$) instead of arbitrary straight-line assumptions.
* **Multi-Scenario Sensitivity Matrix:** Evaluates target asset intrinsic values under severe capital stress variations across custom WACC rate structures and perpetual growth assumptions.

---

## 🛠️ Repository Mapping & Dependencies
Ensure your development folder structure exactly mirrors the environment layout below:

├── .streamlit/
│   └── config.toml          # Enforces Core Institutional Dark Theme UI
├── app.py                   # Central Terminal Application Script
├── requirements.txt         # Package Dependency Allocation Array
└── README.md                # Structural System Documentation

### Local Deployment Sequence
1. Clone the repository structure:
   ```bash
   git clone https://github.com
   cd YOUR_REPO_NAME
   ```
2. Deploy the verified configuration dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the visual dashboard server locally:
   ```bash
   streamlit run app.py
   ```

---
*Disclaimer: This analytics platform operates strictly as an structural financial modeling exploration space and does not constitute formal fiduciary, investment banking, or legal asset management counsel.*
