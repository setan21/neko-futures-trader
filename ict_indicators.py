"""
ICT Indicators Module
Pure price action indicators based on Inner Circle Trader concepts.
"""

import math


def detect_engulfing(candles):
    """
    Detect bullish/bearish engulfing candlestick patterns.
    candles: list of (open, high, low, close) tuples, most recent last
    Returns: dict with type ('bullish'/'bearish'/'none') and strength (0-1)
    """
    if len(candles) < 2:
        return {'type': 'none', 'strength': 0}
    
    prev = candles[-2]
    curr = candles[-1]
    
    prev_open, prev_high, prev_low, prev_close = prev
    curr_open, curr_high, curr_low, curr_close = curr
    
    prev_body = abs(prev_close - prev_open)
    curr_body = abs(curr_close - curr_open)
    
    # Bullish engulfing: prev is bearish (close < open), curr is bullish (close > open)
    # and curr open < prev close, curr close > prev open
    if (prev_close < prev_open and curr_close > curr_open and
            curr_open < prev_close and curr_close > prev_open):
        # Body size relative to average
        avg_body = (prev_body + curr_body) / 2
        if avg_body > 0:
            strength = min(1.0, curr_body / (avg_body * 1.5))
        else:
            strength = 0.5
        return {'type': 'bullish', 'strength': strength}
    
    # Bearish engulfing: prev is bullish, curr is bearish
    if (prev_close > prev_open and curr_close < curr_open and
            curr_open > prev_close and curr_close < prev_open):
        avg_body = (prev_body + curr_body) / 2
        if avg_body > 0:
            strength = min(1.0, curr_body / (avg_body * 1.5))
        else:
            strength = 0.5
        return {'type': 'bearish', 'strength': strength}
    
    return {'type': 'none', 'strength': 0}


def detect_fvg(candles):
    """
    Detect Fair Value Gap (FVG) - bullish or bearish imbalance.
    candles: list of (open, high, low, close) tuples, most recent last
    Returns: dict with type ('bullish'/'bearish'/'none'), gap_top, gap_bottom
    """
    if len(candles) < 3:
        return {'type': 'none', 'gap_top': 0, 'gap_bottom': 0}
    
    candle1 = candles[-3]  # oldest
    candle2 = candles[-2]   # middle
    candle3 = candles[-1]   # most recent
    
    o1, h1, l1, c1 = candle1
    o2, h2, l2, c2 = candle2
    o3, h3, l3, c3 = candle3
    
    # Bullish FVG: candle1 and candle3 don't overlap, gap between them
    # Middle candle (candle2) has a gap below it
    if c3 > c1:  # uptrend context
        gap_bottom = max(l2, l3)
        gap_top = min(h1, h2) if l2 > l3 else l2
        
        # Check if there's actual gap
        if l2 > h3:  # candle2 low is above candle3 high = bullish FVG
            return {'type': 'bullish', 'gap_top': l2, 'gap_bottom': h3}
        if l1 > h2:  # candle1 low is above candle2 high = bullish FVG  
            return {'type': 'bullish', 'gap_top': l1, 'gap_bottom': h2}
    
    # Bearish FVG
    if c3 < c1:  # downtrend context
        if h2 < l3:  # candle2 high is below candle3 low = bearish FVG
            return {'type': 'bearish', 'gap_top': h3, 'gap_bottom': l2}
        if h1 < l2:  # candle1 high is below candle2 low = bearish FVG
            return {'type': 'bearish', 'gap_top': h2, 'gap_bottom': l1}
    
    return {'type': 'none', 'gap_top': 0, 'gap_bottom': 0}


def detect_order_block(candles, direction):
    """
    Detect Order Block - last swing low/high before a strong move.
    candles: list of (open, high, low, close) tuples, most recent last
    direction: 'LONG' or 'SHORT'
    Returns: dict with type ('bullish'/'bearish'/'none'), zone_top, zone_bottom
    """
    if len(candles) < 10:
        return {'type': 'none', 'zone_top': 0, 'zone_bottom': 0}
    
    # Look for the last 5 candles
    recent = candles[-5:]
    
    if direction == "LONG":
        # Bullish order block - candles before a bullish impulse
        # Find a bullish candle with significant body followed by higher highs
        for i in range(len(recent) - 1):
            o, h, l, c = recent[i]
            if c > o and (c - o) > (h - l) * 0.5:  # Bullish candle with body > 50% of range
                # Check if next candles made a move up
                next_closes = [candles[j][3] for j in range(-len(recent)+i+1, 0)]
                if len(next_closes) >= 2 and all(next_closes[k] > next_closes[k-1] for k in range(1, len(next_closes))):
                    return {'type': 'bullish', 'zone_top': h, 'zone_bottom': l}
    
    elif direction == "SHORT":
        # Bearish order block - candles before a bearish impulse
        for i in range(len(recent) - 1):
            o, h, l, c = recent[i]
            if c < o and (o - c) > (h - l) * 0.5:  # Bearish candle with body > 50% of range
                next_closes = [candles[j][3] for j in range(-len(recent)+i+1, 0)]
                if len(next_closes) >= 2 and all(next_closes[k] < next_closes[k-1] for k in range(1, len(next_closes))):
                    return {'type': 'bearish', 'zone_top': h, 'zone_bottom': l}
    
    return {'type': 'none', 'zone_top': 0, 'zone_bottom': 0}


