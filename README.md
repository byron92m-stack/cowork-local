# Bitcoin Dashboard

Streamlit-based Bitcoin dashboard with ClickHouse backend, dark theme, and interactive Plotly charts.

## Features

- **Dark Theme** — Full dark mode UI optimized for crypto monitoring
- **ClickHouse Integration** — Query Bitcoin price data from ClickHouse at `localhost:8123`
- **Live Metrics** — Current price, 24h change, volume, range, and market cap in cards
- **Interactive Charts** — Price line chart, candlestick chart, and price distribution histogram
- **Raw Data Explorer** — View and download query results as CSV
- **CLI Interface** — Full argparse CLI with check, schema, and query commands
- **Auto Demo Data** — Creates and seeds a demo table if none exists

## Installation

```bash
# Install from source
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Usage

### Launch Dashboard

```bash
bitcoin-dashboard
```

Opens the Streamlit app at `http://localhost:8501`.

### CLI Commands

```bash
# Check ClickHouse connection
bitcoin-dashboard --check

# Check with JSON output
bitcoin-dashboard --check --json

# View table schema
bitcoin-dashboard --schema

# Run raw SQL query
bitcoin-dashboard --query "SELECT count() FROM bitcoin_prices"

# Run query with JSON output
bitcoin-dashboard --query "SELECT * FROM bitcoin_prices LIMIT 5" --json

# Print version
bitcoin-dashboard --version
```

### Custom Connection

```bash
bitcoin-dashboard \
    --host 192.168.1.100 \
    --port 8123 \
    --user default \
    --database crypto \
    --table btc_ohlc \
    --limit 500 \
    --interval 1h \
    --timeout 60
```

## Table Schema

The dashboard expects a table with the following schema:

```sql
CREATE TABLE bitcoin_prices (
    timestamp DateTime,
    price Float64,
    volume Float64,
    market_cap Float64,
    open Float64,
    high Float64,
    low Float64,
    close Float64
) ENGINE = MergeTree()
ORDER BY timestamp
```

If the table does not exist, the dashboard will create it and insert demo data automatically.

## Project Structure

```
├── src/
│   └── bitcoin_dashboard/
│       ├── __init__.py      # Package version
│       ├── core.py          # Business logic, ClickHouse client, charts, Streamlit UI
│       └── cli.py           # Argparse CLI entry point
├── tests/
│   ├── test_core.py         # 20+ unit tests for core module
│   └── test_cli.py          # 10+ unit tests for CLI module
├── pyproject.toml           # Project config and dependencies
└── README.md
```

## Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=src.bitcoin_dashboard
```

## Dependencies

- streamlit >= 1.28
- plotly >= 5.18
- pandas >= 2.0
- requests >= 2.31

## License

MIT
