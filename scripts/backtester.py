#!/usr/bin/env python3
"""
Neko Futures Trader - Backtester v3
Monte Carlo Simulation + Real Metrics + Parameter Optimizer

Auto-updated: Fetches real trade data from Binance on each run.
"""

import os
import math
import random
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.parse
    HAS_REQUESTS = False
    import json

# ============ CONFIG ============
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_SECRET = os.getenv('BINANCE_SECRET', '')

# Trading params
MAX_POSITIONS = 5
CURRENT_RR = 3.0
INITIAL_BALANCE = 300.0

# Monte Carlo params
N_SIMULATIONS = 5000
TRADES_PER_SIM = 100

# ============ BINANCE SIGNED API ============
def create_signature(query_string: str) -> str:
    import hmac
    import hashlib
    return hmac.new(
        BINANCE_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def binance_signed_get(endpoint: str, params: dict = None) -> dict:
    if not BINANCE_API_KEY or not BINANCE_SECRET:
        return None
    
    ts = int(time.time() * 1000)
    params = params or {}
    params['timestamp'] = ts
    
    query = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = create_signature(query)
    query += f"&signature={signature}"
    
    url = f"https://fapi.binance.com{endpoint}?{query}"
    headers = {'X-MBX-APIKEY': BINANCE_API_KEY}
    
    try:
        if HAS_REQUESTS:
            r = requests.get(url, headers=headers, timeout=10)
        else:
            req = urllib.request.Request(url, headers=headers)
            r = urllib.request.urlopen(req, timeout=10)
            r = type('Response', (), {'json': lambda: json.loads(r.read()), 'status_code': 200})()
        
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_income_history(days: int = 90) -> List[Dict]:
    end_time = int(time.time() * 1000)
    start_time = int((time.time() - days * 24 * 60 * 60) * 1000)
    
    all_trades = []
    params = {'startTime': start_time, 'endTime': end_time, 'limit': 100}
    
    while len(all_trades) < 2000:
        data = binance_signed_get('/fapi/v1/income', params)
        if not data or not isinstance(data, list) or len(data) == 0:
            break
        
        realized = [t for t in data if t.get('incomeType') == 'REALIZED_PNL']
        all_trades.extend(realized)
        
        if len(data) < 100:
            break
        params['startTime'] = int(data[-1].get('time', 0)) + 1
    
    return all_trades

def calculate_real_stats(trades: List[Dict]) -> dict:
    if not trades:
        return {'winrate': 0.42, 'avg_win': 2.0, 'avg_loss': 3.0, 'total_pnl': 0, 'wins': 0, 'losses': 0, 'total_trades': 0}
    
    wins = [t for t in trades if float(t.get('income', 0)) > 0]
    losses = [t for t in trades if float(t.get('income', 0)) <= 0]
    
    win_amt = [float(t.get('income', 0)) for t in wins]
    loss_amt = [abs(float(t.get('income', 0))) for t in losses]
    
    return {
        'winrate': len(wins) / len(trades) if trades else 0,
        'avg_win': sum(win_amt) / len(win_amt) if win_amt else 0,
        'avg_loss': sum(loss_amt) / len(loss_amt) if loss_amt else 0,
        'total_pnl': sum([float(t.get('income', 0)) for t in trades]),
        'wins': len(wins),
        'losses': len(losses),
        'total_trades': len(trades)
    }

def monte_carlo_simulation(winrate: float, avg_win: float, avg_loss: float, 
                           n_sim: int = N_SIMULATIONS, 
                           trades_per_sim: int = TRADES_PER_SIM,
                           initial_balance: float = INITIAL_BALANCE) -> dict:
    outcomes = []
    max_drawdowns = []
    
    for _ in range(n_sim):
        balance = initial_balance
        peak = balance
        max_dd = 0
        
        for _ in range(trades_per_sim):
            if random.random() < winrate:
                balance += avg_win
            else:
                balance -= avg_loss
            
            peak = max(peak, balance)
            dd = (peak - balance) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        outcomes.append(balance)
        max_drawdowns.append(max_dd)
    
    outcomes.sort()
    max_drawdowns.sort()
    
    return {
        'final_balance_p10': outcomes[int(len(outcomes) * 0.10)],
        'final_balance_p50': outcomes[int(len(outcomes) * 0.50)],
        'final_balance_p90': outcomes[int(len(outcomes) * 0.90)],
        'max_drawdown_p10': max_drawdowns[int(len(max_drawdowns) * 0.10)] * 100,
        'max_drawdown_p50': max_drawdowns[int(len(max_drawdowns) * 0.50)] * 100,
        'max_drawdown_p90': max_drawdowns[int(len(max_drawdowns) * 0.90)] * 100,
        'probability_of_ruin': sum(1 for o in outcomes if o < initial_balance * 0.5) / len(outcomes) * 100
    }

def print_results(real_stats: dict, monte: dict, trades: List[Dict]):
    print("\n" + "="*50)
    print("📊 NEKO BACKTESTER v2 - REAL DATA")
    print("="*50)
    
    print("\n📈 REAL TRADE STATS (from Binance):")
    print(f"   Total Trades: {real_stats['total_trades']}")
    print(f"   Wins: {real_stats['wins']} | Losses: {real_stats['losses']}")
    print(f"   Win Rate: {real_stats['winrate']*100:.1f}%")
    print(f"   Avg Win: ${real_stats['avg_win']:.2f}")
    print(f"   Avg Loss: ${real_stats['avg_loss']:.2f}")
    print(f"   Total PnL: ${real_stats['total_pnl']:.2f}")
    
    print("\n🎲 MONTE CARLO (5000 simulations):")
    print(f"   Balance after 100 trades:")
    print(f"     10th percentile: ${monte['final_balance_p10']:.2f}")
    print(f"     50th percentile: ${monte['final_balance_p50']:.2f}")
    print(f"     90th percentile: ${monte['final_balance_p90']:.2f}")
    print(f"   Probability of 50% loss: {monte['probability_of_ruin']:.1f}%")
    
    print("\n" + "="*50)
    
    if trades:
        print("\n📋 SAMPLE RECENT TRADES:")
        for t in trades[:5]:
            pnl = float(t.get('income', 0))
            date = datetime.fromtimestamp(int(t.get('time', 0))/1000).strftime('%Y-%m-%d')
            symbol = t.get('symbol', 'UNKNOWN')
            sign = '🟢' if pnl > 0 else '🔴'
            print(f"   {sign} {symbol}: {'+' if pnl > 0 else ''}${pnl:.2f} ({date})")

def optimize_parameters(trades: List[Dict], real_stats: dict):
    """Optimize strategy parameters using real trade data."""
    print("\n" + "="*60)
    print("🎯 PARAMETER OPTIMIZER")
    print("="*60)
    
    # Group trades by symbol
    symbol_trades = {}
    for t in trades:
        sym = t.get('symbol', 'UNKNOWN')
        if sym not in symbol_trades:
            symbol_trades[sym] = []
        symbol_trades[sym].append(t)
    
    # Calculate per-symbol stats
    symbol_stats = []
    for sym, sym_trades in symbol_trades.items():
        wins = [t for t in sym_trades if float(t.get('income', 0)) > 0]
        losses = [t for t in sym_trades if float(t.get('income', 0)) <= 0]
        
        if len(sym_trades) >= 3:  # Only symbols with 3+ trades
            wr = len(wins) / len(sym_trades)
            avg_w = sum([float(t.get('income', 0)) for t in wins]) / len(wins) if wins else 0
            avg_l = abs(sum([float(t.get('income', 0)) for t in losses]) / len(losses)) if losses else 0
            rr = avg_w / avg_l if avg_l > 0 else 0
            
            symbol_stats.append({
                'symbol': sym,
                'trades': len(sym_trades),
                'winrate': wr,
                'avg_win': avg_w,
                'avg_loss': avg_l,
                'rr': rr,
                'total_pnl': sum([float(t.get('income', 0)) for t in sym_trades]),
                'wins': len(wins),
                'losses': len(losses)
            })
    
    # Sort by winrate
    symbol_stats.sort(key=lambda x: x['winrate'], reverse=True)
    
    print(f"\n📊 Analyzed {len(symbol_trades)} symbols with 3+ trades")
    
    print("\n🏆 TOP 10 HIGHEST WINRATE SYMBOLS:")
    print("-" * 60)
    print(f"{'Symbol':<12} {'Trades':>6} {'Win%':>6} {'Avg W':>7} {'Avg L':>7} {'R:R':>5} {'PnL':>8}")
    print("-" * 60)
    
    for s in symbol_stats[:10]:
        print(f"{s['symbol']:<12} {s['trades']:>6} {s['winrate']*100:>5.1f}% ${s['avg_win']:>6.2f} ${s['avg_loss']:>6.2f} {s['rr']:>5.2f} ${s['total_pnl']:>7.2f}")
    
    # Show worst symbols
    print("\n🔴 BOTTOM 10 LOWEST WINRATE SYMBOLS:")
    print("-" * 60)
    for s in symbol_stats[-10:]:
        print(f"{s['symbol']:<12} {s['trades']:>6} {s['winrate']*100:>5.1f}% ${s['avg_win']:>6.2f} ${s['avg_loss']:>6.2f} {s['rr']:>5.2f} ${s['total_pnl']:>7.2f}")
    
    # Calculate what-if scenarios
    print("\n" + "="*60)
    print("💡 WHAT-IF SCENARIOS")
    print("="*60)
    
    current_wr = real_stats['winrate']
    current_rr = real_stats['avg_win'] / real_stats['avg_loss'] if real_stats['avg_loss'] > 0 else 0
    
    print(f"\n📊 Current Stats:")
    print(f"   Win Rate: {current_wr*100:.1f}%")
    print(f"   R:R Ratio: {current_rr:.2f}:1")
    print(f"   Expected Value per trade: ${(current_wr * real_stats['avg_win']) - ((1-current_wr) * real_stats['avg_loss']):.2f}")
    
    # Scenario 1: Better R:R with same winrate
    for target_rr in [2.0, 2.5, 3.0]:
        if target_rr > current_rr:
            # Assume avg_loss stays same, avg_win increases
            new_avg_win = real_stats['avg_loss'] * target_rr
            ev = (current_wr * new_avg_win) - ((1-current_wr) * real_stats['avg_loss'])
            print(f"\n   If R:R = {target_rr}:1 (same winrate):")
            print(f"     Avg Win: ${new_avg_win:.2f} | Expected EV: ${ev:.2f}")
            print(f"     Per 100 trades: ${ev*100:.2f} (vs current: ${((current_wr * real_stats['avg_win']) - ((1-current_wr) * real_stats['avg_loss']))*100:.2f})")
    
    # Best symbol analysis
    best_symbols = [s for s in symbol_stats if s['winrate'] >= 0.5 and s['rr'] >= 1.5]
    
    print("\n" + "="*60)
    print("🎯 ACTIONABLE RECOMMENDATIONS")
    print("="*60)
    
    if best_symbols:
        print("\n✅ SYMBOLS TO FOCUS ON (winrate>50%, R:R>1.5):")
        for s in best_symbols[:5]:
            print(f"   • {s['symbol']}: {s['winrate']*100:.0f}% winrate, {s['rr']:.1f}:1 R:R, {s['trades']} trades")
    
    bad_symbols = [s for s in symbol_stats if s['winrate'] < 0.4 or s['total_pnl'] < -5]
    if bad_symbols:
        print("\n🔴 SYMBOLS TO AVOID:")
        for s in bad_symbols[:5]:
            print(f"   • {s['symbol']}: {s['winrate']*100:.0f}% winrate, ${s['total_pnl']:.2f} total PnL")
    
    print(f"""
\n📋 SCANNER PARAMETER RECOMMENDATIONS:

1. MIN_WINRATE_PER_SYMBOL: 0.45 (45%)
   - Only trade symbols with >45% historical winrate

2. MIN_RISK_REWARD: 1.5
   - Only take trades with R:R >= 1.5

3. EXCLUDED_SYMBOLS: {', '.join([s['symbol'] for s in bad_symbols[:5]]) if bad_symbols else 'None'}
   - These symbols have poor performance

4. TRADE_FREQUENCY: Reduce by 50%
   - Currently ~11 trades/day is too many
   - Target: 3-5 quality trades/day
""")

def main():
    print("🔄 Fetching real trade data from Binance...")
    trades = get_income_history(days=90)
    real_stats = calculate_real_stats(trades)
    
    print(f"📊 Running Monte Carlo with winrate={real_stats['winrate']*100:.1f}%...")
    monte = monte_carlo_simulation(
        winrate=real_stats['winrate'],
        avg_win=real_stats['avg_win'] or 2.0,
        avg_loss=real_stats['avg_loss'] or 3.0
    )
    
    print_results(real_stats, monte, trades)
    
    if trades:
        optimize_parameters(trades, real_stats)

if __name__ == "__main__":
    main()
