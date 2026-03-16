---
name: neko-futures-trader
description: |
  Automated Binance Futures trading scanner with runner detection.
  Features:
  - Runner detection (volume spike + momentum + breakout)
  - Real crypto news via Brave Search
  - Fibonacci+ATR based SL/TP
  - Price monitor (auto-close when SL/TP hit)
  - Emoji-heavy Telegram alerts
  - Score-based signal ranking (0-10)
  - Post signals + execute trades to Telegram
  - Auto-start on install
  Use when user wants automated futures trading signals.
metadata:
  openclaw:
    emoji: 🐱📈
    requires:
      bins: ["python3"]
      env: ["BINANCE_API_KEY", "BINANCE_SECRET", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL", "BRAVE_API_KEY"]
    startup:
      command: "cd /root/.openclaw/workspace && nohup bash -c 'while true; do source binance-futures/.env && python3 scanner-v8.py; echo \"---\"; sleep 300; done' > scanner.log 2>&1 &"
      type: "background"
---

# Neko Futures Trader 🐱📈

Binance Futures automated scanner with price monitor.

## Scripts

| Script | Description |
|--------|-------------|
| `scanner-v8.py` | Main scanner - finds runner signals |
| `price-monitor.py` | Auto-close when SL/TP hit |

## Quick Start

```bash
# Install dependencies
pip install requests hmac hashlib

# Setup .env (see below)

# Run scanner (every 5 min)
cd /root/.openclaw/workspace
nohup python3 scanner-v8.py &

# Run price monitor (every 60s)
nohup python3 price-monitor.py &
```

## Environment Setup

Create `.env` file:
```
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL=your_channel_id
BRAVE_API_KEY=your_brave_key
```

## Fibonacci+ATR SL/TP

| Level | Calculation |
|-------|-------------|
| SL | Entry - 1.5×ATR |
| TP1 | Entry + 3×ATR (Fib 1.272) |
| TP2 | Entry + 4.5×ATR (Fib 1.618) |

## Emoji Alerts

### Scanner Signal
```
🟢 LONG SIGNAL 🟢

📈 XANUSDT TECHNICAL ANALYSIS 📊
...

📰 Latest News: ...

✅ ORDER EXECUTED: LONG
🛡 SL: $0.007800
📈 TP: $0.011600
📋 Order ID: ...
```

### Price Monitor Alert (TP)
```
🎉💰 PROFIT TAKEN! 💰🎉

🟢 TIAUSDT LONG
📈 +5.02% ($5.02)
Entry: $0.364600 → Exit: $0.382940
Target: $0.390323 (TP1) 🎯

#TakeProfit #Winning #Crypto
```

### Price Monitor Alert (SL)
```
❌ STOP HIT

🔴 AXSUSDT LONG
📈 -3.12% (-$3.50)
Entry: $1.237000 → Exit: $1.199000
Target: $1.199890 (SL) 🎯

#StopLoss #Trading #Crypto
```

## Configuration

```python
# scanner-v8.py
LEVERAGE = 10
MAX_POSITIONS = 8
ENTRY_PERCENT = 5
MIN_GAIN = 0.5

# price-monitor.py
CHECK_INTERVAL = 60  # seconds
```

## Files

- `scanner-v8.py` - Main scanner
- `price-monitor.py` - Price monitor (auto-close)
- `README.md` - Full docs

## Safety

⚠️ Monitor positions. Understand leveraged trading risks.

---
*Skill by Neko Sentinel* 🐱🛡️
