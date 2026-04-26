#!/usr/bin/env python3
"""
Near-High Filter Backtest (Optimized)

Tests different near-high filter thresholds (0%, 2%, 4%, 6%).
Focus: Does the near-high filter actually improve win rate vs opportunity cost?

Usage:
    python3 scripts/backtest_near_high.py [--symbols 10] [--min-score 4]
"""

import os, sys, json, math, time, argparse
from datetime import datetime
from typing import List, Dict

try:
    import requests
except ImportError:
    print("❌ pip install requests"); sys.exit(1)

PRICE_SL = 5.0
PRICE_TP = 15.0
BINANCE_FAPI = "https://fapi.binance.com"


def get_top_symbols(n=10):
    r = requests.get(f"{BINANCE_FAPI}/fapi/v1/ticker/24hr", timeout=15)
    usdt = [t for t in r.json() if t['symbol'].endswith('USDT')
            and float(t.get('quoteVolume', 0)) > 5_000_000
            and not any(x in t['symbol'] for x in ['UP','DOWN','BULL','BEAR'])]
    usdt.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
    return [t['symbol'] for t in usdt[:n]]


def get_klines(symbol, limit=500):
    try:
        r = requests.get(f"{BINANCE_FAPI}/fapi/v1/klines",
                        params={'symbol': symbol, 'interval': '1h', 'limit': limit}, timeout=15)
        return r.json()
    except:
        return []


def calc_ema_list(prices, period):
    """Fast EMA calculation returning full list."""
    if len(prices) < period:
        return [None] * len(prices)
    k = 2 / (period + 1)
    result = [None] * (period - 1)
    ema = sum(prices[:period]) / period  # SMA seed
    result.append(ema)
    for price in prices[period:]:
        ema = price * k + ema * (1 - k)
        result.append(ema)
    return result


def calc_rsi_list(closes, period=14):
    """Fast RSI list."""
    if len(closes) < period + 1:
        return [50] * len(closes)
    result = [50] * period
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [max(-d, 0) for d in deltas]
    
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    
    for i in range(period, len(deltas)):
        if i >= period:
            avg_g = (avg_g * (period - 1) + gains[i]) / period
            avg_l = (avg_l * (period - 1) + losses[i]) / period
        if avg_l == 0:
            result.append(100)
        else:
            rs = avg_g / avg_l
            result.append(100 - (100 / (1 + rs)))
    return result


