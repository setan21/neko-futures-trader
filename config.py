# === Neko Futures Trader - CONFIGURATION ===
# Scanner v1.0.40 - New LONG/SHORT Strategy + Sleep Mode

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
MIN_SCORE_NORMAL = 4             # Min score to enter in NORMAL mode

# ── SL/TP STRATEGY ────────────────────────────────────────────────────────────
# PRIMARY: ATR-based (adapts to token volatility)
# FALLBACK: Uses PRICE_TP/PRICE_SL when ATR is too tight or too wide

# ATR Multipliers (R:R 1:4)
ATR_HIGH_VOLATILITY = 3.0       # ATR > X% = high volatility token
ATR_MULTIPLIER_SL_HIGH = 2.0     # SL for volatile tokens (2x ATR)
ATR_MULTIPLIER_TP_HIGH = 8.0     # TP for volatile tokens (8x ATR)
ATR_MULTIPLIER_SL_NORMAL = 2.0   # Normal SL multiplier
ATR_MULTIPLIER_TP_NORMAL = 8.0   # Normal TP multiplier
ATR_MULTIPLIER_SL_LOW = 1.5     # Tighter SL for stable tokens
ATR_MULTIPLIER_TP_LOW = 6.0     # Tighter TP for stable tokens

# PRICE FALLBACK (when ATR-based SL would be too tight/wide)
PRICE_TP = 15.0                 # Take Profit: +15% for LONG, -15% for SHORT
PRICE_SL = 5.0                  # Stop Loss: -5% for LONG, +5% for SHORT
PRICE_FALLBACK_MAX_ATR = 10.0    # If ATR% > 10%, use PRICE_TP/PRICE_SL instead
PRICE_FALLBACK_MIN_ATR = 1.0    # If ATR% < 1%, use PRICE_TP/PRICE_SL instead

# ── BREAKEVEN & TRAILING ─────────────────────────────────────────────────────
MIN_PROFIT_BREAKEVEN = 5.0       # % profit to start trailing SL
TRAIL_SL_LOCK = 2.0              # % profit to lock when trailing (SL = entry + this %)
TRAIL_SL_DISTANCE = 2.0          # SL trails this % below current price
MIN_PROFIT_TRAILING_TP = 10.0   # % profit to activate trailing TP
TRAIL_PERCENT = 2.0             # Trail TP by this % when trailing

# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────
POST_SIGNALS_TO_TELEGRAM = True
NOTIFY_ON_OPEN = True
NOTIFY_ON_CLOSE = True
NOTIFY_ON_BREAKEVEN = True
NOTIFY_ON_TRAILING_SL = True
NOTIFY_ON_TRAILING_TP = True

# ── SCANNER ──────────────────────────────────────────────────────────────────
SCAN_INTERVAL = 300             # Scanner run every 5 minutes
MIN_PRICE_CHANGE = 3.0          # Min % price change for signal
SKIP_RECENT_HOURS = 24          # Skip re-entry for 24h after close

# ── LLM ANALYZER (Hybrid AI Gate) ────────────────────────────────────────────
# Second opinion layer — LLM checks candidates before execution
LLM_ENABLED = True              # Toggle LLM analysis on/off
LLM_MODEL = "anthropic/claude-3.5-haiku"  # Model via OpenRouter
LLM_MIN_SCORE = 4               # Only analyze candidates with score >= this
LLM_TEMPERATURE = 0.1           # Low = deterministic
LLM_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"  # OpenRouter endpoint
LLM_TIMEOUT = 15                # Seconds before timeout (fail-open)

# ── RISK ─────────────────────────────────────────────────────────────────────
MAX_MARGIN_PERCENT = 40         # Max margin usage %
MAX_RISK_PERCENT = 1.5          # Max risk per trade %

# ── SAFE COINS ───────────────────────────────────────────────────────────────
SAFE_COINS = [
    'BNBUSDT','ETHUSDT','BTCUSDT','XRPUSDT','ADAUSDT','DOGEUSDT',
    'SOLUSDT','DOTUSDT','MATICUSDT','LTCUSDT','AVAXUSDT','LINKUSDT',
    'ATOMUSDT','UNIUSDT','ETCUSDT','XLMUSDT','BCHUSDT','FILUSDT',
    'APTUSDT','NEARUSDT','ARBUSDT','OPUSDT','AAVEUSDT','MKRUSDT',
    'GRTUSDT','SNXUSDT','IMXUSDT','ALGOUSDT','FTMUSDT','SANDUSDT',
    'MANAUSDT','AXSUSDT','CHZUSDT','ENJUSDT','NEOUSDT','ZECUSDT',
    'EOSUSDT','THETAUSDT','KAVAUSDT','WAVESUSDT','ZILUSDT','KSMUSDT',
    'RUNEUSDT','KLAYUSDT','MINAUSDT','QNTUSDT','LDOUSDT','SUIUSDT',
    'SEIUSDT','TIAUSDT','INJUSDT','TIAUSD_PERP','WIFUSDT','ORDIUSDT'
]
