---
name: neko-futures-trader
description: |
  Automated Binance Futures trading scanner with runner detection.
  Features:
  - Runner detection (volume spike + momentum + breakout)
  - Real crypto news via Brave Search
  - Auto SL/TP after position opens
  - Score-based signal ranking (0-10)
  - Post signals + execute trades to Telegram
  Use when user wants automated futures trading signals.
metadata:
  openclaw:
    emoji: 🐱📈
    requires:
      bins: ["python3"]
      env: ["BINANCE_API_KEY", "BINANCE_SECRET", "TELEGRAM_BOT_TOKEN"]
---

# Neko Futures Trader 🐱📈

Binance Futures automated scanner with runner detection and real news.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/lukmanc405/neko-futures-trader.git
cd neko-futures-trader

# Create .env file
cp .env.example .env
nano .env
```

Edit `.env`:
```
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHANNEL=your_channel_id
```

## Run with OpenClaw

```bash
# Activate skill
openclaw skill activate neko-futures-trader

# Or run directly
source .env
python3 scanner-v8.py
```

## Runner Detection Criteria

| Criteria | Weight |
|----------|--------|
| Volume Spike 3x+ | +2 pts |
| Volume Spike 2x+ | +1 pt |
| 24h Change 10%+ | +2 pts |
| 24h Change 5%+ | +1 pt |
| 1H Momentum 3%+ | +1 pt |
| Breakout (new high) | +2 pts |

**Minimum Score: 3/10** to trigger signal

## Configuration

Edit `scanner-v8.py`:
```python
LEVERAGE = 10
MAX_POSITIONS = 8
ENTRY_PERCENT = 5
MIN_GAIN = 0.5
```

## Signal Template

```
🟢 LONG SIGNAL 🟢

📈 XANUSDT TECHNICAL ANALYSIS 📊

📐 MULTI-TF CONFIRMATION:
• Trend 1H: BULLISH
• Structure: BREAKOUT
📊 24h Change: +47.0%

📐 INDICATORS:
• RSI (14): 72.5
• EMA 21: 0.007842
• ATR: 0.000892

🔊 VOLUME: Volume Spike (12.8x)

🎯 RUNNER METRICS:
• 1H Momentum: +24.5%
• Volume Spike: 12.8x
• Breakout: ✅ Yes
• Score: 7/10 🚀

💡 INSIGHT: BREAKOUT | Strong momentum
🎯 Entry: $0.008950
📈 TP: $0.011600
🛡 SL: $0.007800

📰 XANA Price Up 45% Today | Token Surges

✅ ORDER EXECUTED: LONG
```

## Features

| Feature | Description |
|---------|-------------|
| Runner Detection | Volume + momentum + breakout |
| Real News | Brave Search integration |
| Auto SL/TP | After position opens |
| Score System | Rank signals by strength |

## Files

- `scanner-v8.py` — Main scanner
- `position-monitor.py` — Position watcher
- `README.md` — Full documentation

## Safety

⚠️ Monitor positions regularly. Understand risks of leveraged trading.

---
*Skill by Neko Sentinel* 🐱🛡️
