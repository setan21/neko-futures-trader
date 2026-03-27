# 🐱 Neko Futures Trader

Automated Bittensor Futures Trading Bot with DCA, SL/TP, and Trailing.

## 📁 Project Structure

```
openclaw/
├── skills/neko-futures-trader/   # Source scripts (git repo)
│   ├── scanner-v8.py             # Main scanner (5min intervals)
│   ├── price-monitor.py          # SL/TP monitor (1sec intervals)
│   ├── position_command.py        # Check positions
│   ├── dashboard_api.py          # Dashboard API server
│   ├── emergency_close.py         # Emergency position closer
│   ├── daily_eval.py             # Daily performance evaluation
│   ├── mint_tao20.py             # TAO-20 inscription minter
│   ├── config.py                 # Trading parameters
│   ├── .env                      # API keys (gitignored)
│   ├── SKILL.md                  # This file
│   └── README.md
│
└── workspace/neko-futures-trader/  # Runtime environment
    ├── .env                       # API keys symlink/copy
    ├── logs/                      # Service logs
    │   ├── scanner.log
    │   ├── pm.log
    │   └── dashboard.log
    └── data/
        └── trades.db              # SQLite trade history
```

## 🚀 Quick Start

### 1. Clone & Setup
```bash
# Install skill
git clone https://github.com/lukmanc405/neko-futures-trader.git /root/.openclaw/skills/neko-futures-trader

# Setup workspace
mkdir -p /root/.openclaw/workspace/neko-futures-trader/{logs,data}
cp /root/.openclaw/skills/neko-futures-trader/.env.example /root/.openclaw/workspace/neko-futures-trader/.env
```

### 2. Configure API Keys
```bash
nano /root/.openclaw/workspace/neko-futures-trader/.env
```
```
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHANNEL=your_channel
```

### 3. Install Dependencies
```bash
pip install python-dotenv requests pandas numpy scipy scikit-learn
```

### 4. Start Services
```bash
# Systemd (recommended)
systemctl enable neko-scanner neko-monitor neko-dashboard
systemctl start neko-scanner neko-monitor neko-dashboard

# Or manual
cd /root/.openclaw/workspace/neko-futures-trader
python3 /root/.openclaw/skills/neko-futures-trader/scanner-v8.py &
python3 /root/.openclaw/skills/neko-futures-trader/price-monitor.py &
```

## ⚙️ Configuration

### Trading Parameters (config/config.py)
```python
LEVERAGE = 10
MAX_POSITIONS = 5        # Max open positions
ENTRY_PERCENT = 6        # % of balance per trade
MAX_MARGIN = 30          # Max margin usage %
MAX_RISK_PERCENT = 1.5   # Max risk per trade %

# SL/TP based on ATR volatility
HIGH_VOL:   SL=3×ATR, TP=6×ATR
NORMAL:     SL=2.5×ATR, TP=5×ATR
LOW:        SL=2×ATR, TP=4×ATR

BREAKEVEN = +5%    # Move SL to entry when profit reaches +5%
TRAILING = +10%   # Activate trailing at +10% profit
SCAN_INTERVAL = 5 minutes
MIN_SCORE = 3     # Min signal score to trigger
```

## 📊 Commands

### Check Positions
```bash
cd /root/.openclaw/workspace/neko-futures-trader
python3 /root/.openclaw/skills/neko-futures-trader/position_command.py
```

### View Logs
```bash
tail -f /root/.openclaw/workspace/neko-futures-trader/logs/scanner.log
tail -f /root/.openclaw/workspace/neko-futures-trader/logs/pm.log
```

### Service Management
```bash
systemctl status neko-scanner neko-monitor neko-dashboard
systemctl restart neko-scanner neko-monitor
journalctl -u neko-scanner -f
```

## 🌐 Dashboard

Access at: `https://YOUR_IP:8443/neko-light.html`

### Dashboard Setup
```bash
# Copy HTML
cp /root/.openclaw/skills/neko-futures-trader/neko-light.html /var/www/html/

# Nginx config (see SKILL.md for full nginx.conf)
# Start dashboard
systemctl start neko-dashboard
```

## 📈 Daily Evaluation

Auto-runs at 4 PM via cron:
```bash
python3 /root/.openclaw/skills/neko-futures-trader/daily_eval.py
```

## 🐛 Known Fixes

1. **Algo API endpoint**: Uses `/fapi/v1/algoOrder` (not `/orderAlg`)
2. **Price precision**: Rounds to tickSize for each symbol
3. **Quantity**: Uses `quantity=0` with `closePosition=true`
4. **Margin**: Reduced from 40% to 30%
5. **Max positions**: Reduced from 7 to 5

## 📜 License

MIT
