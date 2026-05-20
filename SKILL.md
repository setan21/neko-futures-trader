---
name: neko-futures-trader
description: Automated Binance Futures trading bot with multi-timeframe scanner, LLM signal gate, dynamic coin universe, partial TP / trailing SL, BTC regime check, and bear-market SHORT logic. Use when user mentions futures trading, crypto trading bot, Binance automated trading, or needs help with trading system setup/maintenance.
---

# 🐱 Neko Futures Trader

## Overview

Automated Binance Futures trading bot with rule-based scanner, LLM signal-quality
gate, multi-timeframe analysis, partial TP, trailing SL, BTC regime check, and
bear-market SHORT logic. Runs on systemd. Reaches the user via Telegram for
trade entries, exits, and daily evaluation reports.

**Emoji:** 🐱📈
**Requires:** Python 3.10+, Binance Futures API, systemd
**Repo:** https://github.com/lukmanc405/neko-futures-trader

---

## When to Use

Trigger when the user mentions:
- "futures trading" or "crypto bot"
- "Binance automated trading"
- "trading scanner" or "SL/TP automation"
- "backtesting" or "strategy validation"
- Dashboard setup/maintenance
- Signal indicator questions
- Win rate diagnosis or filter tuning

---

## 📁 Project Layout (actual paths)

```
/root/workspace/neko-futures-trader/
├── scanner.py                 # Main scanner (60s cycle)
├── price-monitor.py           # SL/TP monitor (15s default, 5s adaptive)
├── dashboard_api.py           # Dashboard API server (port 8080)
├── config.py                  # Trading parameters
├── llm_analyzer.py            # 3-tier LLM fallback (Nous → OR → MiniMax)
├── lib/                       # Helper modules
│   ├── signal_filter.py
│   ├── ict_indicators.py
│   ├── advanced_analysis.py
│   ├── delisting_monitor.py
│   └── error_handling.py
├── scripts/
│   ├── analyze_trades.py      # PnL aggregation by symbol
│   ├── daily_eval.py          # Daily performance evaluator
│   ├── check_balance.py       # Wallet + position summary
│   └── backtester.py          # Monte Carlo backtest
├── static/
│   └── neko-light.html        # Dashboard UI
├── .gitignore
├── README.md
├── AI_CONTRIBUTORS.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── SKILL.md
```

> ⚠️ **Path note:** Use `/root/workspace/neko-futures-trader/` everywhere.
> The legacy `/root/.openclaw/workspace/` symlink may exist for the dashboard
> static files only — services should point to `/root/workspace/`.

---

## 🚀 Setup

### 1. Clone
```bash
git clone https://github.com/lukmanc405/neko-futures-trader.git \
  /root/workspace/neko-futures-trader
cd /root/workspace/neko-futures-trader
```

### 2. Dependencies
```bash
pip install python-dotenv requests pandas numpy scipy scikit-learn \
  python-binance websocket-client
```

### 3. Configure `.env`
```bash
BINANCE_API_KEY=...
BINANCE_SECRET=...                # ⚠️ NOT BINANCE_API_SECRET
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL=<your_user_id>

# LLM gate (3-tier fallback)
NOUS_API_KEY=...
OPENROUTER_API_KEY=...
MINIMAX_API_KEY=...
```

### 4. Logs directory
```bash
mkdir -p /root/workspace/neko-futures-trader/logs
```

---

## ⚙️ Systemd Services

Three services run the system:

| Unit | Script | Purpose |
|------|--------|---------|
| `neko-scanner.service`   | `scanner.py`       | Scans markets every 60s, opens positions |
| `neko-monitor.service`   | `price-monitor.py` | Manages SL/TP, partial TPs, trailing |
| `neko-dashboard.service` | `dashboard_api.py` | Serves dashboard at `:8080` |

### Example unit (scanner)
```ini
[Unit]
Description=Neko Futures Scanner
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/workspace/neko-futures-trader
ExecStart=/usr/bin/python3 /root/workspace/neko-futures-trader/scanner.py
Restart=always
RestartSec=10
StandardOutput=append:/root/workspace/neko-futures-trader/logs/scanner.log
StandardError=append:/root/workspace/neko-futures-trader/logs/scanner.log

[Install]
WantedBy=multi-user.target
```

> 🚫 **Do NOT add `Environment=` lines for API keys.** `scanner.py` already
> loads `.env` at startup. Adding `Environment=` causes silent truncation
> bugs (see `AI_CONTRIBUTORS.md` 2026-05-19 entry — broke the LLM gate for
> 12+ hours).

### Enable
```bash
sudo systemctl daemon-reload
sudo systemctl enable neko-scanner neko-monitor neko-dashboard
sudo systemctl start  neko-scanner neko-monitor neko-dashboard
```

---

## 📊 Useful Commands

