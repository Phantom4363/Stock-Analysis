import yfinance as yf
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================================
# Helpers: formatting
# =========================================
def format_value(value, low, high, is_percentage=False, multiplier=1):
    if value == "N/A" or value is None:
        return f"<span style='color:gray;'>N/A</span>"
    value *= multiplier
    if low <= value <= high:
        return f"<span style='color:green;'>{value:.2f}%</span>" if is_percentage else f"<span style='color:green;'>{value:.2f}</span>"
    else:
        return f"<span style='color:red;'>{value:.2f}%</span>" if is_percentage else f"<span style='color:red;'>{value:.2f}</span>"

def compare_to_sector(company_value, sector_value, higher_is_better=True):
    if company_value == "N/A" or company_value is None or sector_value is None:
        return f"<span style='color:gray;'>N/A</span>"
    if higher_is_better:
        color = "green" if company_value > sector_value else "red"
    else:
        color = "green" if company_value < sector_value else "red"
    return f"<span style='color:{color};'>{company_value:.2f}</span> (vs. {sector_value:.2f})"

def _num(x):
    return x if isinstance(x, (int, float, np.number)) else None

# =========================================
# Scoring helpers (0–100 for each metric)
# =========================================
def score_lower_is_better(value, target, loose_high):
    v = _num(value)
    if v is None:
        return None
    if v <= target:
        return 100.0
    if v >= loose_high:
        return 0.0
    return max(0.0, 100.0 * (1 - (v - target) / (loose_high - target)))

def score_higher_is_better(value, target, loose_low):
    v = _num(value)
    if v is None:
        return None
    if v >= target:
        return 100.0
    if v <= loose_low:
        return 0.0
    return max(0.0, 100.0 * ((v - loose_low) / (target - loose_low)))

def score_within_band_best(value, low, high, hard_low=None, hard_high=None):
    v = _num(value)
    if v is None:
        return None
    if low <= v <= high:
        return 100.0
    if hard_low is None:
        hard_low = low - (high - low)
    if hard_high is None:
        hard_high = high + (high - low)
    if v < low:
        if v <= hard_low:
            return 0.0
        return max(0.0, 100.0 * (v - hard_low) / (low - hard_low))
    else:
        if v >= hard_high:
            return 0.0
        return max(0.0, 100.0 * (hard_high - v) / (hard_high - high))

def score_beta(beta):
    return score_within_band_best(beta, low=0.8, high=1.2, hard_low=0.4, hard_high=1.8)

def score_dividend_yield(y):
    v = _num(y)
    if v is None:
        return None
    return max(0.0, min(100.0, (v / 3.0) * 100.0)) if v <= 6 else 100.0

def score_revenue_growth(g):
    v = _num(g)
    if v is None:
        return None
    if v >= 20:
        return 100.0
    if v >= 10:
        return 70.0 + (v - 10) * 3.0
    if v >= 0:
        return 40.0 + v * 3.0
    if v <= -20:
        return 0.0
    return max(0.0, 40.0 + (v * 2.0))

# =========================================
# Streamlit UI
# =========================================
st.title("📊 Fundamental Stock Analysis Dashboard")
ticker_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT)", "AAPL")
stock = yf.Ticker(ticker_symbol)

st.header(f"Financial Data for {ticker_symbol}")

# --- Fetch stock info ---
fast_info = stock.fast_info if hasattr(stock, "fast_info") else {}
try:
    info = stock.get_info()
except Exception:
    info = {}

current_price = fast_info.get("lastPrice", info.get("currentPrice", None))
sector = info.get("sector", "Unknown")
pe_ratio = fast_info.get("peRatio", info.get("trailingPE", "N/A"))
pb_ratio = fast_info.get("priceToBook", "N/A")
roe = info.get("returnOnEquity", "N/A")
debt_to_equity = info.get("debtToEquity", "N/A")
market_cap = info.get("marketCap", "N/A")
profit_margin = info.get("profitMargins", "N/A")
dividend_yield = info.get("dividendYield", "N/A")
if isinstance(dividend_yield, (int, float)):
    dividend_yield /= 100
operating_margin = info.get("operatingMargins", "N/A")
beta = info.get("beta", "N/A")
current_ratio = info.get("currentRatio", "N/A")

# --- Convert ratios to percentages where needed ---
if isinstance(roe, (int, float)):
    roe *= 100
if isinstance(profit_margin, (int, float)):
    profit_margin *= 100
