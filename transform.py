import duckdb

def run_analytical_transformations():
    print("🧠 Starting analytical data modeling transformations...")
    
    # Connect to our existing DuckDB data warehouse
    db_conn = duckdb.connect("financial_analytics.db")
    
    # 1. Create a modeled table calculating the moving averages using SQL Window functions
    print("📈 Calculating 20-day and 50-day Moving Averages...")
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
            -- Generate a trade signal flag (1 = Buy/Hold, 0 = Sell/Cash)
            CASE 
                WHEN sma_20 > sma_50 AND row_num > 50 THEN 1 
                ELSE 0 
            END as signal
        FROM moving_averages
    """)
    
    # 2. Calculate daily returns and track portfolio performance over time
    print("📊 Generating portfolio performance matrix...")
    db_conn.execute("""
        CREATE OR REPLACE TABLE fct_portfolio_performance AS 
        WITH price_leads AS (
            SELECT 
                Ticker,
                Date,
                Close,
                signal,
                -- Get the close price of the next trading day to compute real return
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
                    -- If we are holding the asset (signal = 1), our return is based on price change
                    WHEN signal = 1 AND Close > 0 THEN (next_day_close - Close) / Close
                    ELSE 0 
                END as daily_strategy_return
            FROM price_leads
        )
        SELECT * FROM daily_returns
    """)
    
    # Verify the transformation tables generated successfully
    check_df = db_conn.execute("""
        SELECT Date, Close, round(sma_20, 2) as SMA20, round(sma_50, 2) as SMA50, signal 
        FROM fct_strategy_signals 
        WHERE sma_50 IS NOT NULL 
        LIMIT 10
    """).df()
    
    print("\n✅ Analytical Transformations Complete! Previewing signals:")
    print(check_df)
    
    db_conn.close()

if __name__ == "__main__":
    run_analytical_transformations()