```bash
# Service management
sudo systemctl status   neko-scanner neko-monitor neko-dashboard
sudo systemctl restart  neko-scanner

# Live logs
journalctl -u neko-scanner -f --no-pager
tail -f /root/workspace/neko-futures-trader/logs/scanner.log
tail -f /root/workspace/neko-futures-trader/logs/pm.log

# Daily evaluation report
python3 /root/workspace/neko-futures-trader/scripts/daily_eval.py

# Trade history analysis
python3 /root/workspace/neko-futures-trader/scripts/analyze_trades.py

# Wallet + position summary
python3 /root/workspace/neko-futures-trader/scripts/check_balance.py

# Backtest a config change
python3 /root/workspace/neko-futures-trader/scripts/backtester.py
```

---

## 🌐 Dashboard

Open: `http://<server-ip>:8080/`
(Make sure `ufw allow 8080/tcp` is in place.)

Features:
- Real-time positions, balance, PnL
- 7-day win rate and closed PnL
- Sparkline charts and dark/light theme
- Mobile-friendly layout

---

## 📈 Signal Pipeline (10 stages)

1. **Universe** — `DYNAMIC_COINS_ENABLED=True` fetches all Binance perps with
   ≥ $2M 24h volume. Static `SAFE_COINS` is the fallback.
2. **Coverage** — top 50 gainers (LONG candidates) + bottom 75 losers
   (SHORT candidates), ~125 symbols per cycle.
3. **Direction** — chosen from price change, EMA9/21 alignment, and 4H trend.
4. **Filters** — chase limit, volume ratio, RSI guard, MACD histogram, EMA
   position, range position (30-bar), green/red candle counts, near-high/low.
5. **BTC regime** — skip crypto LONGs when BTC 4H EMA9 < EMA21.
6. **Trend filter** — LONG needs EMA9 > EMA21; SHORT needs EMA9 < EMA21
   (relaxed in bear regime for SHORT).
7. **Score** — sum of indicator weights. Must clear `MIN_SCORE_NORMAL`.
8. **Bonus scoring** — Bollinger squeeze, taker ratio, top-trader ratio,
   funding rate. Score is re-checked AFTER bonuses.
9. **LLM gate** — 3-tier fallback (Nous → OpenRouter → MiniMax). Asks about
   momentum alignment, RSI zone, SL reasonableness, red flags. Fail-open.
10. **Order placement** — MARKET entry, then separate SL/TP via
    `/fapi/v1/algoOrder`. Quantity formatted to `step_size` decimals.

---

## ⚙️ Trading Parameters (current)

| Param | Value | Notes |
|-------|-------|-------|
| `MAX_POSITIONS` | 8 | NORMAL mode |
| `MAX_POSITIONS_SLEEP` | 4 | SLEEP mode |
| `MAX_MARGIN_PERCENT` | 40% | |
| `MAX_RISK_PERCENT` | 1.5% | per trade |
| `LEVERAGE` | 10x | |
| `MIN_SCORE_NORMAL` | **7** | NEVER drop below 7 — 6 produced 22% WR / -$117 |
| `MIN_SCORE_SLEEP` | 7 | |
| `MIN_PRICE_CHANGE` | 2.0% | |
| `SCAN_INTERVAL` | **60s** | `time.sleep(60)` in scanner.py |
| `PRICE_SL` | **3.0%** | tightened from 5% on 2026-05-18 |
| `PRICE_TP` | **8.0%** | tightened from 15% on 2026-05-18 |
| `MIN_VOLUME_RATIO` | **1.5x** | <1x = pump without buyers |
| `CHASE_LIMIT_CRYPTO` | 4.0% | NO EXCEPTION |
| `CHASE_LIMIT_TRADFI` | 5.0% | NO EXCEPTION |
| `BTC_REGIME_CHECK` | True | skip crypto LONGs when BTC bearish |
| `LOSS_COOLDOWN_HOURS` | 48 | losses get 48h, wins get 24h |
| `MAX_DAILY_LOSS` | -30 USDT | auto-stop trading for the day |

### Partial TP / Trailing
| Stage | % | Action |
|-------|---|--------|
| TP1 | +4% | close 25% |
| TP2 | +6% | close 25% |
| TP3 (trailing TP) | +8% | trailing 50% |
| Breakeven | +3% | move SL to entry |
| Trailing SL | 1.5% | locks profit after breakeven |

---

## 🧠 LLM Signal Gate

The scanner runs an LLM second-opinion layer for every score-passing signal.
Status: **ENABLED** (re-enabled 2026-05-13 with relaxed anti-chasing 5%).

```
Scanner (rules + score ≥ 7) → LLM gate (Nous → OR → MiniMax) → Order
                                       ↑ fail-open on errors
```

### Fallback chain (in `llm_analyzer.py`)
```
1. Nous          xiaomi/mimo-v2-pro       (primary)
2. OpenRouter    nousresearch/hermes-4-70b
3. MiniMax       MiniMax-M2.5
```

