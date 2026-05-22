# === Neko Futures Trader - CONFIGURATION ===
# Scanner v1.0.41 - Dynamic Coin List + Auto-add/Remove

# ── TRADING ──────────────────────────────────────────────────────────────────
LEVERAGE = 10                    # Futures leverage (10x)
MAX_POSITIONS = 8                # Max concurrent positions
AUTO_FILL_EMPTY_SLOTS = True     # Auto-find entries when positions < MAX
ENTRY_PERCENT = 8                # % of balance per trade (NORMAL mode)

# ── SLEEP MODE ───────────────────────────────────────────────────────────────
SLEEP_MODE = False              # Sleep mode toggle (use ./sleepmode command)
MAX_POSITIONS_SLEEP = 4          # Max positions in SLEEP mode
ENTRY_PERCENT_SLEEP = 5          # Entry % in SLEEP mode
MIN_SCORE_SLEEP = 7             # Min score to enter in SLEEP mode

# ── NORMAL MODE ──────────────────────────────────────────────────────────────
MIN_SCORE_NORMAL = 6             # 2026-05-21: 7→6 with new quality filters (ADX, momentum, sustained-dump, vol surge)

# ── SL/TP STRATEGY (2026-05-18 OVERHAUL) ────────────────────────────────────
# Old: SL=5%, TP=15% → 22% WR, big losses. New: SL=3%, TP=8% → tighter risk, better R:R
PRICE_TP = 8.0                  # Take Profit: +8% for LONG, -8% for SHORT
PRICE_SL = 3.0                  # Stop Loss: -3% for LONG, +3% for SHORT

# ── BREAKEVEN & TRAILING ─────────────────────────────────────────────────────
MIN_PROFIT_BREAKEVEN = 3.0       # % profit to start trailing SL (was 5%)
TRAIL_SL_LOCK = 1.5              # % profit to lock when trailing (was 2%)
TRAIL_SL_DISTANCE = 1.5          # SL trails this % below current price (was 2%)
MIN_PROFIT_TRAILING_TP = 6.0    # % profit to activate trailing TP (was 10%)
TRAIL_PERCENT = 1.5             # Trail TP by this % when trailing (was 2%)

# ── PARTIAL TP (2026-05-18: 3-stage exit) ───────────────────────────────────
TP1_PERCENT = 4.0               # Close 25% at this % profit (was 5%)
TP1_CLOSE_PCT = 0.25
TP2_PERCENT = 6.0               # Close another 25% at this % profit (was 10%)
TP2_CLOSE_PCT = 0.25
# Remaining 50% runs to PRICE_TP (8%) or trailing TP

# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────
POST_SIGNALS_TO_TELEGRAM = True
NOTIFY_ON_OPEN = True
NOTIFY_ON_CLOSE = True
NOTIFY_ON_BREAKEVEN = False
NOTIFY_ON_TRAILING_SL = False
NOTIFY_ON_TRAILING_TP = False

# ── SCANNER ──────────────────────────────────────────────────────────────────
SCAN_INTERVAL = 300             # Scanner run every 5 minutes
MIN_PRICE_CHANGE = 1.5          # 2026-05-21: 2%→1.5% catch trend-aligned moves missed at 2%
SKIP_RECENT_HOURS = 24          # Skip re-entry for 24h after close
LOSS_COOLDOWN_HOURS = 48        # 2026-05-18: Skip re-entry 48h after a LOSS (prevent revenge trading)
MIN_VOLUME_RATIO = 1.5          # 2026-05-18: Raised from 1.0 — 0.3-0.5x entries were all losers
CHASE_LIMIT_CRYPTO = 6.0        # 2026-05-21: 5%→6% + pullback detection catches extended moves
CHASE_LIMIT_TRADFI = 5.0        # Max % change for TradFi entries
BTC_REGIME_CHECK = True         # 2026-05-8: Skip LONG if BTC 4H trend is bearish

# ── DYNAMIC COIN LIST ────────────────────────────────────────────────────────
# Auto-fetches all tradeable Binance Futures symbols, filters by volume,
# excludes settling/delisting pairs. Refreshes every hour.
# See dynamic_coins.py for implementation.
DYNAMIC_COINS_ENABLED = True    # 2026-05-17: Enabled — static SAFE_COINS only covers 18% of market, missing 97% of volatile movers
DYNAMIC_MIN_VOLUME = 2_000_000  # Minimum 24h volume in USDT ($2M)

# ── LLM ANALYZER ────────────────────────────────────────────────────────────
LLM_ENABLED = True               # Re-enabled 2026-05-15 with volume filter
LLM_MODEL = "xiaomi/mimo-v2-pro"
LLM_MIN_SCORE = 4
LLM_TEMPERATURE = 0.1
LLM_BASE_URL = "https://inference-api.nousresearch.com/v1/chat/completions"
LLM_TIMEOUT = 15

