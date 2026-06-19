"""
Paper Trading Module for Neko Futures Trader
Simulates trades with real prices, no real funds at risk.
"""

import json
import time
import os
from datetime import datetime
from decimal import Decimal

PAPER_DATA_DIR = "/root/neko-futures-trader/data/paper"
POSITIONS_FILE = f"{PAPER_DATA_DIR}/positions.json"
TRADE_LOG_FILE = f"{PAPER_DATA_DIR}/trades.jsonl"
BALANCE_FILE = f"{PAPER_DATA_DIR}/balance.json"
STATS_FILE = f"{PAPER_DATA_DIR}/stats.json"

# Paper trading config
INITIAL_BALANCE = 10000.0  # USDT
LEVERAGE = 10

def ensure_dirs():
    os.makedirs(PAPER_DATA_DIR, exist_ok=True)

def load_balance():
    ensure_dirs()
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE) as f:
            return json.load(f)
    return {
        "available": INITIAL_BALANCE,
        "total": INITIAL_BALANCE,
        "used_margin": 0.0,
        "unrealized_pnl": 0.0,
        "created_at": datetime.utcnow().isoformat()
    }

def save_balance(balance):
    ensure_dirs()
    with open(BALANCE_FILE, "w") as f:
        json.dump(balance, f, indent=2)

def load_positions():
    ensure_dirs()
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE) as f:
            return json.load(f)
    return {}

def save_positions(positions):
    ensure_dirs()
    with open(POSITIONS_FILE, "w") as f:
        json.dump(positions, f, indent=2)

def log_trade(trade):
    ensure_dirs()
    trade["timestamp"] = datetime.utcnow().isoformat()
    with open(TRADE_LOG_FILE, "a") as f:
        f.write(json.dumps(trade) + "\n")

def generate_order_id():
    return f"PAPER_{int(time.time())}_{os.getpid()}"

def open_position(symbol, side, entry_price, quantity, leverage=LEVERAGE, reason=""):
    """Open a paper position"""
    positions = load_positions()
    balance = load_balance()
    
    order_id = generate_order_id()
    margin = (entry_price * quantity) / leverage
    
    if margin > balance["available"]:
        return {"error": f"Insufficient balance. Need {margin:.2f} USDT, have {balance['available']:.2f} USDT"}
    
    position = {
        "order_id": order_id,
        "symbol": symbol,
        "side": side,  # LONG or SHORT
        "entry_price": float(entry_price),
        "quantity": float(quantity),
        "leverage": leverage,
        "margin": float(margin),
        "entry_time": datetime.utcnow().isoformat(),
        "reason": reason,
        "status": "OPEN",
        "take_profits": [],
        "stop_loss": None,
        "trailing_activated": False
    }
    
    # Calculate SL/TP prices from config
    try:
        from config import PRICE_SL, PRICE_TP, TP1_PERCENT, TP2_PERCENT
    except ImportError:
        PRICE_SL, PRICE_TP, TP1_PERCENT, TP2_PERCENT = 4.0, 8.0, 3.0, 5.0
    
    if side == "LONG":
        position["stop_loss"] = entry_price * (1 - PRICE_SL / 100)
        position["tp1"] = entry_price * (1 + TP1_PERCENT / 100)
        position["tp2"] = entry_price * (1 + TP2_PERCENT / 100)
        position["take_profit"] = entry_price * (1 + PRICE_TP / 100)
    else:  # SHORT
        position["stop_loss"] = entry_price * (1 + PRICE_SL / 100)
        position["tp1"] = entry_price * (1 - TP1_PERCENT / 100)
        position["tp2"] = entry_price * (1 - TP2_PERCENT / 100)
        position["take_profit"] = entry_price * (1 - PRICE_TP / 100)
    
    positions[order_id] = position
    balance["available"] -= margin
    balance["used_margin"] += margin
    
    save_positions(positions)
    save_balance(balance)
    
    log_trade({
        "type": "OPEN",
        "order_id": order_id,
        "symbol": symbol,
        "side": side,
        "price": float(entry_price),
        "quantity": float(quantity),
        "margin": float(margin),
        "reason": reason
    })
    
    return {"success": True, "order_id": order_id, "position": position}

