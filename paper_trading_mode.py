#!/usr/bin/env python3
"""
Paper Trading Mode for Neko Futures Trader
Intercepts order execution and simulates trades
"""

import sys
import os
import json
import time
from datetime import datetime

# Add project to path
sys.path.insert(0, "/root/neko-futures-trader")

# Set environment for paper mode
os.environ["PAPER_TRADING"] = "true"

# Import paper trader
from paper_trader import (
    open_position, close_position, get_dashboard, 
    get_stats, load_positions, save_positions,
    load_balance, save_balance, log_trade
)

# Paper trading state
PAPER_POSITIONS_FILE = "/root/neko-futures-trader/data/paper/open_orders.json"

def load_paper_orders():
    """Load paper trading orders (maps symbol to paper order_id)"""
    if os.path.exists(PAPER_POSITIONS_FILE):
        with open(PAPER_POSITIONS_FILE) as f:
            return json.load(f)
    return {}

def save_paper_orders(orders):
    """Save paper trading orders"""
    os.makedirs(os.path.dirname(PAPER_POSITIONS_FILE), exist_ok=True)
    with open(PAPER_POSITIONS_FILE, "w") as f:
        json.dump(orders, f, indent=2)

def paper_place_order(symbol, side, quantity):
    """
    Simulate place_order() from scanner.py
    Returns mock response similar to Binance API
    """
    import requests
    
    # Get current price from Binance (real price, no real trade)
    try:
        resp = requests.get(f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}", timeout=5)
        price = float(resp.json()["price"])
    except Exception as e:
        return {"error": f"Price fetch failed: {e}"}
    
    # Open paper position
    result = open_position(symbol, side, price, quantity, reason="scanner_signal")
    
    if "error" in result:
        return {"error": result["error"]}
    
    # Track order mapping
    orders = load_paper_orders()
    orders[symbol] = result["order_id"]
    save_paper_orders(orders)
    
    print(f"📝 PAPER ORDER: {side} {symbol}")
    print(f"   Price: ${price:.4f} | Qty: {quantity}")
    print(f"   Order ID: {result['order_id']}")
    
    # Return mock Binance response
    return {
        "orderId": result["order_id"],
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "price": price,
        "executedQty": quantity,
        "status": "FILLED"
    }

def paper_place_algo_order(symbol, algo_type, side, quantity, trigger_price, close_position_flag=True):
    """
    Simulate place_algo_order() for SL/TP
    Returns mock response similar to Binance API
    """
    orders = load_paper_orders()
    order_id = orders.get(symbol)
    
    if not order_id:
        return {"error": f"No open paper position for {symbol}"}
    
    # Update SL/TP in paper position
    from paper_trader import load_positions, save_positions
    positions = load_positions()
    
    if order_id not in positions:
        return {"error": f"Position {order_id} not found"}
    
    if algo_type == "STOP_MARKET":
        positions[order_id]["stop_loss"] = float(trigger_price)
        print(f"📝 PAPER SL: {symbol} @ ${trigger_price:.4f}")
    elif algo_type == "TAKE_PROFIT_MARKET":
        positions[order_id]["take_profit"] = float(trigger_price)
        print(f"📝 PAPER TP: {symbol} @ ${trigger_price:.4f}")
    
    save_positions(positions)
    
    return {
        "algoOrderId": f"PAPER_ALGO_{int(time.time())}",
        "symbol": symbol,
        "algoType": algo_type,
        "side": side,
        "triggerPrice": trigger_price,
        "status": "ACTIVE"
    }

def paper_get_open_algo_orders(symbol=None):
    """
    Simulate get_open_algo_orders()
    Returns paper SL/TP orders
    """
    positions = load_positions()
    orders = []
    
    for order_id, pos in positions.items():
        if pos["status"] != "OPEN":
            continue
        if symbol and pos["symbol"] != symbol:
            continue
        
        # Add SL order
        if pos.get("stop_loss"):
            orders.append({
                "algoOrderId": f"{order_id}_SL",
                "symbol": pos["symbol"],
                "algoType": "STOP_MARKET",
                "side": "SELL" if pos["side"] == "LONG" else "BUY",
                "triggerPrice": pos["stop_loss"],
                "status": "ACTIVE"
            })
        
        # Add TP order
        if pos.get("take_profit"):
            orders.append({
                "algoOrderId": f"{order_id}_TP",
                "symbol": pos["symbol"],
                "algoType": "TAKE_PROFIT_MARKET",
                "side": "SELL" if pos["side"] == "LONG" else "BUY",
                "triggerPrice": pos["take_profit"],
                "status": "ACTIVE"
            })
    
    return orders

