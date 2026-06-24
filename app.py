import streamlit as st
import duckdb
import pandas as pd
import os

# Import our custom scripts to run them dynamically if needed
import ingest
import transform

# Set up page configurations
st.set_page_config(page_title="Financial Strategy Backtester", layout="wide")

st.title("📈 Data Analytics Pipeline: Financial Strategy Backtester")
st.markdown("Analyzing historical performance and risk profiles using a Modern Data Stack workflow.")

db_filename = "financial_analytics.db"

# --- PRODUCTION DATA QUALITY CHECK ---
# If the DB doesn't exist or is empty, build it on the fly!
db_conn = duckdb.connect(db_filename)
tables = [row[0] for row in db_conn.execute("SHOW TABLES").fetchall()]

if "fct_portfolio_performance" not in tables or "fct_strategy_signals" not in tables:
    with st.spinner("⏳ First-time setup: Initializing pipeline, downloading data, and building SQL models..."):
        # 1. Run Ingestion Layer
        raw_data = ingest.ingest_stock_data("AAPL", days_back=730)
        if raw_data is not None:
            db_conn.execute("CREATE OR REPLACE TABLE stg_raw_prices AS SELECT * FROM raw_data")
        
        # 2. Run Transformation Layer
        db_conn.execute("""
            CREATE OR REPLACE TABLE fct_strategy_signals AS 
            WITH moving_averages AS (
                SELECT 
                    Ticker,
                    Date,
                    Close,
                    AVG(Close) OVER(PARTITION BY Ticker ORDER BY Date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as sma_20,
                    AVG(Close) OVER(PARTITION BY Ticker ORDER BY Date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) as sma_50,
                    ROW_NUMBER() OVER(PARTITION BY Ticker ORDER BY Date) as row_num
                FROM stg_raw_prices
            )
            SELECT 
                Ticker,
                Date,
                Close,
                sma_20,
                sma_50,
                CASE 
                    WHEN sma_20 > sma_50 AND row_num > 50 THEN 1 
                    ELSE 0 
                END as signal
            FROM moving_averages
        """)
        
        db_conn.execute("""
            CREATE OR REPLACE TABLE fct_portfolio_performance AS 
            WITH price_leads AS (
                SELECT 
                    Ticker,
                    Date,
                    Close,
                    signal,
                    LEAD(Close) OVER(PARTITION BY Ticker ORDER BY Date) as next_day_close
                FROM fct_strategy_signals
            ),
            daily_returns AS (
                SELECT 
                    Ticker,
                    Date,
                    Close,
                    signal,
                    CASE 
                        WHEN signal = 1 AND Close > 0 THEN (next_day_close - Close) / Close
                        ELSE 0 
                    END as daily_strategy_return
                FROM price_leads
            )
            SELECT * FROM daily_returns
        """)
    st.success("✅ Pipeline successfully built on cloud storage!")

# Fetch final data metrics
df_perf = db_conn.execute("SELECT * FROM fct_portfolio_performance ORDER BY Date").df()
df_signals = db_conn.execute("SELECT * FROM fct_strategy_signals ORDER BY Date").df()
db_conn.close()

# --- FINANCIAL LOGIC CALCULATION LAYER ---
df_perf['daily_strategy_return'] = df_perf['daily_strategy_return'].fillna(0)
total_days = len(df_perf)
df_perf['cum_strategy_return'] = (1 + df_perf['daily_strategy_return']).cumprod() - 1
final_roi = df_perf['cum_strategy_return'].iloc[-1] * 100 if total_days > 0 else 0

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
st.markdown("**Price vs Moving Averages (Signals Generation Base)**")
st.line_chart(df_signals.set_index('Date')[['Close', 'sma_20', 'sma_50']])

st.markdown("**Cumulative Strategy Growth (Returns Matrix)**")
st.area_chart(df_perf.set_index('Date')['cum_strategy_return'])