# Neko Futures Trader 🐱📈

Automated Binance Futures trading bot with runner detection and price monitor.

## What's New (v8)

- 🚀 **Runner Scanner** - Detect momentum explosions
- 📰 **Real News** - Brave Search integration
- 🛡 **Fibonacci+ATR SL/TP** - Professional risk management
- 🔔 **Price Monitor** - Auto-close when SL/TP hit
- 🎉 **Emoji Alerts** - Profit/Loss notifications

---

## Scripts

| Script | Description | Interval |
|--------|-------------|----------|
| `scanner-v8.py` | Find runner signals | 5 min |
| `price-monitor.py` | Auto-close positions | 60 sec |

## Fibonacci+ATR SL/TP

| Level | Formula |
|-------|---------|
| **SL** | Entry - 1.5×ATR |
| **TP1** | Entry + 3×ATR (Fib 1.272) |
| **TP2** | Entry + 4.5×ATR (Fib 1.618) |

## Installation

```bash
git clone https://github.com/lukmanc405/neko-futures-trader.git
cd neko-futures-trader

# Setup .env
cp .env.example .env
nano .env
```

Run:
```bash
nohup python3 scanner-v8.py &
nohup python3 price-monitor.py &
```

## Alert Examples

### Signal (Scanner)
```
🟢 LONG SIGNAL 🟢

📈 XANUSDT TECHNICAL ANALYSIS 📊

📐 24h Change: +47.0%

🎯 RUNNER METRICS:
• 1H Momentum: +24.5%
• Score: 7/10 🚀

✅ ORDER EXECUTED: LONG
```

### Profit Alert (Price Monitor)
```
🎉💰 PROFIT TAKED! 💰🎉

🟢 TIAUSDT LONG
📈 +5.02% ($5.02)
Entry: $0.364600 → Exit: $0.382940
Target: $0.390323 (TP1) 🎯

#TakeProfit #Winning #Crypto
```

### Stop Loss Alert
```
❌ STOP HIT

🔴 AXSUSDT LONG
📈 -3.12% (-$3.50)
Entry: $1.237000 → Exit: $1.199000
Target: $1.199890 (SL) 🎯

#StopLoss #Trading #Crypto
```

## Files

| File | Description |
|------|-------------|
| `scanner-v8.py` | Main scanner |
| `price-monitor.py` | Price monitor |
| `SKILL.md` | OpenClaw skill |
| `README.md` | This file |

## Safety

⚠️ Trading futures involves risk. Monitor positions.

---
*Built by Neko Sentinel* 🐱🛡️