### Config (`config.py`)
```python
LLM_ENABLED = True
LLM_MODEL = "xiaomi/mimo-v2-pro"
LLM_BASE_URL = "https://inference-api.nousresearch.com/v1/chat/completions"
LLM_MIN_SCORE = 4          # only call LLM for score ≥ 4
LLM_TEMPERATURE = 0.1
LLM_TIMEOUT = 15           # then fail-open

LLM_FALLBACK1_ENABLED = True
LLM_FALLBACK1_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_FALLBACK1_MODEL    = "nousresearch/hermes-4-70b"

LLM_FALLBACK2_ENABLED = True
LLM_FALLBACK2_BASE_URL = "https://api.minimaxi.chat/v1/chat/completions"
LLM_FALLBACK2_MODEL    = "MiniMax-M2.5"
```

### Design notes
- **Fail-open**: LLM down/timeout → trade still executes
- **Cache**: 5-min TTL per `(symbol, direction, score)` triple
- **Anti-chasing**: 5% (relaxed from 3% to avoid 93.7% rejection rate)
- **Telegram**: LLM reasoning included in entry notifications

---

## 🐛 Common Pitfalls (must-read for new agents)

1. **`BINANCE_SECRET` (not `BINANCE_API_SECRET`)** — wrong name → invalid signature
2. **`/fapi/v1/algoOrder`** — ALL symbols (crypto + TradFi) need this for SL/TP. The plain `/fapi/v1/order` returns `-4120: Order type not supported`.
3. **`openOrders` vs `openAlgoOrders`** — scanner-placed SL/TP only show in the latter. Health checks must call `/fapi/v1/openAlgoOrders`.
4. **Quantity precision** — `qty_steps * step_size` produces float artifacts. Format with `float(f"{qty:.{decimals}f}")`.
5. **systemd `Environment=` truncation** — multi-line values get silently dropped. Keep API keys in `.env` only.
6. **Stale `__pycache__/`** — after editing scanner.py, run `find . -name __pycache__ -type d -exec rm -rf {} + && find . -name "*.pyc" -delete` before restart.
7. **`MIN_SCORE` floor = 7 for crypto** — anything lower causes drawdown. Documented every time we tested it.
8. **`DYNAMIC_COINS_ENABLED=True`** in volatile markets — static `SAFE_COINS` covers only ~18% of perps. Disabling = 0/20 top movers ever traded.
9. **Bear market SHORT relaxations** — direction-conflict allowed, RSI guard 35→15, MACD-flat exception with vol ≥ 1.0x. Without these, 0 SHORT entries in bear regime.
10. **Range position protection** — LONG rejected if 30-bar range_pos > 70% (crypto) / > 85% (TradFi); SHORT rejected if range_pos < 30% (crypto) / < 15% (TradFi). Skipped when |price_change| > 7% (real breakouts).

---

## 🩺 Diagnosis Playbook

### When win rate < 30%
1. Aggregate REALIZED_PNL by symbol (`scripts/analyze_trades.py`)
2. For biggest losers: check entry `price_change` (chase?), `vol_ratio` (<1.5?), BTC regime, EMA alignment
3. Tighten the matching filter — don't broadly raise `MIN_SCORE`
4. Run `scripts/daily_eval.py` for an automated diff vs yesterday

### When zero signals for > 24h
1. Check market regime — sideways = expected
2. Verify `DYNAMIC_COINS_ENABLED=True`
3. Inspect rejection breakdown:
   ```bash
   grep "no signal" logs/scanner.log | tail -200 | \
     grep -oE "\([^)]+\)" | sort | uniq -c | sort -rn | head
   ```
4. Last resort: lower `MIN_PRICE_CHANGE` 2.0 → 1.5 (NEVER drop `MIN_SCORE` below 7)

### When positions have no SL/TP
1. Check `/fapi/v1/openAlgoOrders` for the symbol
2. If missing, place via `/fapi/v1/algoOrder` (5% SL, 15% TP as emergency)
3. Investigate the precision/timing bug — usually quantity formatting

---

## 📝 Recent History

- **2026-05-19** — bear-market SHORT filters + 30-bar `range_pos` protection. WR 19% → 67%.
- **2026-05-18** — full overhaul. SL 5%→3%, TP 15%→8%, vol 1.0x→1.5x, chase 6%/8%→4%/5%, BTC regime check, EMA9/21 trend filter, 48h loss cooldown.
- **2026-05-13** — re-enabled LLM with 5% anti-chasing; added crypto-index perps (BTCDOMUSDT, ALLUSDT); TradFi-tuned filters.
- **2026-05-06** — disabled LLM (was rejecting 98.5%); SL/TP overhaul; trailing SL fix.
- **2026-04-27** — switched from batch limit to MARKET + separate SL/TP; partial TP system; multi-timeframe analysis.

Full changelog in `CHANGELOG.md`. AI-assistance attribution in
`AI_CONTRIBUTORS.md`.

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
        - NOUS_API_KEY
        - OPENROUTER_API_KEY
        - MINIMAX_API_KEY
    startup:
      command: sudo systemctl start neko-scanner neko-monitor neko-dashboard
      type: service
    repo: https://github.com/lukmanc405/neko-futures-trader
```
