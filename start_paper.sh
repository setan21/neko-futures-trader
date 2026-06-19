#!/bin/bash
# Neko Paper Trading Scanner - Startup Script

cd /root/neko-futures-trader

# Set environment
export PAPER_TRADING=true
export BINANCE_API_KEY=paper_mode
export BINANCE_SECRET=paper_mode

# Create log directory
mkdir -p logs

echo "🐱 Starting Neko Futures Scanner (Paper Trading Mode)"
echo "💰 No real funds at risk!"
echo "📊 Log: logs/scanner.log"
echo ""

# Run scanner
python3 scanner.py 2>&1 | tee -a logs/scanner.log
