import streamlit as st
import duckdb
import pandas as pd

# Set up page configurations
st.set_page_config(page_title="Financial Strategy Backtester", layout="wide")

st.title("📈 Data Analytics Pipeline: Financial Strategy Backtester")
st.markdown("Analyzing historical performance and risk profiles using a Modern Data Stack workflow.")

# Establish connection to the local DuckDB warehouse
db_conn = duckdb.connect("financial_analytics.db")

# Fetch overall performance data
df_perf = db_conn.execute("SELECT * FROM fct_portfolio_performance ORDER BY Date").df()
df_signals = db_conn.execute("SELECT * FROM fct_strategy_signals ORDER BY Date").df()

db_conn.close()

# --- FINANCIAL LOGIC CALCULATION LAYER ---
# Crucial Fix: Fill any NaN values (like the very last row) with 0 before calculating cumulative product
df_perf['daily_strategy_return'] = df_perf['daily_strategy_return'].fillna(0)

total_days = len(df_perf)
# Calculate cumulative compound return of the strategy
df_perf['cum_strategy_return'] = (1 + df_perf['daily_strategy_return']).cumprod() - 1
final_roi = df_perf['cum_strategy_return'].iloc[-1] * 100 if total_days > 0 else 0

# Calculate Win Rate (Percentage of trading periods that yielded positive return while holding)
trades_held = df_perf[df_perf['signal'] == 1]
total_trades = len(trades_held)
winning_trades = len(trades_held[trades_held['daily_strategy_return'] > 0])
win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

# --- DASHBOARD VISUALIZATION LAYER ---
st.subheader("📊 Portfolio Executive Metrics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Total Strategy ROI", value=f"{final_roi:.2f}%", delta="Moving Average Strategy")
with col2:
    st.metric(label="Strategy Win Rate", value=f"{win_rate:.1f}%")
with col3:
    st.metric(label="Total Analyzed Periods", value=f"{total_days} Days")

st.markdown("---")

st.subheader("📉 Strategy Performance Over Time")
# Plot Close price against Moving Averages
st.markdown("**Price vs Moving Averages (Signals Generation Base)**")
st.line_chart(df_signals.set_index('Date')[['Close', 'sma_20', 'sma_50']])

st.markdown("**Cumulative Strategy Growth (Returns Matrix)**")
st.area_chart(df_perf.set_index('Date')['cum_strategy_return'])