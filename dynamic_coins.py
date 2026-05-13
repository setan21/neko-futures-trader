"""
Dynamic Coin List — Auto-manage SAFE_COINS
Fetches all tradeable Binance Futures symbols, filters by volume,
excludes settling/delisting pairs. Refreshes every hour.
"""
import requests
import time
import os
import logging

logger = logging.getLogger("neko")

# ── CONFIG ──────────────────────────────────────────────────────────────────
MIN_VOLUME_USDT = 2_000_000       # Minimum 24h volume in USDT
REFRESH_INTERVAL = 3600            # Refresh every 1 hour
BYPASS_VOLUME_FILTER = {           # Always include these regardless of volume
    # Blue-chip crypto (safety net)
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT',
    'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT',
    'ATOMUSDT', 'UNIUSDT', 'ETCUSDT', 'XLMUSDT', 'FILUSDT',
    'APTUSDT', 'NEARUSDT', 'ARBUSDT', 'OPUSDT', 'INJUSDT', 'SUIUSDT',
    'SEIUSDT', 'TIAUSDT', 'AAVEUSDT', 'MKRUSDT',
    # Stock indices
    'QQQUSDT', 'SPYUSDT',
    # Precious metals
    'XAUUSDT', 'XAGUSDT', 'XPTUSDT', 'XPDUSDT',
}

# ── CACHE ───────────────────────────────────────────────────────────────────
_cache = {
    'coins': None,          # set of symbol strings
    'last_refresh': 0,      # timestamp
    'tradable_info': {},    # symbol -> {volume, price, pct_change, contract_type}
}


def _fetch_tradable_symbols() -> dict:
    """Fetch all TRADING symbols from Binance Futures."""
    try:
        resp = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo', timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {s['symbol']: {
            'status': s['status'],
            'contractType': s.get('contractType', 'PERPETUAL'),
            'baseAsset': s.get('baseAsset', ''),
            'quoteAsset': s.get('quoteAsset', ''),
        } for s in data['symbols']}
    except Exception as e:
        logger.error(f"Failed to fetch exchange info: {e}")
        return {}


def _fetch_tickers() -> dict:
    """Fetch 24h tickers for volume data."""
    try:
        resp = requests.get('https://fapi.binance.com/fapi/v1/ticker/24hr', timeout=10)
        resp.raise_for_status()
        return {t['symbol']: {
            'volume': float(t.get('quoteVolume', 0)),
            'price': float(t.get('lastPrice', 0)),
            'pct_change': float(t.get('priceChangePercent', 0)),
        } for t in resp.json()}
    except Exception as e:
        logger.error(f"Failed to fetch tickers: {e}")
        return {}


def refresh_coins(force: bool = False) -> set:
    """
    Refresh the dynamic coin list. Returns set of 'SYMBOLUSDT' strings.
    
    Logic:
    1. Fetch all TRADING symbols (exclude SETTLING/PENDING)
    2. Filter USDT-margined perpetuals only
    3. Apply volume filter (MIN_VOLUME_USDT)
    4. Always include BYPASS_VOLUME_FILTER symbols
    5. Cache for REFRESH_INTERVAL seconds
    """
    now = time.time()
    if not force and _cache['coins'] and (now - _cache['last_refresh']) < REFRESH_INTERVAL:
        return _cache['coins']

    logger.info("🔄 Refreshing dynamic coin list from Binance...")

    # Fetch data
    symbols_info = _fetch_tradable_symbols()
    tickers = _fetch_tickers()

    if not symbols_info or not tickers:
        logger.warning("⚠️ Failed to fetch data, using cached coins")
        return _cache['coins'] or set()

    # Filter: TRADING status + USDT-margined
    tradable = {}
    for sym, info in symbols_info.items():
        if info['status'] != 'TRADING':
            continue
        if not sym.endswith('USDT'):
            continue
        # Skip quarterly futures
        if info['contractType'] in ('CURRENT_QUARTER', 'NEXT_QUARTER'):
            continue
        tradable[sym] = info

    # Apply volume filter
    dynamic_coins = set()
    low_volume = []
    settling_blocked = []

    for sym, info in tradable.items():
        ticker = tickers.get(sym, {})
        vol = ticker.get('volume', 0)

        # Always include bypass symbols
        if sym in BYPASS_VOLUME_FILTER:
            dynamic_coins.add(sym)
            continue

        # Volume filter
        if vol >= MIN_VOLUME_USDT:
            dynamic_coins.add(sym)
        else:
            low_volume.append((sym, vol))

    # Store metadata
    _cache['coins'] = dynamic_coins
    _cache['last_refresh'] = now
    _cache['tradable_info'] = {
        sym: tickers.get(sym, {}) for sym in dynamic_coins
    }

    # Stats
    tradifi_count = sum(1 for s in dynamic_coins 
                        if symbols_info.get(s, {}).get('contractType') == 'TRADIFI_PERPETUAL')
    perp_count = len(dynamic_coins) - tradifi_count

    logger.info(
        f"✅ Dynamic coins refreshed: {len(dynamic_coins)} total "
        f"({perp_count} crypto, {tradifi_count} TradFi) | "
        f"Volume filter: {MIN_VOLUME_USDT/1e6:.0f}M USDT"
    )

    return dynamic_coins


