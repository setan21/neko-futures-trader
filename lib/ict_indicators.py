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
