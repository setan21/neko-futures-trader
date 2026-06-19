#!/usr/bin/env python3
"""
Neko Paper Trading Dashboard - View stats, positions, trades
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, "/root/neko-futures-trader")
from paper_trader import get_dashboard, get_stats, load_positions, load_balance

def print_header():
    print("\n" + "=" * 60)
    print("🐱 NEKO FUTURES - PAPER TRADING DASHBOARD")
    print("=" * 60)

def print_balance():
    balance = load_balance()
    print("\n💰 BALANCE")
    print(f"  Total:      ${balance['total']:,.2f} USDT")
    print(f"  Available:  ${balance['available']:,.2f} USDT")
    print(f"  Used Margin: ${balance['used_margin']:,.2f} USDT")
    print(f"  Unrealized: ${balance.get('unrealized_pnl', 0):,.2f} USDT")

def print_positions():
    positions = load_positions()
    open_positions = {k: v for k, v in positions.items() if v["status"] == "OPEN"}
    
    print("\n📊 OPEN POSITIONS")
    if not open_positions:
        print("  No open positions")
        return
    
    for order_id, pos in open_positions.items():
        print(f"\n  [{pos['side']}] {pos['symbol']}")
        print(f"    Entry: ${pos['entry_price']:.4f}")
        print(f"    Qty: {pos['quantity']:.4f}")
        print(f"    Margin: ${pos['margin']:.2f}")
        print(f"    SL: ${pos['stop_loss']:.4f} | TP: ${pos['take_profit']:.4f}")

def print_stats():
    stats = get_stats()
    print("\n📈 STATISTICS")
    print(f"  Total Trades: {stats.get('total_trades', 0)}")
    print(f"  Wins: {stats.get('wins', 0)} | Losses: {stats.get('losses', 0)}")
    print(f"  Win Rate: {stats.get('win_rate', 0):.1f}%")
    print(f"  Total PnL: ${stats.get('total_pnl', 0):,.2f} USDT")
    print(f"  Best Trade: ${stats.get('best_trade', 0):,.2f}")
    print(f"  Worst Trade: ${stats.get('worst_trade', 0):,.2f}")

def print_recent_trades(n=5):
    log_file = "/root/neko-futures-trader/data/paper/trades.jsonl"
    if not os.path.exists(log_file):
        print("\n📝 RECENT TRADES: None")
        return
    
    print(f"\n📝 RECENT TRADES (last {n})")
    trades = []
    with open(log_file) as f:
        for line in f:
            if line.strip():
                trades.append(json.loads(line))
    
    for trade in trades[-n:]:
        t = trade.get('timestamp', '')[:19]
        if trade.get('type') == 'OPEN':
            print(f"  [{t}] OPEN {trade['side']} {trade['symbol']} @ ${trade['price']:.4f}")
        elif trade.get('type') == 'CLOSE':
            pnl = trade.get('pnl', 0)
            emoji = "✅" if pnl > 0 else "❌"
            print(f"  [{t}] {emoji} CLOSE {trade['symbol']} @ ${trade['close_price']:.4f} | PnL: ${pnl:.2f}")

def main():
    print_header()
    print_balance()
    print_positions()
    print_stats()
    print_recent_trades()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
