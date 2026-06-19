#!/usr/bin/env python3
"""
Paper Trading Scanner - Wraps the main scanner to use paper trading
Run this instead of scanner.py for paper trading mode.
"""

import sys
import os

# Add project to path
sys.path.insert(0, "/root/neko-futures-trader")

# Set paper trading mode
os.environ["PAPER_TRADING"] = "true"
os.environ["BINANCE_API_KEY"] = "paper_mode"
os.environ["BINANCE_SECRET"] = "paper_mode"

# Import paper trader module
from paper_trader import open_position, get_dashboard, get_stats

# Monkey-patch the order execution to use paper trading
import scanner as real_scanner

# Store original functions
_original_execute_order = None
_original_close_position = None

def paper_execute_order(symbol, side, quantity, leverage, reason=""):
    """Execute order in paper mode"""
    import requests
    
    # Get current price
    try:
        resp = requests.get(f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}", timeout=5)
        price = float(resp.json()["price"])
    except Exception as e:
        return {"error": f"Failed to get price: {e}"}
    
    result = open_position(symbol, side, price, quantity, leverage, reason)
    print(f"📝 PAPER TRADE: {side} {symbol} @ {price} | Qty: {quantity} | Reason: {reason}")
    return result

def paper_close_position(symbol, order_id, reason=""):
    """Close position in paper mode"""
    import requests
    from paper_trader import close_position as real_close
    
    # Get current price
    try:
        resp = requests.get(f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}", timeout=5)
        price = float(resp.json()["price"])
    except Exception as e:
        return {"error": f"Failed to get price: {e}"}
    
    result = real_close(order_id, price, reason)
    print(f"📝 PAPER CLOSE: {symbol} @ {price} | PnL: {result.get('pnl', 0):.2f} USDT | Reason: {reason}")
    return result

def run_paper_scanner():
    """Run the scanner in paper trading mode"""
    print("=" * 60)
    print("🐱 NEKO FUTURES TRADER - PAPER TRADING MODE")
    print("=" * 60)
    print("💰 No real funds at risk!")
    print("📊 Using real market data for signals")
    print("=" * 60)
    
    # Show current dashboard
    dashboard = get_dashboard()
    print(f"\n💵 Starting Balance: {dashboard['balance']['total']:.2f} USDT")
    print(f"📈 Total Trades: {dashboard['stats'].get('total_trades', 0)}")
    print(f"🎯 Win Rate: {dashboard['stats'].get('win_rate', 0):.1f}%")
    print(f"💰 Total PnL: {dashboard['stats'].get('total_pnl', 0):.2f} USDT")
    print()
    
    # Run the actual scanner
    # The scanner will call execute_order which we've monkey-patched
    try:
        # Import and run main scanner logic
        from scanner import main as scanner_main
        
        # Override functions in scanner module
        if hasattr(real_scanner, 'execute_order'):
            real_scanner.execute_order = paper_execute_order
        if hasattr(real_scanner, 'close_position'):
            real_scanner.close_position = paper_close_position
        
        print("🚀 Starting scanner...")
        scanner_main()
    except KeyboardInterrupt:
        print("\n⏹️ Scanner stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_paper_scanner()
