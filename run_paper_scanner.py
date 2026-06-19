#!/usr/bin/env python3
"""
Neko Paper Trading Scanner - Background Runner
Continuously scans and places paper trades
"""
import os
import sys
import time
import signal

# Set environment
os.environ["PAPER_TRADING"] = "true"
os.environ["BINANCE_API_KEY"] = "paper_mode"
os.environ["BINANCE_SECRET"] = "paper_mode"

sys.path.insert(0, "/root/neko-futures-trader")

# Handle graceful shutdown
shutdown = False
def signal_handler(signum, frame):
    global shutdown
    print(f"\nReceived signal {signum}, shutting down...")
    shutdown = True

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Import after env is set
import scanner
from scanner import main, PAPER_TRADING
from paper_trader import get_dashboard
from position_monitor import monitor_positions

print("=" * 60)
print("🐱 NEKO PAPER TRADING SCANNER")
print("=" * 60)
print(f"Mode: PAPER_TRADING = {PAPER_TRADING}")
print(f"Initial balance: $10,000 USDT")

dashboard = get_dashboard()
print(f"Current balance: ${dashboard['balance']['total']:.2f}")
print("=" * 60)

iteration = 0
while not shutdown:
    iteration += 1
    print(f"\n--- Iteration {iteration} ---")
    try:
        # MONITOR open positions FIRST (SL/TP/timeout). This was missing before,
        # which let positions run for days with no exit (zombie positions).
        try:
            closed = monitor_positions()
            for c in closed:
                print(f"  CLOSED {c['symbol']} {c['reason']} pnl={c['pnl']:.2f} ({c['pnl_pct']:.1f}%)")
        except Exception as me:
            print(f"  monitor error: {me}")
        main()
        print(f"✓ Scan {iteration} complete")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Show dashboard after each scan
    dashboard = get_dashboard()
    print(f"Balance: ${dashboard['balance']['total']:.2f} | Positions: {dashboard['position_count']}")
    
    # Sleep between scans (unless shutdown requested)
    if not shutdown:
        print("Sleeping 60s...")
        for _ in range(60):
            if shutdown:
                break
            time.sleep(1)

print("\n" + "=" * 60)
print("Scanner stopped. Final state:")
dashboard = get_dashboard()
print(f"Balance: ${dashboard['balance']['total']:.2f}")
print(f"Positions: {dashboard['position_count']}")
print("=" * 60)