if isinstance(dividend_yield, (int, float)):
    dividend_yield *= 100
if isinstance(operating_margin, (int, float)):
    operating_margin *= 100
if isinstance(debt_to_equity, (int, float)):
    debt_to_equity /= 100

# =========================================
# NEW: Show Key Metrics at Top
# =========================================
st.subheader("🔑 Key Stock Metrics")
if current_price:
    st.write(f"**Current Price:** ${current_price:.2f}")
else:
    st.write("**Current Price:** N/A")
if pe_ratio and pe_ratio != "N/A":
    st.write(f"**P/E Ratio:** {pe_ratio:.2f}")
else:
    st.write("**P/E Ratio:** N/A")
if pb_ratio and pb_ratio != "N/A":
    st.write(f"**P/B Ratio:** {pb_ratio:.2f}")
else:
    st.write("**P/B Ratio:** N/A")

# =========================================
# Sector Benchmarks
# =========================================
sector_benchmarks = {
    "Technology": {"PE": 25, "PB": 6, "ROE": 18, "ProfitMargin": 15},
    "Healthcare": {"PE": 20, "PB": 4, "ROE": 14, "ProfitMargin": 12},
    "Financial Services": {"PE": 14, "PB": 1.5, "ROE": 10, "ProfitMargin": 20},
    "Consumer Defensive": {"PE": 22, "PB": 3.5, "ROE": 15, "ProfitMargin": 10},
    "Industrials": {"PE": 18, "PB": 2.5, "ROE": 12, "ProfitMargin": 8},
    "Energy": {"PE": 12, "PB": 1.8, "ROE": 16, "ProfitMargin": 10},
    "Unknown": {"PE": 20, "PB": 3, "ROE": 12, "ProfitMargin": 10}
}
benchmarks = sector_benchmarks.get(sector, sector_benchmarks["Unknown"])

# =========================================
# Compute Revenue Growth (YoY)
# =========================================
rev_growth = None
try:
    revenue_data = stock.financials.loc['Total Revenue']
    if len(revenue_data) >= 2:
        recent = float(revenue_data.iloc[0])
        previous = float(revenue_data.iloc[1])
        if previous != 0:
            rev_growth = ((recent - previous) / previous) * 100
except Exception:
    pass

# =========================================
# Scoring Engine
# =========================================
def compute_scores():
    details = {}
    reasons_pos, reasons_neg = [], []

    s_pe = score_lower_is_better(pe_ratio, target=benchmarks["PE"], loose_high=max(benchmarks["PE"] * 2.5, 10))
    s_pb = score_lower_is_better(pb_ratio, target=benchmarks["PB"], loose_high=max(benchmarks["PB"] * 3.0, 5))
    s_roe = score_higher_is_better(roe, target=benchmarks["ROE"], loose_low=0)
    pm = profit_margin if _num(profit_margin) is not None else operating_margin
    s_margin = score_higher_is_better(pm, target=benchmarks["ProfitMargin"], loose_low=0)
    s_growth = score_revenue_growth(rev_growth)
    s_de = score_lower_is_better(debt_to_equity, target=0.5, loose_high=3.0)
    s_cr = score_within_band_best(current_ratio, low=1.5, high=3.0, hard_low=0.8, hard_high=5.0)
    s_beta = score_beta(beta)
    s_div = score_dividend_yield(dividend_yield)

    components = {
        "Valuation (PE)": (s_pe, 0.20),
        "Valuation (PB)": (s_pb, 0.10),
        "Profitability (ROE)": (s_roe, 0.15),
        "Profitability (Margins)": (s_margin, 0.10),
        "Growth (Revenue YoY)": (s_growth, 0.20),
        "Health (Debt/Equity)": (s_de, 0.08),
        "Health (Current Ratio)": (s_cr, 0.07),
        "Stability (Beta)": (s_beta, 0.05),
        "Income (Dividend Yield)": (s_div, 0.05),
    }

    total_weight_available = sum(w for s, w in components.values() if s is not None and not np.isnan(s))
    if total_weight_available == 0:
        return 0.0, {}, ["No sufficient data to score."]

    overall = 0.0
    for name, (s, w) in components.items():
        if s is None or np.isnan(s):
            continue
        adj_w = w / total_weight_available
        overall += s * adj_w
        details[name] = round(s, 1)
        if s >= 75:
            reasons_pos.append(f"{name} strong ({s:.0f})")
        elif s <= 35:
            reasons_neg.append(f"{name} weak ({s:.0f})")

    reasons = []
    if reasons_pos:
        reasons.append("Strengths: " + ", ".join(reasons_pos))
    if reasons_neg:
        reasons.append("Watch-outs: " + ", ".join(reasons_neg))
    return round(overall, 1), details, reasons

