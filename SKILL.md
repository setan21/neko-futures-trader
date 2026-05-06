---
name: neko-futures-trader
description: Automated Binance Futures trading bot with scanning, SL/TP automation, and backtesting. Use when user mentions futures trading, crypto trading bot, Binance automated trading, or needs help with trading system setup/maintenance.
---

# 🐱 Neko Futures Trader

## Overview

Automated Binance Futures trading bot with advanced signal detection, risk management, and comprehensive backtesting capabilities.

**Emoji:** 🐱📈  
**Requires:** Python 3.8+, Binance Futures API, systemd

---

## When to Use

Trigger when user mentions:
- "futures trading" or "crypto bot"
- "Binance automated trading"
- "trading scanner" or "SL/TP automation"
- "backtesting" or "strategy validation"
- Dashboard setup/maintenance
- Signal indicator questions

---

## 📁 File Structure

```
neko-futures-trader/
├── scanner.py                 # Main scanner (5min intervals)
├── price-monitor.py           # SL/TP monitor (1sec intervals)
├── position_command.py        # Position checker
├── position-monitor.py        # Position monitor helper
├── dashboard_api.py           # Dashboard API server
├── config.py                  # Trading parameters
├── llm_analyzer.py            # LLM analyzer (disabled by default, 3-tier fallback)
├── lib/                       # Helper modules
│   ├── signal_filter.py
│   ├── ict_indicators.py
│   ├── advanced_analysis.py
│   ├── delisting_monitor.py
│   └── error_handling.py
├── scripts/
│   ├── dashboard_api.py       # API server
│   ├── backtester.py          # Backtesting engine
│   ├── analyze_trades.py      # Trade analysis
│   └── check_balance.py       # Balance checker
├── static/
│   └── neko-light.html        # Dashboard UI
├── .gitignore
├── SKILL.md
└── README.md
```

---

## 🚀 Setup

### 1. Install
```bash
git clone https://github.com/lukmanc405/neko-futures-trader.git \
  /root/.openclaw/skills/neko-futures-trader
cd /root/.openclaw/skills/neko-futures-trader
```

### 2. Dependencies
```bash
pip install python-dotenv requests pandas numpy scipy scikit-learn
```

### 3. Configure (.env)
```bash
BINANCE_API_KEY=***
BINANCE_SECRET=***
TELEGRAM_BOT_TOKEN=***
TELEGRAM_CHANNEL=your_user_id
```

> ⚠️ **Important:** Env var is `BINANCE_SECRET` (NOT `BINANCE_API_SECRET`)

### 4. Workspace Setup
```bash
mkdir -p /root/.openclaw/workspace/neko-futures-trader/{logs,data}
cp .env /root/.openclaw/workspace/neko-futures-trader/
```

---

## ⚙️ Systemd Services

### Scanner Service
```ini
[Unit]
Description=Neko Futures Scanner
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/neko-futures-trader
ExecStart=/usr/bin/python3 /root/.openclaw/skills/neko-futures-trader/scanner.py
Restart=always
RestartSec=10
StandardOutput=append:/root/.openclaw/workspace/neko-futures-trader/logs/scanner.log
StandardError=append:/root/.openclaw/workspace/neko-futures-trader/logs/scanner.log

[Install]
WantedBy=multi-user.target
```

### Monitor Service
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

### Enable Services
```bash
systemctl daemon-reload
systemctl enable neko-scanner neko-monitor neko-dashboard
systemctl start neko-scanner neko-monitor neko-dashboard
```

---

## 📊 Commands

```bash
# Check positions
python3 position_command.py

# Daily evaluation
python3 daily_eval.py

# Backtesting (Monte Carlo)
python3 backtester.py

# Emergency close
python3 emergency_close.py

# Service management
systemctl status neko-scanner neko-monitor
systemctl restart neko-scanner
journalctl -u neko-scanner -f
```

---

## 🌐 Dashboard

Access at: `https://YOUR_IP:8443/neko-light.html`

### Features
- Real-time positions, balance, PnL
- Win rate & closed PnL (7-day history)
- Glassmorphism UI with particles
- Dark/Light theme toggle
- Sparkline charts
- Toast notifications
- Responsive design

---

## 📈 Indicators

### Active Indicators

| Indicator | Score | Description |
|-----------|-------|-------------|
| Volume Spike | +2 | >3x average volume |
| Price Change | +2 | >3% price change |
| OI Change | +2 | >20% open interest change |
| Weekly Change | +1 to +2 | >5% or >20% weekly change |
| EMA Position | Filter | Price must be near/below 21EMA |

### Filters (Reject Signals)

| Filter | Condition | Action |
|--------|-----------|--------|
| RSI | LONG when RSI > 70 | Reject LONG (overbought) |
| RSI | LONG when RSI < 30 | Reject LONG (oversold) |
| RSI | SHORT when RSI < 30 | Reject SHORT (oversold) |
| MACD Histogram | Contradicts direction | Reject |
| Bollinger Squeeze | No squeeze + weak move | Reject (chop) |
| EMA Extended | Price too extended | Reject (chase) |
| Anti-Chase | Recent entry within 24h | Skip re-entry |

### Removed (Poor Accuracy)

- ❌ Breakout/Breakdown
- ❌ Pocket Pivot
- ❌ Batch orders (using MARKET + separate SL/TP instead)