def paper_get_position_risk(symbol=None):
    """
    Simulate get_position_risk()
    Returns current paper positions with PnL
    """
    import requests
    
    positions = load_positions()
    result = []
    
    for order_id, pos in positions.items():
        if pos["status"] != "OPEN":
            continue
        if symbol and pos["symbol"] != symbol:
            continue
        
        # Get current price
        try:
            resp = requests.get(f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={pos['symbol']}", timeout=5)
            current_price = float(resp.json()["price"])
        except:
            current_price = pos["entry_price"]
        
        # Calculate PnL
        if pos["side"] == "LONG":
            pnl = (current_price - pos["entry_price"]) * pos["quantity"]
            pnl_pct = ((current_price - pos["entry_price"]) / pos["entry_price"]) * 100
        else:
            pnl = (pos["entry_price"] - current_price) * pos["quantity"]
            pnl_pct = ((pos["entry_price"] - current_price) / pos["entry_price"]) * 100
        
        result.append({
            "symbol": pos["symbol"],
            "positionAmt": pos["quantity"] if pos["side"] == "LONG" else -pos["quantity"],
            "entryPrice": pos["entry_price"],
            "markPrice": current_price,
            "unRealizedProfit": pnl,
            "leverage": pos["leverage"],
            "marginType": "cross",
            "isolatedWallet": pos["margin"],
            "positionSide": pos["side"]
        })
    
    return result

def paper_get_account():
    """
    Simulate get_account()
    Returns paper account info
    """
    balance = load_balance()
    positions = load_positions()
    
    # Calculate total margin from open positions
    used_margin = sum(p["margin"] for p in positions.values() if p["status"] == "OPEN")
    
    return {
        "totalWalletBalance": balance["total"],
        "availableBalance": balance["available"],
        "totalMarginBalance": balance["total"],
        "totalUnrealizedProfit": balance.get("unrealized_pnl", 0),
        "totalInitialMargin": used_margin,
        "totalMaintMargin": used_margin * 0.5,
        "totalCrossWalletBalance": balance["total"],
        "assets": [{
            "asset": "USDT",
            "walletBalance": balance["total"],
            "unrealizedProfit": balance.get("unrealized_pnl", 0),
            "marginBalance": balance["total"],
            "availableBalance": balance["available"],
            "crossWalletBalance": balance["total"]
        }]
    }

def paper_get_balance():
    """
    Simulate get_balance() - returns totalMarginBalance
    """
    balance = load_balance()
    positions = load_positions()
    
    # Calculate unrealized PnL from open positions
    unrealized = 0
    for pos in positions.values():
        if pos["status"] != "OPEN":
            continue
        try:
            import requests
            resp = requests.get(f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={pos['symbol']}", timeout=5)
            current_price = float(resp.json()["price"])
            
            if pos["side"] == "LONG":
                pnl = (current_price - pos["entry_price"]) * pos["quantity"]
            else:
                pnl = (pos["entry_price"] - current_price) * pos["quantity"]
            unrealized += pnl
        except:
            pass
    
    return balance["total"] + unrealized

def paper_get_positions():
    """
    Simulate get_positions() - returns list of open positions
    """
    import requests
    
    positions = load_positions()
    result = []
    
    for order_id, pos in positions.items():
        if pos["status"] != "OPEN":
            continue
        
        # Get current price
        try:
            resp = requests.get(f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={pos['symbol']}", timeout=5)
            current_price = float(resp.json()["price"])
        except:
            current_price = pos["entry_price"]
        
        # Calculate PnL
        if pos["side"] == "LONG":
            pnl = (current_price - pos["entry_price"]) * pos["quantity"]
            amt = pos["quantity"]
        else:
            pnl = (pos["entry_price"] - current_price) * pos["quantity"]
            amt = -pos["quantity"]
        
        result.append({
            "symbol": pos["symbol"],
            "positionAmt": str(amt),
            "entryPrice": str(pos["entry_price"]),
            "markPrice": str(current_price),
            "unRealizedProfit": str(pnl),
            "leverage": str(pos["leverage"]),
            "marginType": "cross",
            "isolatedWallet": str(pos["margin"]),
            "positionSide": pos["side"]
        })
    
    return result

def create_paper_wrapper():
    """
    Create a wrapper module that can be imported instead of the real Binance client
    """
    wrapper_code = '''"""
Paper Trading Binance Client Wrapper
Import this instead of making real API calls
"""
import sys
sys.path.insert(0, "/root/neko-futures-trader")

from paper_trading_mode import (
    paper_place_order as place_order,
    paper_place_algo_order as place_algo_order,
    paper_get_open_algo_orders as get_open_algo_orders,
    paper_get_position_risk as get_position_risk,
    paper_get_account as get_account
)

# Mock API_KEY check
API_KEY = "PAPER_MODE"
'''
    
    wrapper_path = "/root/neko-futures-trader/paper_client.py"
    with open(wrapper_path, "w") as f:
        f.write(wrapper_code)
    
    print(f"✓ Paper client wrapper created: {wrapper_path}")
    return wrapper_path

def patch_scanner():
    """
    Patch scanner.py to use paper trading functions
    """
    scanner_path = "/root/neko-futures-trader/scanner.py"
    
    with open(scanner_path) as f:
        content = f.read()
    
    # Check if already patched
    if "PAPER_TRADING" in content and "paper_" in content:
        print("Scanner already patched for paper trading")
        return
    
    # Add paper trading imports at the top (after existing imports)
    paper_imports = '''
# === PAPER TRADING MODE ===
import os
PAPER_TRADING = os.environ.get("PAPER_TRADING", "false").lower() == "true"

if PAPER_TRADING:
    from paper_trading_mode import (
        paper_place_order,
        paper_place_algo_order,
        paper_get_open_algo_orders,
        paper_get_position_risk,
        paper_get_account
    )
    print("📝 PAPER TRADING MODE ENABLED - No real funds at risk!")
# === END PAPER TRADING MODE ===

'''
    
    # Find first import and add paper imports after
    import_pos = content.find("import ")
    if import_pos > 0:
        content = content[:import_pos] + paper_imports + content[import_pos:]
    
    # Patch place_order function
    old_place_order = '''def place_order(symbol, side, quantity):
    ts = int(time.time() * 1000)'''
    
    new_place_order = '''def place_order(symbol, side, quantity):
    if PAPER_TRADING:
        return paper_place_order(symbol, side, quantity)
    ts = int(time.time() * 1000)'''
    
    content = content.replace(old_place_order, new_place_order)
    
    # Save patched scanner
    backup_path = scanner_path + ".backup"
    with open(backup_path, "w") as f:
        f.write(content)
    
    with open(scanner_path, "w") as f:
        f.write(content)
    
    print(f"✓ Scanner patched for paper trading")
    print(f"  Backup saved to: {backup_path}")

def setup_paper_trading():
    """Complete setup for paper trading mode"""
    print("=" * 60)
    print("🐱 NEKO FUTURES - PAPER TRADING SETUP")
    print("=" * 60)
    
    # Create data directory
    os.makedirs("/root/neko-futures-trader/data/paper", exist_ok=True)
    
    # Create paper client wrapper
    create_paper_wrapper()
    
    # Patch scanner
    patch_scanner()
    
    print("\n✅ Paper trading setup complete!")
    print("\nTo run in paper mode:")
    print("  cd /root/neko-futures-trader")
    print("  PAPER_TRADING=true python3 scanner.py")
    print("\nTo view paper trading dashboard:")
    print("  python3 paper_trader.py dashboard")
    print("  python3 paper_trader.py stats")
    print("  python3 paper_trader.py positions")

if __name__ == "__main__":
    setup_paper_trading()
