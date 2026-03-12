#!/bin/bash
set -e

echo "TCM-Exosome Platform Starting..."

# Only init DB if it doesn't exist yet
if [ ! -f /app/data/tcm_exosome.db ]; then
    echo "Initializing fresh database..."
    python src/database/init_db.py
else
    echo "Database already exists, skipping init."
fi

echo "Starting crawler daemon..."
python run_crawlers.py --daemon --interval 6 > /app/logs/crawler.log 2>&1 &

echo "Running initial crawl..."
python run_crawlers.py --once > /app/logs/first_crawl.log 2>&1 &

echo "Starting Dashboard on :8501..."
exec streamlit run src/dashboard/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
