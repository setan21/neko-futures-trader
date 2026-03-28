# SKILL.md - Neko Futures Trader

## Overview
Automated Binance Futures trading bot with advanced signal detection and risk management.

**Emoji:** 🐱📈
**Requires:** Python 3.8+, Binance Futures API

---

## 📁 File Structure

```
neko-futures-trader/
├── scanner-v8.py           # Scanner (5min intervals)
├── price-monitor.py        # SL/TP monitor (1sec)
├── position_command.py     # Position checker
├── dashboard_api.py        # Dashboard API
├── emergency_close.py     # Emergency closer
├── daily_eval.py           # Comprehensive daily evaluation
├── config.py              # Trading parameters
├── lib/                   # Helper modules
│   ├── signal_filter.py
│   ├── ict_indicators.py
│   ├── advanced_analysis.py
│   ├── delisting_monitor.py
│   └── error_handling.py
└── static/
    └── neko-light.html    # Dashboard UI
```

---

## 🚀 Setup

### 1. Install
```bash
git clone https://github.com/lukmanc405/neko-futures-trader.git /root/.openclaw/skills/neko-futures-trader
cd /root/.openclaw/skills/neko-futures-trader
```

### 2. Dependencies
```bash
pip install python-dotenv requests pandas numpy scipy scikit-learn
```

### 3. Configure (.env)
```bash
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHANNEL=your_user_id
```

### 4. Setup Workspace
```bash
mkdir -p /root/.openclaw/workspace/neko-futures-trader/{logs,data}
cp .env /root/.openclaw/workspace/neko-futures-trader/
```

---

## ⚙️ Systemd Services

### Scanner
```ini
[Unit]
Description=Neko Futures Scanner
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/neko-futures-trader
ExecStart=/usr/bin/python3 /root/.openclaw/skills/neko-futures-trader/scanner-v8.py
Restart=always
RestartSec=10
StandardOutput=append:/root/.openclaw/workspace/neko-futures-trader/logs/scanner.log
StandardError=append:/root/.openclaw/workspace/neko-futures-trader/logs/scanner.log

[Install]
WantedBy=multi-user.target
```

### Monitor
```ini
[Unit]
Description=Neko Futures Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/neko-futures-trader
ExecStart=/usr/bin/python3 /root/.openclaw/skills/neko-futures-trader/price-monitor.py
Restart=always
RestartSec=10
StandardOutput=append:/root/.openclaw/workspace/neko-futures-trader/logs/pm.log
StandardError=append:/root/.openclaw/workspace/neko-futures-trader/logs/pm.log

[Install]
WantedBy=multi-user.target
```

### Enable
```bash
systemctl daemon-reload
systemctl enable neko-scanner neko-monitor
systemctl start neko-scanner neko-monitor
```

---

## 🌐 Dashboard

### Setup
```bash
# Copy HTML
cp static/neko-light.html /var/www/html/

# Nginx (port 8443 SSL)
# See nginx config in repository

# Start service
systemctl start neko-dashboard
```

### Access
`https://YOUR_IP:8443/neko-light.html`

---

## 📊 Commands

```bash
# Check positions
python3 position_command.py

# Daily evaluation (comprehensive)
python3 daily_eval.py

# Emergency close
python3 emergency_close.py

# Service management
systemctl status neko-scanner neko-monitor
systemctl restart neko-scanner
journalctl -u neko-scanner -f
```

---

## 📈 Indicators (Signal Scoring)

### Active Indicators

| Indicator | Score | Description |
|-----------|-------|-------------|
| Volume Spike | +2 | >3x average volume |
| Price Change | +1 to +2 | >5% or >10% change |
| OI Change | +2 | >20% open interest change |
| Weekly Change | +1 to +2 | >5% or >20% weekly change |

### Filters (Reject Signals)

| Filter | Condition | Action |
|--------|-----------|--------|
| RSI | LONG when RSI > 70 | Reject |
| RSI | SHORT when RSI < 30 | Reject |
| MACD Histogram | Contradicts direction | Reject |
| Bollinger Squeeze | No squeeze + weak move | Reject (chop) |
| EMA Position | Price too extended | Reject (chase) |

### Removed (Poor Accuracy)

- ❌ Breakout/Breakdown
- ❌ Pocket Pivot

---

## ⚙️ Trading Parameters

| Param | Default | Description |
|-------|---------|-------------|
| MAX_POSITIONS | 5 | Max open positions |
| MAX_MARGIN | 30% | Max margin usage |
| LEVERAGE | 10x | Leverage |
| MIN_SCORE | 3 | Signal threshold |

### R:R Ratio 1:3 (Optimized)

With 42.9% winrate, you need R:R > 1:1.07 to break even.
1:3 ratio ensures profitability even with 40% winrate.

| Volatility | ATR Range | SL | TP | Ratio |
|------------|-----------|-----|-----|-------|
| HIGH | > 10% | 2x ATR | 6x ATR | 1:3 |
| NORMAL | 5-10% | 2x ATR | 6x ATR | 1:3 |
| LOW | < 5% | 1.5x ATR | 4.5x ATR | 1:3 |

---

## 🐛 Bug Fixes

1. **Algo API:** `/fapi/v1/algoOrder` (not `/orderAlg`)
2. **Params:** `algoType=CONDITIONAL`, `quantity=1`, `reduceOnly=true`
3. **Precision:** Rounds to tickSize per symbol
4. **Floating point:** String formatting for SL/TP prices

---

## metadata

```yaml
metadata:
  openclaw:
    emoji: 🐱📈
    requires:
      bins: [python3]
      env: [BINANCE_API_KEY, BINANCE_SECRET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL]
    startup:
      command: "systemctl start neko-scanner neko-monitor"
      type: service
```