def get_coins() -> set:
    """Get current coin set (refreshes if stale)."""
    return refresh_coins()


def get_coin_info(symbol: str) -> dict:
    """Get ticker info for a symbol."""
    refresh_coins()  # ensure cache is fresh
    return _cache['tradable_info'].get(symbol, {})


def get_stats() -> dict:
    """Get stats about current coin list."""
    coins = refresh_coins()
    info = _cache.get('tradable_info', {})

    # Categorize
    crypto = []
    stocks = []
    commodities = []
    indices = []
    other = []

    STOCK_KEYWORDS = {
        'TSLA', 'NVDA', 'AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'AMD',
        'COIN', 'MSTR', 'HOOD', 'CRCL', 'PLTR', 'BABA', 'INTC', 'TSM',
        'AVGO', 'QCOM', 'BA', 'NFLX', 'DIS', 'PYPL', 'SQ', 'UBER',
        'ABNB', 'SHOP', 'RIVN', 'SOFI', 'ARM', 'SMCI', 'MU', 'MRVL',
        'LRCX', 'KLAC', 'SNAP', 'PINS', 'RBLX', 'NET', 'DDOG', 'SNOW',
        'PANW', 'CRWD', 'TEAM', 'NOW', 'WDAY', 'TTD', 'MELI', 'SE',
        'GRAB', 'CPNG', 'LI', 'NIO', 'XPEV', 'LCID', 'GME', 'AMC',
        'BB', 'NKLA', 'DJT', 'ROKU', 'TTWO', 'EA', 'SONY', 'WMT',
        'JPM', 'GS', 'V', 'MA', 'BAC', 'F', 'GM', 'RACE', 'HON',
        'CAT', 'DE', 'UNH', 'JNJ', 'PFE', 'MRK', 'ABBV', 'LLY',
        'COST', 'HD', 'NKE', 'SBUX', 'MCD', 'PEP', 'KO', 'PAYP',
        'BILL', 'EWY', 'EWJ', 'USAR', 'SNDK',
    }
    COMMODITY_KEYWORDS = {'XAU', 'XAG', 'XPT', 'XPD', 'CL', 'NATGAS', 'COPPER', 'BZ'}
    INDEX_KEYWORDS = {'QQQ', 'SPY', 'DIA', 'IWM'}

    for sym in sorted(coins):
        base = sym.replace('USDT', '')
        if base in STOCK_KEYWORDS:
            stocks.append(sym)
        elif base in COMMODITY_KEYWORDS:
            commodities.append(sym)
        elif base in INDEX_KEYWORDS:
            indices.append(sym)
        else:
            crypto.append(sym)

    return {
        'total': len(coins),
        'crypto': len(crypto),
        'stocks': len(stocks),
        'commodities': len(commodities),
        'indices': len(indices),
        'min_volume': MIN_VOLUME_USDT,
        'last_refresh': _cache['last_refresh'],
    }


# ── TELEGRAM COMMAND HELPER ─────────────────────────────────────────────────
def format_coin_list() -> str:
    """Format coin list for Telegram display."""
    stats = get_stats()
    coins = get_coins()

    # Get top movers
    info = _cache.get('tradable_info', {})
    top_vol = sorted(
        [(s, info.get(s, {}).get('volume', 0)) for s in coins],
        key=lambda x: -x[1]
    )[:15]

    msg = (
        f"📊 **Dynamic Coin List**\n\n"
        f"Total: **{stats['total']}** pairs\n"
        f"• Crypto: {stats['crypto']}\n"
        f"• Stocks: {stats['stocks']}\n"
        f"• Commodities: {stats['commodities']}\n"
        f"• Indices: {stats['indices']}\n\n"
        f"Min Volume: ${stats['min_volume']/1e6:.0f}M\n\n"
        f"**Top 15 by Volume:**\n"
    )
    for sym, vol in top_vol:
        pct = info.get(sym, {}).get('pct_change', 0)
        emoji = '🟢' if pct > 0 else '🔴' if pct < 0 else '⚪'
        msg += f"• {sym}: ${vol/1e6:.0f}M {emoji}{pct:+.1f}%\n"

    return msg


if __name__ == '__main__':
    # Test: print stats
    import json
    logging.basicConfig(level=logging.INFO)
    coins = refresh_coins(force=True)
    stats = get_stats()
    print(json.dumps(stats, indent=2))
    print(f"\nTotal coins: {len(coins)}")
    print(f"Sample: {sorted(list(coins))[:20]}")