def close_position(order_id, close_price, reason=""):
    """Close a paper position"""
    positions = load_positions()
    balance = load_balance()
    
    if order_id not in positions:
        return {"error": f"Position {order_id} not found"}
    
    pos = positions[order_id]
    pos["side"] = "LONG" if pos.get("side") in ("LONG","BUY") else "SHORT"
    
    # Calculate PnL
    if pos["side"] == "LONG":
        pnl = (close_price - pos["entry_price"]) * pos["quantity"]
    else:  # SHORT
        pnl = (pos["entry_price"] - close_price) * pos["quantity"]
    
    pnl_pct = (pnl / pos["margin"]) * 100
    
    # Update balance
    balance["available"] += pos["margin"] + pnl
    balance["used_margin"] -= pos["margin"]
    balance["total"] += pnl
    balance["unrealized_pnl"] = 0  # Reset since we closed
    
    # Update position
    pos["status"] = "CLOSED"
    pos["close_price"] = float(close_price)
    pos["close_time"] = datetime.utcnow().isoformat()
    pos["pnl"] = float(pnl)
    pos["pnl_pct"] = float(pnl_pct)
    pos["close_reason"] = reason
    
    save_positions(positions)
    save_balance(balance)
    
    # Update stats
    update_stats(pnl, pnl_pct, pos["side"], reason)
    
    log_trade({
        "type": "CLOSE",
        "order_id": order_id,
        "symbol": pos["symbol"],
        "side": pos["side"],
        "entry_price": pos["entry_price"],
        "close_price": float(close_price),
        "pnl": float(pnl),
        "pnl_pct": float(pnl_pct),
        "reason": reason,
        "duration": str(datetime.utcnow() - datetime.fromisoformat(pos["entry_time"]))
    })
    
    return {
        "success": True,
        "pnl": float(pnl),
        "pnl_pct": float(pnl_pct),
        "reason": reason
    }

def update_position_sl_tp(order_id, stop_loss=None, take_profit=None, tp1=None, tp2=None):
    """Update SL/TP for a position"""
    positions = load_positions()
    
    if order_id not in positions:
        return {"error": f"Position {order_id} not found"}
    
    if stop_loss is not None:
        positions[order_id]["stop_loss"] = float(stop_loss)
    if take_profit is not None:
        positions[order_id]["take_profit"] = float(take_profit)
    if tp1 is not None:
        positions[order_id]["tp1"] = float(tp1)
    if tp2 is not None:
        positions[order_id]["tp2"] = float(tp2)
    
    save_positions(positions)
    return {"success": True}

def check_positions(current_prices):
    """
    Check all open positions against current prices.
    Returns list of actions to take (SL hit, TP hit, etc.)
    """
    positions = load_positions()
    balance = load_balance()
    actions = []
    unrealized_total = 0
    
    for order_id, pos in positions.items():
        if pos["status"] != "OPEN":
            continue
        pos["side"] = "LONG" if pos.get("side") in ("LONG","BUY") else "SHORT"
        
        symbol = pos["symbol"]
        if symbol not in current_prices:
            continue
        
        current_price = current_prices[symbol]
        
        # Calculate unrealized PnL
        if pos["side"] == "LONG":
            pnl = (current_price - pos["entry_price"]) * pos["quantity"]
            pnl_pct = ((current_price - pos["entry_price"]) / pos["entry_price"]) * 100
        else:  # SHORT
            pnl = (pos["entry_price"] - current_price) * pos["quantity"]
            pnl_pct = ((pos["entry_price"] - current_price) / pos["entry_price"]) * 100
        
        unrealized_total += pnl
        
        # Auto-close logic
        from datetime import datetime, timedelta
        try:
            entry_dt = datetime.fromisoformat(pos.get("entry_time", datetime.utcnow().isoformat()))
            hold_hours = (datetime.utcnow() - entry_dt).total_seconds() / 3600
            
            # === INSTANT CUT LOSS: loss gede langsung potong ===
            # -15% loss → langsung cut, jangan tunggu makin dalam
            if pnl_pct <= -15:
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": "INSTANT_CUT", "price": current_price})
                continue
            # -10% loss dalam 30 menit pertama → cut cepat
            if hold_hours < 0.5 and pnl_pct <= -10:
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": "QUICK_CUT", "price": current_price})
                continue
            # -8% loss dalam 1 jam pertama → cut
            if hold_hours < 1 and pnl_pct <= -8:
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": "QUICK_CUT", "price": current_price})
                continue
            
            # === INSTANT TP: profit gede langsung ambil ===
            # 50%+ profit → langsung TP, gak usah tunggu
            if pnl_pct >= 50:
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": "BIG_TP_50", "price": current_price})
                continue
            # 25%+ profit → TP juga
            if pnl_pct >= 25:
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": "BIG_TP_25", "price": current_price})
                continue
            # 10%+ profit di bawah 1 jam → TP (cepet banget ijo)
            if hold_hours < 1 and pnl_pct >= 10:
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": "QUICK_TP", "price": current_price})
                continue
            
            # === TIME-BASED ===
            # 2h: lock profit kalau udah ijo > 2%
            if hold_hours > 2 and pnl_pct >= 2:
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": "TIME_TP", "price": current_price})
                continue
            # 4h: take profit kalau ijo > 0.5%
            if hold_hours > 4 and pnl_pct >= 0.5:
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": "TIME_TP", "price": current_price})
                continue
            # 8h: ambil berapapun profit
            if hold_hours > 8 and pnl_pct > 0:
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": "TIME_TP", "price": current_price})
                continue
            # 12h: cut loss, ganti opportunity lain
            if hold_hours > 12:
                reason = "TIMEOUT_LOSS" if pnl_pct < 0 else "TIMEOUT_WIN"
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": reason, "price": current_price})
                continue
        except:
            pass
        
        # Check SL
        if pos["side"] == "LONG" and current_price <= pos["stop_loss"]:
            actions.append({"action": "CLOSE", "order_id": order_id, "reason": "STOP_LOSS", "price": current_price})
        elif pos["side"] == "SHORT" and current_price >= pos["stop_loss"]:
            actions.append({"action": "CLOSE", "order_id": order_id, "reason": "STOP_LOSS", "price": current_price})
        
        # Check TP1
        elif "tp1" in pos and pos["tp1"] not in pos.get("take_profits", []):
            if pos["side"] == "LONG" and current_price >= pos["tp1"]:
                actions.append({"action": "PARTIAL_TP", "order_id": order_id, "reason": "TP1", "price": current_price, "close_pct": 0.25})
            elif pos["side"] == "SHORT" and current_price <= pos["tp1"]:
                actions.append({"action": "PARTIAL_TP", "order_id": order_id, "reason": "TP1", "price": current_price, "close_pct": 0.25})
        
        # Check TP2
        elif "tp2" in pos and pos["tp2"] not in pos.get("take_profits", []):
            if pos["side"] == "LONG" and current_price >= pos["tp2"]:
                actions.append({"action": "PARTIAL_TP", "order_id": order_id, "reason": "TP2", "price": current_price, "close_pct": 0.25})
            elif pos["side"] == "SHORT" and current_price <= pos["tp2"]:
                actions.append({"action": "PARTIAL_TP", "order_id": order_id, "reason": "TP2", "price": current_price, "close_pct": 0.25})
        
        # Check final TP
        else:
            if pos["side"] == "LONG" and current_price >= pos["take_profit"]:
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": "TAKE_PROFIT", "price": current_price})
            elif pos["side"] == "SHORT" and current_price <= pos["take_profit"]:
                actions.append({"action": "CLOSE", "order_id": order_id, "reason": "TAKE_PROFIT", "price": current_price})
    
    # Update unrealized PnL
    balance["unrealized_pnl"] = unrealized_total
    save_balance(balance)
    
    return actions

