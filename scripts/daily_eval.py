#!/usr/bin/env python3
"""
Daily Evaluation Script for Neko Futures Scanner
Analyzes last 24h performance, adjusts filters, reports to Telegram.
"""

import os
import sys
import json
import time
import re
import requests
from datetime import datetime, timedelta
from collections import Counter

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'scanner.log')
TRADES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'trades.json')
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.py')

def load_recent_logs(hours=24):
    """Load log lines from the last N hours."""
    if not os.path.exists(LOG_FILE):
        return []
    
    cutoff = time.time() - (hours * 3600)
    lines = []
    with open(LOG_FILE, 'r', errors='ignore') as f:
        for line in f:
            lines.append(line)
    
    # Return last 50000 lines (approx 24h worth)
    return lines[-50000:]

def analyze_signals(lines):
    """Analyze signal generation and rejection patterns."""
    signals = []
    rejections = Counter()
    orders_placed = 0
    order_failures = Counter()
    
    for line in lines:
        if '✅ SIGNAL!' in line:
            m = re.search(r'Checking (\w+) \(([^)]+)\).*✅ SIGNAL! (\w+)', line)
            if m:
                signals.append({
                    'symbol': m.group(1),
                    'change': m.group(2),
                    'direction': m.group(3)
                })
        
        if 'no signal' in line:
            m = re.search(r'\(([^)]+)\)\s*no signal', line)
            if m:
                reason = m.group(1)
                if reason.startswith('score='): rejections['score too low'] += 1
                elif reason.startswith('vol='): rejections['volume too low'] += 1
                elif reason.startswith('ch='): rejections['price change < MIN'] += 1
                elif reason.startswith('chase_'): rejections['chase filter'] += 1
                elif reason.startswith('rsi_short_low'): rejections['RSI SHORT guard'] += 1
                elif reason.startswith('rsi='): rejections['RSI filter'] += 1
                elif reason.startswith('green='): rejections['green candles'] += 1
                elif reason.startswith('red='): rejections['red candles'] += 1
                elif reason.startswith('ema_pos='): rejections['EMA position'] += 1
                elif reason.startswith('near_high'): rejections['near high'] += 1
                elif reason.startswith('near_low'): rejections['near low'] += 1
                elif reason.startswith('hist='): rejections['MACD histogram'] += 1
                elif reason.startswith('4h='): rejections['4h trend mismatch'] += 1
                elif reason.startswith('adx='): rejections['ADX filter'] += 1
                elif reason.startswith('macd_flat'): rejections['MACD flat'] += 1
                elif reason.startswith('score=') and 'post_bonus' in reason: rejections['score post-bonus'] += 1
                else: rejections[reason] += 1
        
        if 'Order:' in line and 'Posted to Telegram' in line:
            orders_placed += 1
        
        if 'Order failed:' in line:
            m = re.search(r'Order failed: (.+)', line)
            if m:
                reason = m.group(1).strip()[:50]
                order_failures[reason] += 1
    
    return {
        'signals': signals,
        'rejections': rejections,
        'orders_placed': orders_placed,
        'order_failures': order_failures
    }

def analyze_trades():
    """Analyze recent trades from Binance API."""
    try:
        # Load API keys
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'portfolio-tracker', 'data')
        # Try to find user data file
        for f in os.listdir(data_dir) if os.path.exists(data_dir) else []:
            if f.endswith('.json') and f != 'wallets.json':
                with open(os.path.join(data_dir, f)) as fh:
                    user_data = json.load(fh)
                    if 'binance_api_key' in user_data:
                        api_key = user_data['binance_api_key']
                        api_secret = user_data['binance_api_secret']
                        break
        else:
            return {'error': 'No Binance API keys found'}
        
        import hmac
        import hashlib
        
        # Get realized PnL
        ts = int(time.time() * 1000)
        params = f'timestamp={ts}&recvWindow=60000'
        sig = hmac.new(api_secret.encode(), params.encode(), hashlib.sha256).hexdigest()
        url = f'https://fapi.binance.com/fapi/v1/income?incomeType=REALIZED_PNL&limit=100&{params}&signature={sig}'
        r = requests.get(url, headers={'X-MBX-APIKEY': api_key}, timeout=10)
        income = r.json()
        
        # Filter last 24h
        cutoff = (time.time() - 86400) * 1000
        recent = [i for i in income if int(i['time']) > cutoff]
        
        by_symbol = {}
        total_pnl = 0
        for i in recent:
            sym = i['symbol']
            pnl = float(i['income'])
            by_symbol.setdefault(sym, {'pnl': 0, 'trades': 0})
            by_symbol[sym]['pnl'] += pnl
            by_symbol[sym]['trades'] += 1
            total_pnl += pnl
        
        winners = sum(1 for s, d in by_symbol.items() if d['pnl'] > 0)
        losers = sum(1 for s, d in by_symbol.items() if d['pnl'] < 0)
        
        return {
            'total_pnl': total_pnl,
            'by_symbol': by_symbol,
            'winners': winners,
            'losers': losers,
            'win_rate': winners / max(winners + losers, 1) * 100
        }
    except Exception as e:
        return {'error': str(e)}

