# SKILL.md - Neko Futures Trader

## Overview
Automated futures trading bot for Bittensor with scanning, DCA, SL/TP, and trailing stop loss.

**Emoji:** 🐱📈
**Requires:** Python 3.8+, Binance Futures API

---

## 📁 File Structure

```
neko-futures-trader/
├── config/
│   ├── .env              # API keys (BINANCE_API_KEY, BINANCE_SECRET, TELEGRAM_*)
│   ├── config.py         # Trading parameters
│   └── risk_config.json  # Risk limits
├── scripts/
│   ├── scanner-v8.py         # Scanner (5min)
│   ├── price-monitor.py       # SL/TP monitor (1sec)
│   ├── position_command.py   # Position checker
│   ├── dashboard_api.py       # Dashboard backend
│   ├── emergency_close.py     # Emergency closer
│   ├── daily_eval.py         # Daily evaluation
│   └── mint_tao20.py         # TAO-20 minter
├── data/
│   └── trades.db         # Trade history (SQLite)
└── logs/
    └── *.log             # Service logs
```

---

## 🚀 Setup

### 1. Install
```bash
# Copy to workspace
cp -r config scripts data /root/.openclaw/workspace/neko-futures-trader/

# Install dependencies
pip install python-dotenv requests pandas numpy scipy scikit-learn
```

### 2. Configure (.env)
```bash
BINANCE_API_KEY=your_key
BINANCE_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHANNEL=your_channel_id
```

### 3. Start
```bash
# Option A: Systemd (recommended)
systemctl enable neko-scanner neko-monitor neko-dashboard
systemctl start neko-scanner neko-monitor

# Option B: Manual
cd /root/.openclaw/workspace/neko-futures-trader
python3 scripts/scanner-v8.py &
python3 scripts/price-monitor.py &
```

---

## ⚙️ Systemd Services

### Install Services
```bash
# Scanner service
cat > /etc/systemd/system/neko-scanner.service << 'EOF'
[Unit]
Description=Neko Futures Trader Scanner
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/neko-futures-trader
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/neko-futures-trader/scripts/scanner-v8.py
Restart=always
RestartSec=10
StandardOutput=append:/root/.openclaw/workspace/neko-futures-trader/logs/scanner.log
StandardError=append:/root/.openclaw/workspace/neko-futures-trader/logs/scanner.log

[Install]
WantedBy=multi-user.target
EOF

# Monitor service
cat > /etc/systemd/system/neko-monitor.service << 'EOF'
[Unit]
Description=Neko Futures Trader Price Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/neko-futures-trader
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/neko-futures-trader/scripts/price-monitor.py
Restart=always
RestartSec=10
StandardOutput=append:/root/.openclaw/workspace/neko-futures-trader/logs/pm.log
StandardError=append:/root/.openclaw/workspace/neko-futures-trader/logs/pm.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl daemon-reload
systemctl enable neko-scanner neko-monitor
systemctl start neko-scanner neko-monitor
```

### Service Commands
```bash
systemctl status neko-scanner neko-monitor
systemctl restart neko-scanner
systemctl stop neko-monitor
journalctl -u neko-scanner -f
```

---

## 🌐 Dashboard

### Install Dashboard Service
```bash
cat > /etc/systemd/system/neko-dashboard.service << 'EOF'
[Unit]
Description=Neko Futures Trader Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/neko-futures-trader
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/neko-futures-trader/scripts/dashboard_api.py
Restart=always
RestartSec=5
StandardOutput=append:/root/.openclaw/workspace/neko-futures-trader/logs/dashboard.log
StandardError=append:/root/.openclaw/workspace/neko-futures-trader/logs/dashboard.log

[Install]
WantedBy=multi-user.target
EOF

systemctl enable neko-dashboard
systemctl start neko-dashboard
```

### Nginx Config
```nginx
server {
    listen 8443 ssl;
    server_name YOUR_IP;

    ssl_certificate /etc/nginx/ssl/ssl.crt;
    ssl_certificate_key /etc/nginx/ssl/ssl.key;

    root /var/www/html;

    location /neko-light.html {
        try_files /neko-light.html =404;
    }

    location /api {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        try_files /neko-light.html =404;
    }
}
```

### Copy Static Files
```bash
cp /root/.openclaw/skills/neko-futures-trader/neko-light.html /var/www/html/
```

### Access
- Dashboard: `https://YOUR_IP:8443/neko-light.html`
- API: `https://YOUR_IP:8443/api`

---

## 📊 Commands

### Check Positions
```bash
cd /root/.openclaw/workspace/neko-futures-trader
python3 scripts/position_command.py
```

### Daily Evaluation
```bash
cd /root/.openclaw/workspace/neko-futures-trader
python3 scripts/daily_eval.py
```

### Emergency Close All
```bash
cd /root/.openclaw/workspace/neko-futures-trader
python3 scripts/emergency_close.py
```

---

## 🔧 Configuration

### Trading Parameters (config/config.py)
| Parameter | Default | Description |
|-----------|---------|-------------|
| LEVERAGE | 10 | Leverage multiplier |
| MAX_POSITIONS | 5 | Max open positions |
| ENTRY_PERCENT | 6 | % of balance per entry |
| MAX_MARGIN | 30 | Max margin usage % |
| MAX_RISK_PERCENT | 1.5 | Max risk per trade % |
| MIN_SCORE | 3 | Min signal score to trigger |

### SL/TP (ATR-based)
| Volatility | SL | TP |
|------------|-----|-----|
| HIGH | 3×ATR | 6×ATR |
| NORMAL | 2.5×ATR | 5×ATR |
| LOW | 2×ATR | 4×ATR |

### Other
- BREAKEVEN: +5% (move SL to entry)
- TRAILING: +10% (activate trailing)
- SCAN_INTERVAL: 5 minutes

---

## 🐛 Known Issues Fixed

1. **Algo API**: Uses `/fapi/v1/algoOrder` (correct endpoint)
2. **Price Precision**: Rounds to tickSize per symbol
3. **Quantity Precision**: Proper rounding for each coin
4. **closePosition**: Uses `quantity=0` with `closePosition=true`

---

## metadata

```yaml
metadata:
  openclaw:
    emoji: 🐱📈
    requires:
      bins: [python3]
      env:
        - BINANCE_API_KEY
        - BINANCE_SECRET
        - TELEGRAM_BOT_TOKEN
        - TELEGRAM_CHANNEL
    startup:
      command: "systemctl start neko-scanner neko-monitor || (cp -r config scripts data /root/.openclaw/workspace/neko-futures-trader/ && systemctl daemon-reload && systemctl enable neko-scanner neko-monitor && systemctl start neko-scanner neko-monitor)"
      type: service
```

---

## Quick Reference

```bash
# Start all services
systemctl start neko-scanner neko-monitor neko-dashboard

# Check status
systemctl status neko-scanner neko-monitor

# View logs
tail -f /root/.openclaw/workspace/neko-futures-trader/logs/scanner.log
tail -f /root/.openclaw/workspace/neko-futures-trader/logs/pm.log

# Restart scanner
systemctl restart neko-scanner

# Check positions
cd /root/.openclaw/workspace/neko-futures-trader && python3 scripts/position_command.py
```