overall_score, detail_scores, reasons = compute_scores()

def label_from_score(score: float):
    if score >= 80:
        return "BUY", "green", "✅"
    if score >= 60:
        return "HOLD", "orange", "🟨"
    return "SELL", "red", "⛔"

label, color, icon = label_from_score(overall_score)

# =========================================
# Display Metrics + Analysis
# =========================================
st.subheader("📈 Full Financial Metrics")
st.write("P/E Ratio: ", format_value(pe_ratio, 15, 25), unsafe_allow_html=True)
st.write("P/B Ratio: ", format_value(pb_ratio, 1, 3), unsafe_allow_html=True)
st.write("Return on Equity (ROE): ", format_value(roe, 10, 20, is_percentage=True), unsafe_allow_html=True)
st.write("Debt-to-Equity Ratio: ", format_value(debt_to_equity, 0.5, 1.5), unsafe_allow_html=True)
st.write("Profit Margin: ", format_value(profit_margin, 10, 20, is_percentage=True), unsafe_allow_html=True)
st.write("Dividend Yield: ", format_value(dividend_yield, 2, 10, is_percentage=True), unsafe_allow_html=True)
st.write("Operating Margin: ", format_value(operating_margin, 15, 25, is_percentage=True), unsafe_allow_html=True)
st.write("Beta: ", format_value(beta, 0.8, 1.2), unsafe_allow_html=True)
st.write("Current Ratio: ", format_value(current_ratio, 1.5, 3), unsafe_allow_html=True)
st.write("Market Capitalization: $", market_cap)

if rev_growth is not None:
    st.write("Revenue Growth (YoY): ", format_value(rev_growth, 10, 100, is_percentage=True), unsafe_allow_html=True)
else:
    st.write("Revenue Growth (YoY): <span style='color:gray;'>N/A</span>", unsafe_allow_html=True)

# =========================================
# Sector Benchmark Comparison
# =========================================
st.subheader(f"📉 Sector Comparison ({sector})")
st.markdown("**P/E Ratio:** " + compare_to_sector(pe_ratio, benchmarks["PE"], higher_is_better=False), unsafe_allow_html=True)
st.markdown("**P/B Ratio:** " + compare_to_sector(pb_ratio, benchmarks["PB"], higher_is_better=False), unsafe_allow_html=True)
st.markdown("**Return on Equity (ROE):** " + compare_to_sector(roe, benchmarks["ROE"], higher_is_better=True), unsafe_allow_html=True)
st.markdown("**Profit Margin:** " + compare_to_sector(profit_margin if _num(profit_margin) is not None else operating_margin, benchmarks["ProfitMargin"], higher_is_better=True), unsafe_allow_html=True)

# =========================================
# Rating & Signal
# =========================================
st.subheader("🧭 Rating & Signal")
st.markdown(
    f"<div style='padding:12px;border-radius:10px;border:1px solid #ddd;'>"
    f"<div style='font-size:22px;font-weight:700;'>Overall Rating: {overall_score:.1f} / 100</div>"
    f"<div style='font-size:20px;margin-top:6px;'>Signal: {icon} "
    f"<span style='color:{color};font-weight:700;'>{label}</span></div>"
    f"</div>",
    unsafe_allow_html=True
)

if detail_scores:
    st.markdown("**Component Scores**")
    df_scores = pd.DataFrame(
        {"Component": list(detail_scores.keys()), "Score": list(detail_scores.values())}
    ).sort_values("Score", ascending=False)
    st.dataframe(df_scores, use_container_width=True)

for r in reasons:
    st.write("• " + r)

st.caption("Note: This is a heuristic model using publicly-available fundamentals. Not financial advice.")

# =========================================
# Charts
# =========================================
historical_data = stock.history(period="5y")
st.subheader("📊 Historical Stock Price")
if not historical_data.empty:
    st.line_chart(historical_data['Close'], use_container_width=True)
else:
    st.warning("Historical price data is not available.")

try:
    st.subheader("📉 Total Revenue Over Time")
    st.line_chart(stock.financials.loc['Total Revenue'], use_container_width=True)
except KeyError:
    st.warning("Revenue data is not available.")