def generate_report(log_analysis, trade_analysis):
    """Generate evaluation report."""
    report = []
    report.append("📊 NEKO DAILY EVALUATION")
    report.append(f"📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    
    # Trade performance
    if 'error' not in trade_analysis:
        report.append("💰 TRADE PERFORMANCE (24h)")
        report.append(f"  Total PnL: {trade_analysis['total_pnl']:+.2f} USDT")
        report.append(f"  Win Rate: {trade_analysis['win_rate']:.0f}% ({trade_analysis['winners']}W / {trade_analysis['losers']}L)")
        report.append("")
        
        if trade_analysis['by_symbol']:
            report.append("  By Symbol:")
            for sym, data in sorted(trade_analysis['by_symbol'].items(), key=lambda x: x[1]['pnl']):
                emoji = "🟢" if data['pnl'] > 0 else "🔴"
                report.append(f"    {emoji} {sym}: {data['pnl']:+.2f} ({data['trades']} trades)")
            report.append("")
    
    # Signal analysis
    report.append("📡 SIGNAL ANALYSIS (24h)")
    report.append(f"  Signals Generated: {len(log_analysis['signals'])}")
    report.append(f"  Orders Placed: {log_analysis['orders_placed']}")
    report.append(f"  Order Failures: {sum(log_analysis['order_failures'].values())}")
    report.append("")
    
    # Top rejection reasons
    if log_analysis['rejections']:
        report.append("🚫 TOP REJECTION REASONS:")
        for reason, count in log_analysis['rejections'].most_common(8):
            report.append(f"  • {reason}: {count:,}")
        report.append("")
    
    # Order failures
    if log_analysis['order_failures']:
        report.append("⚠️ ORDER FAILURES:")
        for reason, count in log_analysis['order_failures'].most_common(5):
            report.append(f"  • {reason}: {count}")
        report.append("")
    
    # Filter recommendations
    report.append("🔧 RECOMMENDATIONS:")
    total_rejections = sum(log_analysis['rejections'].values())
    
    if log_analysis['rejections'].get('volume too low', 0) > total_rejections * 0.1:
        report.append("  ⚠️ Volume filter rejecting >10% — consider lowering to 0.8x")
    
    if log_analysis['rejections'].get('chase filter', 0) > total_rejections * 0.05:
        report.append("  ⚠️ Chase filter active — market moving, good")
    
    if log_analysis['orders_placed'] == 0:
        report.append("  🚨 NO ORDERS in 24h — market dry or filters too strict")
    
    if trade_analysis.get('win_rate', 0) < 40:
        report.append("  🚨 Win rate < 40% — tighten entry filters")
    elif trade_analysis.get('win_rate', 0) > 60:
        report.append("  ✅ Win rate > 60% — filters working well")
    
    if trade_analysis.get('total_pnl', 0) < -50:
        report.append("  🚨 Big loss — check chase limits and volume filter")
    
    return "\n".join(report)

def main():
    print("Loading logs...")
    lines = load_recent_logs(24)
    
    print("Analyzing signals...")
    log_analysis = analyze_signals(lines)
    
    print("Analyzing trades...")
    trade_analysis = analyze_trades()
    
    print("Generating report...")
    report = generate_report(log_analysis, trade_analysis)
    
    print(report)
    
    # Save report
    report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, f'daily_eval_{datetime.utcnow().strftime("%Y%m%d")}.txt')
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")
    
    return report

if __name__ == '__main__':
    main()