def precompute_indicators(candles):
    """Precompute all indicators once per symbol. Returns dict of lists."""
    closes = [float(c[4]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    volumes = [float(c[5]) for c in candles]
    
    n = len(closes)
    
    # EMAs
    ema9 = calc_ema_list(closes, 9)
    ema21 = calc_ema_list(closes, 21)
    ema50 = calc_ema_list(closes, 50) if n >= 50 else [None] * n
    
    # RSI
    rsi = calc_rsi_list(closes, 14)
    
    # Rolling high/low for near-high filter
    rolling_high_20 = [max(highs[max(0,i-19):i+1]) for i in range(n)]
    rolling_low_20 = [min(lows[max(0,i-19):i+1]) for i in range(n)]
    
    # Volume ratio (vs 24h avg)
    vol_ratio = [1.0] * 24
    for i in range(24, n):
        avg = sum(volumes[i-24:i]) / 24
        vol_ratio.append(volumes[i] / avg if avg > 0 else 1)
    
    # Price change 24h
    price_chg = [0.0] * 24
    for i in range(24, n):
        price_chg.append((closes[i] - closes[i-24]) / closes[i-24] * 100)
    
    # SMA50 trend
    sma50 = [sum(closes[max(0,i-49):i+1]) / min(50, i+1) for i in range(n)]
    
    # Simplified VWAP (24h typical * vol)
    vwap = [closes[0]] * 24
    for i in range(24, n):
        tp_vol = sum(((highs[j]+lows[j]+closes[j])/3) * volumes[j] for j in range(i-23, i+1))
        v_vol = sum(volumes[j] for j in range(i-23, i+1))
        vwap.append(tp_vol / v_vol if v_vol > 0 else closes[i])
    
    # ATR for ema_position
    tr = [0] * n
    for i in range(1, n):
        tr[i] = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
    atr = [0] * 14
    for i in range(14, n):
        atr.append(sum(tr[i-13:i+1]) / 14)
    
    # EMA position
    ema_pos = [50] * n
    for i in range(14, n):
        if ema21[i] and atr[i] > 0:
            band_low = ema21[i] - atr[i]
            band_high = ema21[i] + atr[i]
            if band_high > band_low:
                ema_pos[i] = (closes[i] - band_low) / (band_high - band_low) * 100
    
    # MACD histogram (simplified)
    macd_hist = [0] * 35
    for i in range(35, n):
        if ema9[i] and ema21[i]:
            macd_line = ema9[i] - ema21[i]
            macd_hist.append(macd_line)  # Simplified
    
    # Choppiness (14)
    chop = [50] * 14
    for i in range(14, n):
        atr_sum = sum(tr[i-13:i+1])
        hh = max(highs[i-13:i+1])
        ll = min(lows[i-13:i+1])
        if hh > ll and atr_sum > 0:
            chop.append(min(100, max(0, 100 * atr_sum / (14 * (hh - ll)))))
        else:
            chop.append(50)
    
    return {
        'closes': closes, 'highs': highs, 'lows': lows, 'volumes': volumes,
        'ema9': ema9, 'ema21': ema21, 'ema50': ema50,
        'rsi': rsi, 'rolling_high_20': rolling_high_20, 'rolling_low_20': rolling_low_20,
        'vol_ratio': vol_ratio, 'price_chg': price_chg, 'sma50': sma50,
        'vwap': vwap, 'ema_pos': ema_pos, 'macd_hist': macd_hist, 'chop': chop,
    }


def score_at(idx, ind, direction):
    """Score a signal at bar idx using precomputed indicators."""
    closes = ind['closes']
    score = 0
    
    vr = ind['vol_ratio'][idx]
    pc = ind['price_chg'][idx]
    ema_p = ind['ema_pos'][idx]
    r = ind['rsi'][idx]
    v = ind['vwap'][idx]
    e9 = ind['ema9'][idx]
    e21 = ind['ema21'][idx]
    sma = ind['sma50'][idx]
    ch = ind['chop'][idx]
    mh = ind['macd_hist'][idx]
    cur = closes[idx]
    
    if direction == "LONG":
        if vr >= 3: score += 1
        if pc > 10: score += 2
        elif pc > 5: score += 1
        if cur > sma: score += 1
        if 0 <= ema_p <= 100 and ema_p < 50: score += 1
        if r < 30: score += 1
        if cur > v: score += 1
        if e9 and cur > e9: score += 1
        if cur > v and (e9 and cur > e9): score += 1
    else:  # SHORT
        if e9 and e21 and e9 < e21: score += 2
        if e9 and e21 and cur < e9 and cur < e21: score += 1
        if r < 50: score += 1
        if mh < 0: score += 2
        if pc < -2: score += 2
        if cur < v: score += 1
        if e9 and cur < e9: score += 1
        if cur < v and (e9 and cur < e9): score += 1
    
    return score


def passes_filters(idx, ind, direction, near_high_pct):
    """Check filters at bar idx."""
    r = ind['rsi'][idx]
    ep = ind['ema_pos'][idx]
    ch = ind['chop'][idx]
    mh = ind['macd_hist'][idx]
    cur = ind['closes'][idx]
    
    # EMA position
    if direction == "LONG" and ep > 70: return False
    if direction == "SHORT" and ep < 30: return False
    
    # RSI
    if direction == "LONG" and r > 65: return False
    if direction == "SHORT" and r < 35: return False
    
    # Near high/low (THE FILTER WE'RE TESTING)
    if near_high_pct > 0:
        if direction == "LONG":
            rh = ind['rolling_high_20'][idx]
            if cur >= rh * (1 - near_high_pct / 100): return False
        else:
            rl = ind['rolling_low_20'][idx]
            if cur <= rl * (1 + near_high_pct / 100): return False
    
    # Choppiness
    if ch > 60: return False
    
    # MACD
    if direction == "LONG" and mh < 0: return False
    if direction == "SHORT" and mh > 0: return False
    
    return True


def simulate_trade(closes, highs, lows, entry_idx, direction):
    """Simulate SL/TP trade. Returns (pnl_pct, exit_reason)."""
    entry = closes[entry_idx]
    
    if direction == "LONG":
        sl = entry * (1 - PRICE_SL / 100)
        tp = entry * (1 + PRICE_TP / 100)
    else:
        sl = entry * (1 + PRICE_SL / 100)
        tp = entry * (1 - PRICE_TP / 100)
    
    end = min(entry_idx + 48, len(closes) - 1)
    
    for i in range(entry_idx + 1, end + 1):
        h, l = highs[i], lows[i]
        if direction == "LONG":
            if l <= sl: return -PRICE_SL, 'SL'
            if h >= tp: return PRICE_TP, 'TP'
        else:
            if h >= sl: return -PRICE_SL, 'SL'
            if l <= tp: return PRICE_TP, 'TP'
    
    # Time exit
    exit_p = closes[end]
    pnl = ((exit_p - entry) / entry * 100) if direction == "LONG" else ((entry - exit_p) / entry * 100)
    return pnl, 'TIME'


def run_backtest(symbols, near_high_pct, min_score=4):
    all_trades = []
    
    for sym in symbols:
        print(f"  📡 {sym}...", end=" ", flush=True)
        candles = get_klines(sym, 500)
        if len(candles) < 100:
            print(f"skip ({len(candles)} bars)")
            continue
        
        ind = precompute_indicators(candles)
        n = len(ind['closes'])
        sym_trades = 0
        last_trade = -10
        
        for i in range(50, n - 49):
            if i - last_trade < 2: continue
            
            pc = ind['price_chg'][i]
            
            for direction in ["LONG", "SHORT"]:
                if direction == "LONG" and pc < 0: continue
                if direction == "SHORT" and pc >= 0: continue
                
                score = score_at(i, ind, direction)
                if score < min_score: continue
                if not passes_filters(i, ind, direction, near_high_pct): continue
                
                pnl, reason = simulate_trade(ind['closes'], ind['highs'], ind['lows'], i, direction)
                all_trades.append({
                    'symbol': sym, 'direction': direction,
                    'pnl_pct': pnl, 'exit_reason': reason, 'score': score,
                    'rsi': ind['rsi'][i], 'ema_pos': ind['ema_pos'][i],
                    'chop': ind['chop'][i], 'vol_ratio': ind['vol_ratio'][i],
                })
                last_trade = i
                sym_trades += 1
                break
        
        print(f"{sym_trades} trades")
    
    return all_trades


def print_stats(trades, label):
    if not trades:
        print(f"\n  📊 {label}: NO TRADES")
        return {}
    
    wins = [t for t in trades if t['pnl_pct'] > 0]
    losses = [t for t in trades if t['pnl_pct'] <= 0]
    total = len(trades)
    wr = len(wins) / total * 100
    gp = sum(t['pnl_pct'] for t in wins) if wins else 0
    gl = abs(sum(t['pnl_pct'] for t in losses)) if losses else 0
    pf = gp / gl if gl > 0 else 999
    sl = len([t for t in trades if t['exit_reason'] == 'SL'])
    tp = len([t for t in trades if t['exit_reason'] == 'TP'])
    
    stats = {'total': total, 'win_rate': wr, 'profit_factor': pf,
             'net_pnl': sum(t['pnl_pct'] for t in trades),
             'sl_count': sl, 'tp_count': tp,
             'avg_win': sum(t['pnl_pct'] for t in wins) / len(wins) if wins else 0,
             'avg_loss': sum(t['pnl_pct'] for t in losses) / len(losses) if losses else 0}
    
    print(f"\n  📊 {label}")
    print(f"     Trades: {total} | WR: {wr:.1f}% | PF: {pf:.2f} | Net: {sum(t['pnl_pct'] for t in trades):+.1f}%")
    print(f"     SL: {sl} ({sl/total*100:.0f}%) | TP: {tp} ({tp/total*100:.0f}%)")
    print(f"     Avg Win: {stats['avg_win']:+.1f}% | Avg Loss: {stats['avg_loss']:+.1f}%")
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbols', type=int, default=15)
    parser.add_argument('--min-score', type=int, default=4)
    args = parser.parse_args()
    
    print("🐱 NEKO NEAR-HIGH FILTER BACKTEST")
    print(f"   Top {args.symbols} symbols | SL={PRICE_SL}% | TP={PRICE_TP}% | Min Score={args.min_score}")
    print()
    
    print("📡 Fetching symbols...")
    symbols = get_top_symbols(args.symbols)
    print(f"   {', '.join(symbols)}")
    
    thresholds = [0, 2, 4, 6]
    results = {}
    
    for thresh in thresholds:
        label = f"Filter: {thresh}%" if thresh > 0 else "No Filter (0%)"
        print(f"\n🔄 {label}")
        trades = run_backtest(symbols, thresh, args.min_score)
        results[thresh] = print_stats(trades, label)
    
    # === COMPARISON ===
    print(f"\n{'='*65}")
    print("📊 COMPARISON")
    print(f"{'='*65}")
    print(f"{'Filter':<12} {'Trades':>8} {'Win%':>8} {'Net PNL':>10} {'PF':>8} {'SL%':>7} {'TP%':>7}")
    print("-" * 65)
    
    for thresh in thresholds:
        s = results.get(thresh, {})
        if not s: continue
        total = s['total']
        sl_p = s['sl_count'] / total * 100 if total else 0
        tp_p = s['tp_count'] / total * 100 if total else 0
        print(f"  {thresh}%{'':<9} {total:>8} {s['win_rate']:>7.1f}% {s['net_pnl']:>+9.1f}% {s['profit_factor']:>7.2f} {sl_p:>6.0f}% {tp_p:>6.0f}%")
    
    # Save
    out = os.path.expanduser('~/workspace/neko-futures-trader/scripts/backtest_results.json')
    with open(out, 'w') as f:
        json.dump({'config': {'sl': PRICE_SL, 'tp': PRICE_TP, 'min_score': args.min_score},
                   'results': {str(k): v for k, v in results.items()},
                   'run_at': datetime.now().isoformat()}, f, indent=2)
    print(f"\n💾 Saved to {out}")


if __name__ == "__main__":
    main()
