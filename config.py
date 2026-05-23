# === Neko Futures Trader - CONFIGURATION ===
# Scanner v1.0.42 - AGGRESSIVE OVERHAUL 2026-05-22
# Goal: Maximize profit per trade, reduce noise entries, protect capital

# ── TRADING ──────────────────────────────────────────────────────────────────
LEVERAGE = 10                    # Futures leverage (10x)
MAX_POSITIONS = 4                # 2026-05-22: 8→4 — fewer, higher quality positions (concentration > diversification at small capital)
AUTO_FILL_EMPTY_SLOTS = True     # Auto-find entries when positions < MAX
ENTRY_PERCENT = 6                # 2026-05-22: 8→6% — smaller positions = survive more SL hits

# ── SLEEP MODE ───────────────────────────────────────────────────────────────
SLEEP_MODE = False              # Sleep mode toggle (use ./sleepmode command)
MAX_POSITIONS_SLEEP = 2          # 2026-05-22: 4→2 — sleep mode = very selective
ENTRY_PERCENT_SLEEP = 4          # 2026-05-22: 5→4%
MIN_SCORE_SLEEP = 9             # 2026-05-22: 7→9 — only A+ setups in sleep mode

# ── NORMAL MODE ──────────────────────────────────────────────────────────────
MIN_SCORE_NORMAL = 8             # 2026-05-22 OVERHAUL: 7→8 — demand strong signal convergence. Score 6-7 entries were 80%+ losers.

# ── SL/TP STRATEGY (2026-05-22 AGGRESSIVE OVERHAUL) ─────────────────────────
# Tighter SL + bigger TP = higher R:R per trade
# Old: SL=3%, TP=8% (R:R 1:2.6). New: SL=2.5%, TP=10% (R:R 1:4)
# At 10x leverage: SL = 25% account risk, TP = 100% gain per unit
PRICE_TP = 10.0                 # 2026-05-22: 8→10% — let winners run bigger
PRICE_SL = 2.5                  # 2026-05-22: 3→2.5% — tighter stop = less pain per loss

# ── BREAKEVEN & TRAILING ─────────────────────────────────────────────────────
MIN_PROFIT_BREAKEVEN = 2.5       # 2026-05-22: 3→2.5% — move to breakeven faster (protect capital)
TRAIL_SL_LOCK = 1.5              # % profit to lock when trailing
TRAIL_SL_DISTANCE = 1.2          # 2026-05-22: 1.5→1.2% — tighter trail to lock more profit
MIN_PROFIT_TRAILING_TP = 7.0    # 2026-05-22: 6→7% — only trail TP on big winners
TRAIL_PERCENT = 1.5              # Trail TP by this %

# ── PARTIAL TP (2026-05-22: 3-stage exit, aggressive) ────────────────────────
TP1_PERCENT = 3.5               # 2026-05-22: 4→3.5% — take first partial earlier (secure profit faster)
TP1_CLOSE_PCT = 0.30            # 2026-05-22: 25→30% — take more off the table early
TP2_PERCENT = 6.0               # Close another 25% at 6%
TP2_CLOSE_PCT = 0.25
# Remaining 45% runs to PRICE_TP (10%) or trailing TP

# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────
POST_SIGNALS_TO_TELEGRAM = True
NOTIFY_ON_OPEN = True
NOTIFY_ON_CLOSE = True
NOTIFY_ON_BREAKEVEN = False
NOTIFY_ON_TRAILING_SL = False
NOTIFY_ON_TRAILING_TP = False

# ── SCANNER (2026-05-22 AGGRESSIVE FILTERS) ─────────────────────────────────
SCAN_INTERVAL = 300             # Scanner run every 5 minutes
MIN_PRICE_CHANGE = 2.5          # 2026-05-22: 1.5→2.5% — only trade meaningful moves (noise < 2%)
SKIP_RECENT_HOURS = 24          # Skip re-entry for 24h after close
LOSS_COOLDOWN_HOURS = 72        # 2026-05-22: 48→72h — 3 days cooldown after loss (no revenge)
MIN_VOLUME_RATIO = 2.5          # 2026-05-22: 1.5→2.5x — require serious volume (real moves only)
CHASE_LIMIT_CRYPTO = 4.0        # 2026-05-22: 6→4% — much tighter chase filter (never chase)
CHASE_LIMIT_TRADFI = 3.5        # 2026-05-22: 5→3.5% — TradFi even tighter (slow moves)
BTC_REGIME_CHECK = True         # Skip LONG if BTC bearish, SHORT if bullish

# ── DYNAMIC COIN LIST ────────────────────────────────────────────────────────
DYNAMIC_COINS_ENABLED = True
DYNAMIC_MIN_VOLUME = 5_000_000  # 2026-05-22: $2M→$5M — only liquid coins (no low-vol traps)

# ── LLM ANALYZER ────────────────────────────────────────────────────────────
LLM_ENABLED = True
LLM_MODEL = "xiaomi/mimo-v2-pro"
LLM_MIN_SCORE = 6               # 2026-05-22: 4→6 — LLM only analyzes high-scoring signals
LLM_TEMPERATURE = 0.1
LLM_BASE_URL = "https://inference-api.nousresearch.com/v1/chat/completions"
LLM_TIMEOUT = 15

LLM_FALLBACK1_ENABLED = False
LLM_FALLBACK1_BASE_URL = ""
LLM_FALLBACK1_MODEL = ""

LLM_FALLBACK2_ENABLED = False
LLM_FALLBACK2_BASE_URL = ""
LLM_FALLBACK2_MODEL = ""

# ── LLM BACKUP MODE (when all LLM providers fail) ───────────────────────────
LLM_BACKUP_MODE = "rule_based"
LLM_BACKUP_MIN_SCORE = 9        # 2026-05-22: 8→9 — backup needs A+ signals only
LLM_BACKUP_MAX_CHASE = 4.0      # 2026-05-22: 5→4% — tighter chase in backup mode
LLM_BACKUP_MAX_RSI_LONG = 65.0  # 2026-05-22: 68→65 — stricter RSI in backup
LLM_BACKUP_MIN_RSI_LONG = 32.0  # 2026-05-22: 30→32 — avoid falling knife
LLM_BACKUP_MAX_RSI_SHORT = 75.0 # 2026-05-22: 78→75
LLM_BACKUP_MIN_RSI_SHORT = 35.0 # 2026-05-22: 32→35 — avoid oversold bounce
LLM_BACKUP_MIN_VOL_RATIO = 2.0  # 2026-05-22: 1→2x — backup needs volume confirmation
LLM_BACKUP_MAX_FUNDING_LONG = 0.06   # 2026-05-22: 0.08→0.06 — tighter funding
LLM_BACKUP_MAX_FUNDING_SHORT = -0.06

# ── RISK (2026-05-22 AGGRESSIVE CAPITAL PROTECTION) ─────────────────────────
MAX_MARGIN_PERCENT = 30          # 2026-05-22: 40→30% — never use more than 30% margin
MAX_RISK_PERCENT = 1.5
MAX_DAILY_LOSS = -20.0           # 2026-05-22: -30→-20 USDT — stop trading earlier on bad days

# ── SAFE COINS (FALLBACK — only used if DYNAMIC_COINS_ENABLED = False) ───────
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