def update_stats(pnl, pnl_pct, side, reason):
    # Normalize side: positions use BUY/SELL, stats keyed by LONG/SHORT
    side = {"BUY": "LONG", "SELL": "SHORT"}.get(side, side)
    """Update trading statistics"""
    ensure_dirs()
    
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            stats = json.load(f)
    else:
        stats = {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "by_side": {"LONG": {"wins": 0, "losses": 0, "pnl": 0.0}, 
                       "SHORT": {"wins": 0, "losses": 0, "pnl": 0.0}},
            "by_reason": {},
            "created_at": datetime.utcnow().isoformat()
        }
    
    stats["total_trades"] += 1
    stats["total_pnl"] += pnl
    
    if pnl > 0:
        stats["wins"] += 1
        stats["by_side"][side]["wins"] += 1
        if pnl > stats["best_trade"]:
            stats["best_trade"] = pnl
    else:
        stats["losses"] += 1
        stats["by_side"][side]["losses"] += 1
        if pnl < stats["worst_trade"]:
            stats["worst_trade"] = pnl
    
    stats["by_side"][side]["pnl"] += pnl
    
    if reason not in stats["by_reason"]:
        stats["by_reason"][reason] = {"count": 0, "pnl": 0.0}
    stats["by_reason"][reason]["count"] += 1
    stats["by_reason"][reason]["pnl"] += pnl
    
    # Calculate win rate
    if stats["total_trades"] > 0:
        stats["win_rate"] = (stats["wins"] / stats["total_trades"]) * 100
    
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

def get_stats():
    """Get current trading statistics"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            return json.load(f)
    return {"total_trades": 0, "wins": 0, "losses": 0, "win_rate": 0, "total_pnl": 0}

def get_dashboard():
    """Get paper trading dashboard data"""
    balance = load_balance()
    positions = load_positions()
    stats = get_stats()
    
    open_positions = {k: v for k, v in positions.items() if v["status"] == "OPEN"}
    
    return {
        "balance": balance,
        "open_positions": open_positions,
        "position_count": len(open_positions),
        "stats": stats,
        "mode": "PAPER_TRADING"
    }

def reset_paper_account():
    """Reset paper account to initial state"""
    ensure_dirs()
    
    balance = {
        "available": INITIAL_BALANCE,
        "total": INITIAL_BALANCE,
        "used_margin": 0.0,
        "unrealized_pnl": 0.0,
        "created_at": datetime.utcnow().isoformat()
    }
    save_balance(balance)
    save_positions({})
    
    # Clear trade log
    with open(TRADE_LOG_FILE, "w") as f:
        pass
    
    print(f"Paper account reset. Balance: {INITIAL_BALANCE} USDT")
    return balance

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 paper_trader.py [dashboard|reset|positions|stats]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "dashboard":
        data = get_dashboard()
        print(json.dumps(data, indent=2))
    elif cmd == "reset":
        reset_paper_account()
    elif cmd == "positions":
        positions = load_positions()
        print(json.dumps(positions, indent=2))
    elif cmd == "stats":
        stats = get_stats()
        print(json.dumps(stats, indent=2))
    else:
        print(f"Unknown command: {cmd}")
