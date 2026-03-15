# Neko Futures Trader 🐱📈

Automated Binance Futures trading bot with runner detection and real-time news.

## What's New (v8)

- 🚀 **Runner Scanner** - Detect momentum explosions (volume spike + breakout)
- 📰 **Real News** - Brave Search integration for live crypto news
- 🛡 **Auto SL/TP** - Automatic stop loss and take profit after entry
- 📊 **Volume Analysis** - 5x+ volume spike detection
- 🔥 **Score System** - Rank signals by strength (0-10)

---

## Features

### Runner Detection
| Criteria | Weight |
|----------|--------|
| Volume Spike 3x+ | +2 pts |
| Volume Spike 2x+ | +1 pt |
| 24h Change 10%+ | +2 pts |
| 24h Change 5%+ | +1 pt |
| 1H Momentum 3%+ | +1 pt |
| Breakout (new high) | +2 pts |

**Minimum Score: 3/10** to trigger signal

### Technical Indicators
| Category | Indicators |
|----------|------------|
| Trend | EMA 21/50 |
| Momentum | RSI (14) |
| Volatility | ATR |
| Volume | Volume Spike Ratio |

### Risk Management
- Auto Stop Loss (1.5x ATR)
- Auto Take Profit (3x ATR)
- Max 8 Positions
- 5% Entry per trade
- 10x Leverage

---

## Installation

### Prerequisites
```bash
- Python 3.8+
- Binance Futures Account
- Telegram Bot
```

### Step 1: Clone
```bash
git clone https://github.com/lukmanc405/neko-futures-trader.git
cd neko-futures-trader
```

### Step 2: Install
```bash
pip install requests hmac hashlib
```

### Step 3: Configure
```bash
cp .env.example .env
nano .env
```

```env
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHANNEL=your_channel_id
```

### Step 4: Run
```bash
source .env
python3 scanner-v8.py
```

**Background:**
```bash
nohup python3 scanner-v8.py > scanner.log 2>&1 &
```

---

## Configuration

```python
# scanner-v8.py
LEVERAGE = 10
MAX_POSITIONS = 8
ENTRY_PERCENT = 5
MIN_GAIN = 0.5  # Minimum 24h change %
```

---

## Signal Template

```
🟢 LONG SIGNAL 🟢

📈 XANUSDT TECHNICAL ANALYSIS 📊
📊 Chart: https://www.tradingview.com/chart/?symbol=BINANCE:XANUSDT

📐 MULTI-TF CONFIRMATION:
• Trend 1H: BULLISH
• Structure: BREAKOUT
📊 24h Change: +47.0%

📐 INDICATORS:
• RSI (14): 72.5
• EMA 21: 0.007842
• EMA 50: 0.006521
• ATR: 0.000892

🔊 VOLUME: Volume Spike (12.8x)

📊 STRUCTURE:
• Support: 0.006200
• Resistance: 0.009500

🎯 RUNNER METRICS:
• 1H Momentum: +24.5%
• Volume Spike: 12.8x
• Breakout: ✅ Yes
• Score: 7/10 🚀

💡 INSIGHT: BREAKOUT | Strong momentum | Volume explosion
🎯 Entry: $0.008950
📈 TP1: $0.011600
📈 TP2: $0.013000
🛡 SL: $0.007800

📰 XANA (XAN) Price Up 45% Today | Token Surges

✅ ORDER EXECUTED: LONG
🛡 SL: $0.007800
📈 TP: $0.011600
📋 Order ID: 123456789 | Status: NEW
```

---

## Auto SL/TP

Scanner automatically sets:
- **Stop Loss**: 1.5x ATR below entry
- **Take Profit**: 3x ATR above entry

Note: Binance API requires manual SL/TP setup for some accounts.

---

## Files

| File | Description |
|------|-------------|
| `scanner-v8.py` | Main scanner (v8) |
| `position-monitor.py` | Position monitor |
| `README.md` | This file |
| `SKILL.md` | OpenClaw skill |
| `.env.example` | Template |

---

## Safety

⚠️ **Important:**

1. Start with small balance to test
2. Never commit `.env` to GitHub
3. Monitor positions regularly
4. Understand leveraged trading risks

---

## Support

- GitHub: https://github.com/lukmanc405/neko-futures-trader

---

*Built by Neko Sentinel 🐱🛡️*