---

## 🧠 LLM Analyzer (Hybrid AI Gate)

The scanner has an optional LLM second opinion layer. **Currently DISABLED** — LLM was rejecting 98.5% of valid signals.

### Status: DISABLED
```python
LLM_ENABLED = False  # Set True in config.py to re-enable
```

### How it Works (when enabled)
```
Scanner (rule-based, 14 indicators) → Score ≥ 6
        ↓
  LLM Analyzer (3-tier fallback)
        ↓
  [YES] → Execute order with SL/TP
  [NO]  → Skip signal
```

### 3-Tier Fallback Chain
```
1. Nous Primary (xiaomi/mimo-v2-pro)
   → https://inference-api.nousresearch.com/v1/chat/completions
   ↓ (on failure)
2. OpenRouter (hermes-4-70b)
   → https://openrouter.ai/api/v1/chat/completions
   ↓ (on failure)
3. MiniMax (MiniMax-M2.5)
   → https://api.minimaxi.chat/v1/chat/completions
```

### Config (`config.py`)
```python
LLM_ENABLED = False                    # Disabled — too many false rejections
LLM_MODEL = "xiaomi/mimo-v2-pro"       # Nous primary
LLM_MIN_SCORE = 4                      # Only analyze score ≥ 4
LLM_TEMPERATURE = 0.1                  # Low = deterministic
LLM_BASE_URL = "https://inference-api.nousresearch.com/v1/chat/completions"
LLM_TIMEOUT = 15                       # Seconds, then fail-open

# Fallback 1: OpenRouter
LLM_FALLBACK1_ENABLED = True
LLM_FALLBACK1_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_FALLBACK1_MODEL = "nousresearch/hermes-4-70b"

# Fallback 2: MiniMax
LLM_FALLBACK2_ENABLED = True
LLM_FALLBACK2_BASE_URL = "https://api.minimaxi.chat/v1/chat/completions"
LLM_FALLBACK2_MODEL = "MiniMax-M2.5"
```

### Key Design Decisions
- **Fail-open**: If LLM is down/timeout/error → trade still executes. No missed trades.
- **Cache**: 5-min TTL per symbol+direction+score. Repeated signals don't re-call LLM.
- **Prompt**: Asks about momentum alignment, RSI zone (30-65 acceptable for LONG), SL reasonableness, red flags.
- **Telegram**: LLM reasoning included in trade notifications.

### `llm_analyzer.py` Functions
- `analyze_signal(analysis)` — Main entry. Returns `{approved, reason, confidence, model, latency_ms}`
- `format_analysis_prompt(analysis)` — Builds concise prompt from indicator dict
- `call_llm(prompt, model, timeout)` — Multi-provider API call with fallback chain
- `parse_llm_response(content)` — JSON parser with markdown fallback

---

## ⚙️ Trading Parameters

| Param | Default | Description |
|-------|---------|-------------|
| MAX_POSITIONS | 8 | Max open positions (NORMAL mode) |
| MAX_POSITIONS_SLEEP | 4 | Max positions in SLEEP mode |
| MAX_MARGIN_PERCENT | 40% | Max margin usage |
| MAX_RISK_PERCENT | 1.5% | Max risk per trade |
| LEVERAGE | 10x | Leverage |
| MIN_SCORE_NORMAL | 6 | Signal threshold (NORMAL mode) |
| MIN_SCORE_SLEEP | 7 | Signal threshold (SLEEP mode) |
| MIN_PRICE_CHANGE | 3.0% | Min price change for signal |
| SCAN_INTERVAL | 300s | Scanner interval (5 min) |

### R:R Ratio 1:3

| Parameter | Value |
|-----------|-------|
| SL | 5% (fixed) |
| TP | 15% (fixed) |
| Ratio | 1:3 |

---

## 🐛 Bug Fixes Applied

1. **Algo API:** `/fapi/v1/algoOrder` endpoint
2. **Params:** `algoType=CONDITIONAL`, `quantity=1`, `reduceOnly=true`
3. **Precision:** Rounds to tickSize per symbol
4. **Floating point:** String formatting for SL/TP prices
5. **Income API:** Use `/fapi/v1/income` for accurate winrate
6. **Anti-chase:** 24h cooldown prevents re-entry on same symbol
7. **Order type:** MARKET orders + separate SL/TP (batch orders removed)

---

## 📝 Changelog

### 2026-05-06
- **BREAKING:** LLM analyzer disabled — was rejecting 98.5% of valid signals
- RSI acceptance range widened for LONG: 30-65 (was 30-60)
- `MIN_PRICE_CHANGE` raised from 2.0% to 3.0% (filter noise)
- Removed unused functions: `batch_orders`, `place_order_with_sl_tp`
- Switched to MARKET orders + separate SL/TP (no batch)
- Untracked `.positions_sl_tp.json` from git

---

## metadata

```yaml
metadata:
  openclaw:
    emoji: 🐱📈
    requires:
      bins: [python3, systemctl]
      env:
        - BINANCE_API_KEY
        - BINANCE_SECRET
        - TELEGRAM_BOT_TOKEN
        - TELEGRAM_CHANNEL
    startup:
      command: systemctl start neko-scanner neko-monitor neko-dashboard
      type: service
    repo: https://github.com/lukmanc405/neko-futures-trader
```