LLM_FALLBACK1_ENABLED = True
LLM_FALLBACK1_BASE_URL = "http://localhost:20128/v1/chat/completions"
LLM_FALLBACK1_MODEL = "kr/claude-haiku-4.5"

LLM_FALLBACK2_ENABLED = True
LLM_FALLBACK2_BASE_URL = "https://api.minimaxi.chat/v1/chat/completions"
LLM_FALLBACK2_MODEL = "MiniMax-M2.5"

# ── LLM BACKUP MODE (2026-05-22: when all LLM providers fail) ───────────
# Options: "rule_based" (smart technical filter), "fail_open" (old: approve all), "fail_closed" (reject all)
LLM_BACKUP_MODE = "rule_based"
LLM_BACKUP_MIN_SCORE = 8            # Higher bar than normal MIN_SCORE (6) — only high-confidence setups
LLM_BACKUP_MAX_CHASE = 5.0          # Max % 24h change before rejecting (anti-chase)
LLM_BACKUP_MAX_RSI_LONG = 68.0      # Reject LONG if RSI above this
LLM_BACKUP_MIN_RSI_LONG = 30.0      # Reject LONG if RSI below this (falling knife)
LLM_BACKUP_MAX_RSI_SHORT = 78.0     # Reject SHORT if RSI above this (squeeze risk)
LLM_BACKUP_MIN_RSI_SHORT = 32.0     # Reject SHORT if RSI below this (oversold)
LLM_BACKUP_MIN_VOL_RATIO = 1.0      # Minimum volume ratio (no conviction below this)
LLM_BACKUP_MAX_FUNDING_LONG = 0.08  # Max funding rate for LONG (crowded)
LLM_BACKUP_MAX_FUNDING_SHORT = -0.08  # Max funding rate for SHORT (crowded)

# ── RISK ─────────────────────────────────────────────────────────────────────
MAX_MARGIN_PERCENT = 40
MAX_RISK_PERCENT = 1.5
MAX_DAILY_LOSS = -30.0           # 2026-05-18: Stop trading if daily PNL hits -30 USDT (prevents blowup days)

# ── SAFE COINS (FALLBACK — only used if DYNAMIC_COINS_ENABLED = False) ───────
# Static list as backup. Dynamic mode fetches live from Binance API.
SAFE_COINS = [
    # === CRYPTO (blue-chip + mid-cap) ===
    'BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT','DOGEUSDT',
    'ADAUSDT','AVAXUSDT','DOTUSDT','LINKUSDT','LTCUSDT','BCHUSDT',
    'ATOMUSDT','UNIUSDT','ETCUSDT','XLMUSDT','FILUSDT',
    'APTUSDT','NEARUSDT','ARBUSDT','OPUSDT','AAVEUSDT','MKRUSDT',
    'GRTUSDT','SNXUSDT','IMXUSDT','ALGOUSDT','SANDUSDT',
    'MANAUSDT','AXSUSDT','CHZUSDT','ENJUSDT','NEOUSDT','ZECUSDT',
    'EOSUSDT','THETAUSDT','KAVAUSDT','ZILUSDT','KSMUSDT',
    'RUNEUSDT','MINAUSDT','QNTUSDT','LDOUSDT','SUIUSDT',
    'SEIUSDT','TIAUSDT','INJUSDT','WIFUSDT','ORDIUSDT',
    'RENDERUSDT','TAOUSDT','ONDOUSDT','PENDLEUSDT','STXUSDT',
    'TRXUSDT','EIGENUSDT','DYDXUSDT','CAKEUSDT','ENSUSDT',
    'FETUSDT','WLDUSDT','JUPUSDT','1000PEPEUSDT','1000SHIBUSDT',
    '1000BONKUSDT','ENAUSDT','PENGUUSDT','TRUMPUSDT','TONUSDT',
    'HYPEUSDT','POLUSDT',
    # === STOCK PERPS ===
    'TSLAUSDT','NVDAUSDT','AAPLUSDT','AMZNUSDT','GOOGLUSDT','METAUSDT',
    'MSFTUSDT','AMDUSDT','COINUSDT','MSTRUSDT','HOODUSDT','CRCLUSDT',
    'PLTRUSDT','BABAUSDT','INTCUSDT','TSMUSDT','AVGOUSDT','QCOMUSDT',
    'MUUSDT','BILLUSDT','SNDKUSDT','EWYUSDT',
    # === STOCK INDICES ===
    'QQQUSDT','SPYUSDT',
    # === CRYPTO INDICES ===
    'BTCDOMUSDT','ALLUSDT',
    # === COMMODITIES ===
    'XAUUSDT','XAGUSDT','XPTUSDT','XPDUSDT',
    'CLUSDT','BZUSDT','NATGASUSDT','COPPERUSDT',
]