def calc_fib_retracement(candles):
    """
    Calculate Fibonacci retracement levels from recent swing.
    candles: list of (open, high, low, close) tuples, most recent last
    Returns: dict with levels {0.382, 0.5, 0.618, 0.786, 1.0} mapped to prices
    """
    if len(candles) < 20:
        return {}
    
    # Get last 20 candles to find swing high/low
    recent = candles[-20:]
    highs = [c[1] for c in recent]
    lows = [c[2] for c in recent]
    
    swing_high = max(highs)
    swing_low = min(lows)
    
    diff = swing_high - swing_low
    
    if diff == 0:
        return {}
    
    levels = {
        0.382: swing_high - diff * 0.382,
        0.500: swing_high - diff * 0.500,
        0.618: swing_high - diff * 0.618,
        0.786: swing_high - diff * 0.786,
        1.000: swing_low,
    }
    
    return levels


def fib_zone_near_price(candles, current_price, tolerance_pct=2.0):
    """
    Find Fibonacci levels near the current price.
    candles: list of (open, high, low, close) tuples, most recent last
    current_price: current price to check proximity
    tolerance_pct: percentage tolerance (default 2%)
    Returns: dict of levels near price with distance info
    """
    fib_levels = calc_fib_retracement(candles)
    
    if not fib_levels:
        return {}
    
    tolerance = current_price * (tolerance_pct / 100)
    near_levels = {}
    
    for fib_ratio, price in fib_levels.items():
        distance = abs(price - current_price)
        if distance <= tolerance:
            near_levels[fib_ratio] = {
                'price': price,
                'distance_pct': (distance / current_price) * 100
            }
    
    return near_levels


# ═══════════════════════════════════════════════════════════════════════════════
# SMC/ICT ADVANCED INDICATORS (2026-06-15)
# ═══════════════════════════════════════════════════════════════════════════════

def detect_market_structure(candles):
    """
    Detect market structure using swing highs/lows.
    Swing = candle with high/low higher/lower than 2 neighbors on each side.
    
    candles: list of [time, open, high, low, close, volume, ...] (Binance kline format)
    Returns: {'trend': 'bullish'/'bearish'/'ranging', 'swings': [...], 'last_bms': price_or_None}
    """
    if len(candles) < 7:
        return {'trend': 'ranging', 'swings': [], 'last_bms': None}
    
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    closes = [float(c[4]) for c in candles]
    
    # Find swing highs and lows (need 2 candles on each side)
    swing_highs = []
    swing_lows = []
    
    for i in range(2, len(candles) - 2):
        # Swing high: candle i's high is higher than 2 neighbors on each side
        if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2]):
            swing_highs.append({'index': i, 'price': highs[i], 'type': 'high'})
        
        # Swing low: candle i's low is lower than 2 neighbors on each side
        if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and
                lows[i] < lows[i+1] and lows[i] < lows[i+2]):
            swing_lows.append({'index': i, 'price': lows[i], 'type': 'low'})
    
    # Combine and sort by index
    swings = sorted(swing_highs + swing_lows, key=lambda x: x['index'])
    
    if len(swings) < 3:
        return {'trend': 'ranging', 'swings': swings, 'last_bms': None}
    
    # Analyze structure from last 3+ swings
    # Look at last few swing highs and lows separately
    recent_sh = [s for s in swing_highs[-3:]]
    recent_sl = [s for s in swing_lows[-3:]]
    
    trend = 'ranging'
    last_bms = None
    
    # Check for bullish structure: HH + HL
    if len(recent_sh) >= 2 and len(recent_sl) >= 2:
        hh = recent_sh[-1]['price'] > recent_sh[-2]['price']  # Higher High
        hl = recent_sl[-1]['price'] > recent_sl[-2]['price']  # Higher Low
        lh = recent_sh[-1]['price'] < recent_sh[-2]['price']  # Lower High
        ll = recent_sl[-1]['price'] < recent_sl[-2]['price']  # Lower Low
        
        if hh and hl:
            trend = 'bullish'
            last_bms = recent_sh[-1]['price']  # Last Break of Market Structure
        elif lh and ll:
            trend = 'bearish'
            last_bms = recent_sl[-1]['price']
        elif hh and not ll:
            trend = 'bullish'
            last_bms = recent_sh[-1]['price']
        elif lh and not hl:
            trend = 'bearish'
            last_bms = recent_sl[-1]['price']
    
    return {'trend': trend, 'swings': swings, 'last_bms': last_bms}


