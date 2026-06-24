# 📈 Financial Strategy Backtester Pipeline

An end-to-end data analytics pipeline that automates historical stock ingestion, runs advanced algorithmic moving average crossover modeling within an embedded data warehouse, and serves real-time portfolio performance tracking metrics.

🔗 **[Click Here to View the Live Interactive Dashboard](https://financial-backtester-pipeline-dcfhssvdq92jaubf2svg5a.streamlit.app/)**

---

## 📊 Live Dashboard Preview
<video src="dashboard_preview.mp4" width="100%" autoplay loop muted controls></video>

---

## 🛠️ Tech Stack & Architecture
* **Ingestion Layer:** Python (`yfinance` API wrapper)
* **Data Warehouse Storage:** DuckDB (Columnar analytical storage)
* **Transformation Modeling:** Embedded SQL Window Functions (`AVG() OVER()`, `LEAD()`)
* **Visualization Layer:** Streamlit Cloud Network Interface