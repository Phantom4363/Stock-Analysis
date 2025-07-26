import yfinance as yf
import streamlit as st
import matplotlib.pyplot as plt

# --- Format individual metrics ---
def format_value(value, low, high, is_percentage=False, multiplier=1):
    if value == "N/A" or value is None:
        return f"<span style='color:gray;'>N/A</span>"
    value *= multiplier
    if low <= value <= high:
        return f"<span style='color:green;'>{value:.2f}%</span>" if is_percentage else f"<span style='color:green;'>{value:.2f}</span>"
    else:
        return f"<span style='color:red;'>{value:.2f}%</span>" if is_percentage else f"<span style='color:red;'>{value:.2f}</span>"

# --- Sector comparison formatter ---
def compare_to_sector(company_value, sector_value, higher_is_better=True):
    if company_value == "N/A" or company_value is None or sector_value is None:
        return f"<span style='color:gray;'>N/A</span>"
    if higher_is_better:
        color = "green" if company_value > sector_value else "red"
    else:
        color = "green" if company_value < sector_value else "red"
    return f"<span style='color:{color};'>{company_value:.2f}</span> (vs. {sector_value:.2f})"

# --- Streamlit App ---
st.title("📊 Fundamental Stock Analysis Dashboard")

ticker_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT)", "AAPL")
stock = yf.Ticker(ticker_symbol)
st.header(f"Financial Data for {ticker_symbol}")

current_price = stock.info.get('currentPrice', None)
sector = stock.info.get('sector', 'Unknown')

if current_price is not None:
    st.write(f"**Current Stock Price:** ${current_price:.2f}")
else:
    st.write("**Current Stock Price:** N/A")

# --- Pull metrics ---
pe_ratio = stock.info.get('trailingPE', 'N/A')
pb_ratio = stock.info.get('priceToBook', 'N/A')
roe = stock.info.get('returnOnEquity', 'N/A')
debt_to_equity = stock.info.get('debtToEquity', 'N/A')
market_cap = stock.info.get('marketCap', 'N/A')
profit_margin = stock.info.get('profitMargins', 'N/A')
dividend_yield = stock.info.get('dividendYield', 'N/A')
operating_margin = stock.info.get('operatingMargins', 'N/A')
beta = stock.info.get('beta', 'N/A')
current_ratio = stock.info.get('currentRatio', 'N/A')

# --- Format numbers ---
if roe and isinstance(roe, (int, float)):
    roe *= 100
if profit_margin and isinstance(profit_margin, (int, float)):
    profit_margin *= 100
if dividend_yield and isinstance(dividend_yield, (int, float)):
    dividend_yield *= 100
if operating_margin and isinstance(operating_margin, (int, float)):
    operating_margin *= 100
if debt_to_equity and isinstance(debt_to_equity, (int, float)):
    debt_to_equity /= 100

# --- Hardcoded sector benchmarks ---
sector_benchmarks = {
    "Technology":      {"PE": 25, "PB": 6, "ROE": 18, "ProfitMargin": 15},
    "Healthcare":      {"PE": 20, "PB": 4, "ROE": 14, "ProfitMargin": 12},
    "Financial Services": {"PE": 14, "PB": 1.5, "ROE": 10, "ProfitMargin": 20},
    "Consumer Defensive": {"PE": 22, "PB": 3.5, "ROE": 15, "ProfitMargin": 10},
    "Industrials":     {"PE": 18, "PB": 2.5, "ROE": 12, "ProfitMargin": 8},
    "Energy":          {"PE": 12, "PB": 1.8, "ROE": 16, "ProfitMargin": 10},
    "Unknown":         {"PE": 20, "PB": 3, "ROE": 12, "ProfitMargin": 10}
}
benchmarks = sector_benchmarks.get(sector, sector_benchmarks["Unknown"])

# --- Display key metrics ---
st.subheader("📈 Key Financial Metrics")
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

# --- Revenue Growth (YoY) ---
try:
    revenue_data = stock.financials.loc['Total Revenue']
    if len(revenue_data) >= 2:
        recent = revenue_data.iloc[0]
        previous = revenue_data.iloc[1]
        growth = ((recent - previous) / previous) * 100
        st.write("Revenue Growth (YoY): ", format_value(growth, 10, 100, is_percentage=True), unsafe_allow_html=True)
    else:
        st.write("Revenue Growth (YoY): <span style='color:gray;'>N/A</span>", unsafe_allow_html=True)
except Exception:
    st.write("Revenue Growth (YoY): <span style='color:gray;'>N/A</span>", unsafe_allow_html=True)

# --- Sector Benchmark Comparison ---
st.subheader(f"📉 Sector Comparison ({sector})")
st.markdown("**P/E Ratio:** " +
            compare_to_sector(pe_ratio, benchmarks["PE"], higher_is_better=False),
            unsafe_allow_html=True)
st.markdown("**P/B Ratio:** " +
            compare_to_sector(pb_ratio, benchmarks["PB"], higher_is_better=False),
            unsafe_allow_html=True)
st.markdown("**Return on Equity (ROE):** " +
            compare_to_sector(roe, benchmarks["ROE"], higher_is_better=True),
            unsafe_allow_html=True)
st.markdown("**Profit Margin:** " +
            compare_to_sector(profit_margin, benchmarks["ProfitMargin"], higher_is_better=True),
            unsafe_allow_html=True)

# --- Historical stock price chart ---
historical_data = stock.history(period="5y")
st.subheader("📊 Historical Stock Price")
if not historical_data.empty:
    st.line_chart(historical_data['Close'], use_container_width=True)
else:
    st.warning("Historical price data is not available.")

# --- Revenue trend chart ---
try:
    st.subheader("📉 Total Revenue Over Time")
    st.line_chart(stock.financials.loc['Total Revenue'], use_container_width=True)
except KeyError:
    st.warning("Revenue data is not available.")