def detect_liquidity_pools(candles, tolerance=0.005):
    """
    Find equal highs (Buy-Side Liquidity) and equal lows (Sell-Side Liquidity).
    Equal highs/lows = swing points within tolerance% of each other.
    
    candles: list of [time, open, high, low, close, volume, ...]
    tolerance: percentage tolerance for "equal" (default 0.5%)
    Returns: {'bsl': [prices], 'ssl': [prices], 'bsl_count': N, 'ssl_count': N}
    """
    if len(candles) < 10:
        return {'bsl': [], 'ssl': [], 'bsl_count': 0, 'ssl_count': 0}
    
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    
    # Find local highs and lows (simple: higher/lower than 1 neighbor each side)
    local_highs = []
    local_lows = []
    
    for i in range(1, len(candles) - 1):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            local_highs.append(highs[i])
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            local_lows.append(lows[i])
    
    # Cluster equal highs (BSL - Buy-Side Liquidity)
    bsl = []
    used_h = set()
    for i in range(len(local_highs)):
        if i in used_h:
            continue
        cluster = [local_highs[i]]
        for j in range(i + 1, len(local_highs)):
            if j in used_h:
                continue
            if abs(local_highs[i] - local_highs[j]) / local_highs[i] <= tolerance:
                cluster.append(local_highs[j])
                used_h.add(j)
        if len(cluster) >= 2:
            bsl.append(sum(cluster) / len(cluster))  # Average of cluster
        used_h.add(i)
    
    # Cluster equal lows (SSL - Sell-Side Liquidity)
    ssl = []
    used_l = set()
    for i in range(len(local_lows)):
        if i in used_l:
            continue
        cluster = [local_lows[i]]
        for j in range(i + 1, len(local_lows)):
            if j in used_l:
                continue
            if abs(local_lows[i] - local_lows[j]) / local_lows[i] <= tolerance:
                cluster.append(local_lows[j])
                used_l.add(j)
        if len(cluster) >= 2:
            ssl.append(sum(cluster) / len(cluster))
        used_l.add(i)
    
    return {'bsl': bsl, 'ssl': ssl, 'bsl_count': len(bsl), 'ssl_count': len(ssl)}


def calc_impulse_system(closes, period=13):
    """
    Elder's Impulse System: combines 13 EMA slope + MACD histogram slope.
    GREEN: both rising (strong bull)
    RED: both falling (strong bear)
    BLUE: mixed (consolidation/reversal warning)
    
    closes: list of close prices
    period: EMA period (default 13)
    Returns: {'signal': 'GREEN'/'RED'/'BLUE', 'ema_slope': float, 'macd_hist_slope': float}
    """
    if len(closes) < period + 10:
        return {'signal': 'BLUE', 'ema_slope': 0, 'macd_hist_slope': 0}
    
    # Calculate EMA
    def ema(data, p):
        k = 2 / (p + 1)
        result = [data[0]]
        for price in data[1:]:
            result.append(price * k + result[-1] * (1 - k))
        return result
    
    ema_series = ema(closes, period)
    ema_slope = ema_series[-1] - ema_series[-2] if len(ema_series) >= 2 else 0
    
    # MACD histogram
    ema_12 = ema(closes, 12)
    ema_26 = ema(closes, 26)
    macd_line = [f - s for f, s in zip(ema_12, ema_26)]
    signal_line = ema(macd_line, 9)
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    
    hist_slope = histogram[-1] - histogram[-2] if len(histogram) >= 2 else 0
    
    # Determine impulse signal
    if ema_slope > 0 and hist_slope > 0:
        signal = 'GREEN'
    elif ema_slope < 0 and hist_slope < 0:
        signal = 'RED'
    else:
        signal = 'BLUE'
    
    return {'signal': signal, 'ema_slope': ema_slope, 'macd_hist_slope': hist_slope}


