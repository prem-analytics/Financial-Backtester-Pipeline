import datetime
import yfinance as yf
import duckdb

def ingest_stock_data(ticker: str, days_back: int = 730):
    print(f"🚀 Starting ingestion for ticker: {ticker}...")
    
    # Calculate timestamps for the historical window
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days_back)
    
    try:
        # Fetch historical data using yfinance wrapper
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"⚠️ No data found for {ticker}.")
            return None
            
        # Reset index so 'Date' becomes a clean column instead of the dataframe index
        df = df.reset_index()
        df['Ticker'] = ticker
        
        print(f"📥 Successfully downloaded {len(df)} rows for {ticker}.")
        return df
    except Exception as e:
        print(f"❌ Failed to fetch data for {ticker}: {e}")
        return None

if __name__ == "__main__":
    target_ticker = "AAPL"
    raw_data = ingest_stock_data(target_ticker, days_back=730) # 2 years of data
    
    if raw_data is not None:
        # Connect to a persistent local DuckDB database file
        db_conn = duckdb.connect("financial_analytics.db")
        
        # Create or overwrite our raw staging table
        db_conn.execute("CREATE OR REPLACE TABLE stg_raw_prices AS SELECT * FROM raw_data")
        
        # Verify columns and rows landed correctly
        check_df = db_conn.execute("SELECT Ticker, Date, Close, Volume FROM stg_raw_prices LIMIT 5").df()
        print("\n📊 Verification: First 5 rows stored in DuckDB:")
        print(check_df)
        
        db_conn.close()