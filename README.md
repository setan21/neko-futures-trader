# 🐱 Neko Futures Trader

Automated Binance Futures Trading Bot with advanced signal detection and risk management.

## 📁 Structure

```
neko-futures-trader/
├── scanner-v8.py           # Main scanner (5min intervals)
├── price-monitor.py        # SL/TP monitor (1sec intervals)
├── position_command.py     # Check positions
├── dashboard_api.py        # Dashboard API server
├── emergency_close.py      # Emergency position closer
├── daily_eval.py           # Comprehensive daily evaluation
├── config.py               # Trading parameters
├── lib/                    # Helper modules
│   ├── signal_filter.py
│   ├── ict_indicators.py
│   ├── advanced_analysis.py
│   ├── delisting_monitor.py
│   └── error_handling.py
├── static/
│   └── neko-light.html    # Dashboard UI
├── README.md
└── SKILL.md
```

## 🚀 Quick Start

```bash
# Install dependencies
pip install python-dotenv requests pandas numpy scipy scikit-learn

# Setup .env
cp .env.example .env
nano .env

# Start services
systemctl enable neko-scanner neko-monitor neko-dashboard
systemctl start neko-scanner neko-monitor neko-dashboard
```

## ⚙️ Config (.env)

```bash
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHANNEL=your_user_id
```

## 📊 Commands

```bash
# Check positions
python3 position_command.py

# Daily evaluation (comprehensive)
python3 daily_eval.py

# Emergency close all
python3 emergency_close.py

# View logs
tail -f logs/scanner.log
tail -f logs/pm.log
```

## 🌐 Dashboard

`https://YOUR_IP:8443/neko-light.html`

## 📈 Indicators (Signal Scoring)

### Active Indicators

| Indicator | Score | Description |
|-----------|-------|-------------|
| Volume Spike | +2 | >3x average volume |
| Price Change | +1 to +2 | >5% or >10% change |
| OI Change | +2 | >20% open interest change |
| Weekly Change | +1 to +2 | >5% or >20% weekly change |
| EMA Position | Filter | Price must be near/below 21EMA |

### Filters (Reject Signals)

| Filter | Condition | Action |
|--------|-----------|--------|
| RSI LONG | RSI > 70 | Reject LONG |
| RSI SHORT | RSI < 30 | Reject SHORT |
| MACD Histogram | Contradicts direction | Reject signal |
| Bollinger Squeeze | No squeeze + weak move | Reject (chop) |
| EMA Extended | Price too extended | Reject (chase) |

### Removed (Poor Accuracy)

- ❌ Breakout/Breakdown
- ❌ Pocket Pivot

---

## 📊 ATR-Based SL/TP System

**ATR = Average True Range** - measures market volatility.

### R:R Ratio 1:3 (Optimized)

| Volatility | ATR Range | SL | TP | Ratio |
|------------|-----------|-----|-----|-------|
| HIGH | > 10% | 2x ATR | 6x ATR | 1:3 |
| NORMAL | 5-10% | 2x ATR | 6x ATR | 1:3 |
| LOW | < 5% | 1.5x ATR | 4.5x ATR | 1:3 |

### Example

```
Entry: $100
ATR: $2 (2%)

HIGH VOL:
  SL = $100 - (2 × $2) = $96
  TP = $100 + (6 × $2) = $112
  Risk: $4 | Reward: $12 = 1:3 ratio ✅

LOW VOL:
  SL = $100 - (1.5 × $2) = $97
  TP = $100 + (4.5 × $2) = $109
  Risk: $3 | Reward: $9 = 1:3 ratio ✅
```

### Why 1:3 R:R?

With 42.9% winrate, you need R:R > 1:1.07 to break even.
1:3 ratio ensures profitability even with 40% winrate.

---

## ⚙️ Parameters

| Param | Default | Description |
|-------|---------|-------------|
| MAX_POSITIONS | 5 | Max open positions |
| MAX_MARGIN | 30% | Max margin usage |
| LEVERAGE | 10x | Leverage multiplier |
| MIN_SCORE | 3 | Min signal score |

---

## 🐛 Bug Fixes Applied

- ✅ Algo order endpoint: `/fapi/v1/algoOrder`
- ✅ tickSize price rounding (no precision errors)
- ✅ `quantity=1` + `reduceOnly=true` (works reliably)
- ✅ Floating point precision in SL/TP

---

## 📊 Daily Evaluation Metrics

The bot sends comprehensive daily reports including:

- Balance & Open PnL
- Win Rate, R:R, Expectancy
- Per-symbol performance
- Blacklist suggestions (worst performers)
- Trade recommendations

---

## 🔧 Maintenance

```bash
# Restart services
systemctl restart neko-scanner neko-monitor neko-dashboard

# Check status
systemctl status neko-scanner neko-monitor neko-dashboard

# Logs
journalctl -u neko-scanner -f
```