def detect_amd_cycle(candles):
    """
    Detect Accumulation-Manipulation-Distribution cycle.
    Accumulation: tight range (<60% of prior range)
    Manipulation: false breakout from range
    Distribution: real directional move
    
    candles: list of [time, open, high, low, close, volume, ...]
    Returns: {'phase': 'accumulation'/'manipulation'/'distribution'/'none', 'range_pct': float}
    """
    if len(candles) < 10:
        return {'phase': 'none', 'range_pct': 0}
    
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    closes = [float(c[4]) for c in candles]
    
    # Split into older half and recent half
    mid = len(candles) // 2
    older_range = max(highs[:mid]) - min(lows[:mid]) if mid > 0 else 1
    recent_range = max(highs[mid:]) - min(lows[mid:]) if mid < len(candles) else 1
    
    if older_range == 0:
        return {'phase': 'none', 'range_pct': 0}
    
    range_pct = (recent_range / older_range) * 100
    
    # Recent candles analysis
    recent_closes = closes[mid:]
    recent_highs = highs[mid:]
    recent_lows = lows[mid:]
    
    # Check for recent breakout
    older_high = max(highs[:mid])
    older_low = min(lows[:mid])
    
    last_close = closes[-1]
    last_3_closes = closes[-3:]
    
    # Accumulation: tight range
    if range_pct < 60:
        return {'phase': 'accumulation', 'range_pct': range_pct}
    
    # Manipulation: false breakout (broke range but reversed)
    broke_high = any(h > older_high for h in recent_highs[-3:])
    broke_low = any(l < older_low for l in recent_lows[-3:])
    reversed_back = (broke_high and last_close < older_high) or (broke_low and last_close > older_low)
    
    if (broke_high or broke_low) and reversed_back:
        return {'phase': 'manipulation', 'range_pct': range_pct}
    
    # Distribution: real move (broke and holding)
    if broke_high and last_close > older_high:
        return {'phase': 'distribution', 'range_pct': range_pct}
    if broke_low and last_close < older_low:
        return {'phase': 'distribution', 'range_pct': range_pct}
    
    return {'phase': 'none', 'range_pct': range_pct}


def detect_turtle_soup(candles, tolerance=0.005):
    """
    Detect Turtle Soup pattern: false breakout above/below liquidity then reversal.
    Like a stop hunt — price sweeps highs/lows then reverses sharply.
    
    candles: list of [time, open, high, low, close, volume, ...]
    tolerance: price tolerance for sweep (default 0.5%)
    Returns: {'type': 'long'/'short'/'none', 'sweep_price': float, 'reversal_confirmed': bool}
    """
    if len(candles) < 8:
        return {'type': 'none', 'sweep_price': 0, 'reversal_confirmed': False}
    
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    opens = [float(c[1]) for c in candles]
    closes = [float(c[4]) for c in candles]
    
    # Find recent range high/low (last 5-10 candles before the last 2)
    range_start = max(0, len(candles) - 8)
    range_end = len(candles) - 2
    range_high = max(highs[range_start:range_end])
    range_low = min(lows[range_start:range_end])
    
    if range_high == 0 or range_low == 0:
        return {'type': 'none', 'sweep_price': 0, 'reversal_confirmed': False}
    
    last = candles[-1]
    prev = candles[-2]
    last_high = float(last[2])
    last_low = float(last[3])
    last_close = float(last[4])
    last_open = float(last[1])
    prev_high = float(prev[2])
    prev_low = float(prev[3])
    prev_close = float(prev[4])
    
    # Long Turtle Soup: sweep below range_low, then close back above
    sweep_low = last_low < range_low * (1 - tolerance) or prev_low < range_low * (1 - tolerance)
    if sweep_low:
        sweep_price = min(last_low, prev_low)
        # Reversal confirmed: last candle closed back above range low + is bullish
        if last_close > range_low and last_close > last_open:
            return {'type': 'long', 'sweep_price': sweep_price, 'reversal_confirmed': True}
        elif last_close > range_low or prev_close > range_low:
            return {'type': 'long', 'sweep_price': sweep_price, 'reversal_confirmed': False}
    
    # Short Turtle Soup: sweep above range_high, then close back below
    sweep_high = last_high > range_high * (1 + tolerance) or prev_high > range_high * (1 + tolerance)
    if sweep_high:
        sweep_price = max(last_high, prev_high)
        if last_close < range_high and last_close < last_open:
            return {'type': 'short', 'sweep_price': sweep_price, 'reversal_confirmed': True}
        elif last_close < range_high or prev_close < range_high:
            return {'type': 'short', 'sweep_price': sweep_price, 'reversal_confirmed': False}
    
    return {'type': 'none', 'sweep_price': 0, 'reversal_confirmed': False}
