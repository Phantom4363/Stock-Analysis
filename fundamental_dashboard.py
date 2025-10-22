import streamlit as st
import yfinance as yf
import pandas as pd

# --- Helper: Safe formatting function ---
def format_value(value, decimals=2, pad=10, is_percentage=False):
    if value is None:
        return "N/A".ljust(pad)
    if is_percentage:
        value *= 100  # convert decimal to %
        return f"{value:.{decimals}f}%".ljust(pad)
    return f"{value:.{decimals}f}".ljust(pad)

# --- Helper: Safe metric extraction ---
def safe_get(info, key, default=None):
    try:
        val = info.get(key, default)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return default
        return val
    except Exception:
        return default

# --- Streamlit setup ---
st.set_page_config(page_title="Fundamental Stock Analysis Dashboard", layout="wide")
st.title("📊 Fundamental Stock Analysis Dashboard")

# --- Input ---
ticker_input = st.text_input("Enter a stock ticker symbol (e.g., AAPL, MSFT, TSLA):", "AAPL").upper()
ticker = yf.Ticker(ticker_input)

# --- Try multiple info sources ---
try:
    info = ticker.get_info()
    if not info:  # fallback if empty
        info = ticker.fast_info
except Exception:
    info = {}

if not info:
    st.error("Failed to retrieve data. Try another ticker.")
    st.stop()

# --- Extract metrics safely ---
market_cap = safe_get(info, "marketCap") or safe_get(info, "market_cap")
trailing_pe = safe_get(info, "trailingPE") or safe_get(info, "trailing_pe")
forward_pe = safe_get(info, "forwardPE") or safe_get(info, "forward_pe")
peg_ratio = safe_get(info, "pegRatio")
roe = safe_get(info, "returnOnEquity")
profit_margin = safe_get(info, "profitMargins")
dividend_yield = safe_get(info, "dividendYield") or safe_get(info, "dividend_yield")
operating_margin = safe_get(info, "operatingMargins")
debt_to_equity = safe_get(info, "debtToEquity")

# --- Convert ratios ---
if isinstance(roe, (int, float)): roe *= 100
if isinstance(profit_margin, (int, float)): profit_margin *= 100
if isinstance(operating_margin, (int, float)): operating_margin *= 100
if isinstance(debt_to_equity, (int, float)): debt_to_equity /= 100

# --- Display Overview ---
st.header(f"Company Overview: {ticker_input}")
col1, col2, col3 = st.columns(3)
col1.metric("Market Cap", f"${market_cap:,.0f}" if market_cap else "N/A")
col2.metric("Trailing P/E", f"{trailing_pe:.2f}" if trailing_pe else "N/A")
col3.metric("Forward P/E", f"{forward_pe:.2f}" if forward_pe else "N/A")

st.divider()

# --- Key Ratios ---
st.header("📈 Key Ratios and Profitability")
st.write("Return on Equity (ROE): ", format_value(roe, 2, 10, is_percentage=True), unsafe_allow_html=True)
st.write("Profit Margin: ", format_value(profit_margin, 2, 10, is_percentage=True), unsafe_allow_html=True)
st.write(
    "Dividend Yield: ",
    format_value(dividend_yield if isinstance(dividend_yield, (int, float)) else None, 2, 10, is_percentage=True),
    unsafe_allow_html=True
)
st.write("Operating Margin: ", format_value(operating_margin, 2, 10, is_percentage=True), unsafe_allow_html=True)
st.write("Debt-to-Equity Ratio: ", format_value(debt_to_equity, 2, 10), unsafe_allow_html=True)
st.write("PEG Ratio: ", format_value(peg_ratio, 2, 10), unsafe_allow_html=True)

st.divider()

# --- Scoring logic ---
def score_pe(pe):
    if pe is None: return 0
    if pe < 10: return 10
    elif pe < 20: return 8
    elif pe < 30: return 6
    elif pe < 40: return 4
    else: return 2

def score_roe(roe):
    if roe is None: return 0
    if roe > 30: return 10
    elif roe > 20: return 8
    elif roe > 10: return 6
    elif roe > 5: return 4
    else: return 2

def score_profit_margin(pm):
    if pm is None: return 0
    if pm > 30: return 10
    elif pm > 20: return 8
    elif pm > 10: return 6
    elif pm > 5: return 4
    else: return 2

def score_dividend_yield(dy):
    if dy is None: return 0
    dy *= 100
    if dy > 5: return 10
    elif dy > 3: return 8
    elif dy > 2: return 6
    elif dy > 1: return 4
    else: return 2

def score_peg(peg):
    if peg is None: return 0
    if peg < 1: return 10
    elif peg < 1.5: return 8
    elif peg < 2: return 6
    elif peg < 3: return 4
    else: return 2

def score_debt_to_equity(de):
    if de is None: return 0
    if de < 0.3: return 10
    elif de < 0.5: return 8
    elif de < 1: return 6
    elif de < 2: return 4
    else: return 2

# --- Calculate overall score ---
scores = [
    score_pe(trailing_pe),
    score_roe(roe),
    score_profit_margin(profit_margin),
    score_dividend_yield(dividend_yield),
    score_peg(peg_ratio),
    score_debt_to_equity(debt_to_equity)
]

overall_score = sum(scores) / len(scores) if len(scores) > 0 else 0

st.header("📊 Fundamental Strength Score")
st.progress(int(overall_score * 10))
st.write(f"**Overall Score: {overall_score:.2f}/10**")

if overall_score >= 8:
    st.success("✅ Strong fundamentals — potential high-quality stock!")
elif overall_score >= 5:
    st.warning("⚠️ Mixed fundamentals — further analysis recommended.")
else:
    st.error("❌ Weak fundamentals — proceed with caution.")



