"""
SMC/ICT Confluence Scoring Module (2026-06-15)
Calculates bonus points based on Smart Money Concepts alignment.
Adds 0-8 bonus points to existing scanner scores.
"""

from ict_indicators import (
    detect_market_structure,
    detect_liquidity_pools,
    detect_order_block,
    detect_fvg,
    calc_fib_retracement,
    fib_zone_near_price,
    calc_impulse_system,
    detect_amd_cycle,
    detect_turtle_soup,
    detect_engulfing,
)


def calculate_smc_bonus(candles_1h, candles_4h, direction, current_price):
    """
    Calculate SMC/ICT confluence bonus score (0-8 points).
    
    Checks:
    1. Market Structure alignment (+2): 1H structure matches direction
    2. Impulse System alignment (+2): GREEN for LONG, RED for SHORT on 4H
    3. Order Block proximity (+1): price near fresh OB
    4. FVG confluence (+1): price near unfilled FVG
    5. Liquidity pool setup (+1): SSL below for LONG, BSL above for SHORT
    6. Fibonacci OTE zone (+1): price in 0.382-0.618 retracement
    
    Args:
        candles_1h: 1H candles in Binance kline format [time, open, high, low, close, vol, ...]
        candles_4h: 4H candles in Binance kline format
        direction: 'LONG' or 'SHORT'
        current_price: current price
    
    Returns: (bonus_score: int, details: dict)
    """
    bonus = 0
    details = {}
    
    # ── Safety: handle insufficient data ──
    if not candles_1h or len(candles_1h) < 10:
        return 0, {'error': 'insufficient_1h_data'}
    if not candles_4h or len(candles_4h) < 5:
        return 0, {'error': 'insufficient_4h_data'}
    if current_price <= 0:
        return 0, {'error': 'invalid_price'}
    
    try:
        # === 1. MARKET STRUCTURE ALIGNMENT (+2) ===
        structure = detect_market_structure(candles_1h)
        struct_trend = structure.get('trend', 'ranging')
        
        if direction == 'LONG' and struct_trend == 'bullish':
            bonus += 2
            details['structure'] = '+2 (1H bullish structure aligned)'
        elif direction == 'SHORT' and struct_trend == 'bearish':
            bonus += 2
            details['structure'] = '+2 (1H bearish structure aligned)'
        elif struct_trend == 'ranging':
            details['structure'] = '+0 (1H ranging — no structure edge)'
        else:
            details['structure'] = f'+0 (1H {struct_trend} vs {direction} — counter-structure)'
    except Exception as e:
        details['structure'] = f'error: {e}'
    
    try:
        # === 2. IMPULSE SYSTEM ALIGNMENT (+2) ===
        h4_closes = [float(c[4]) for c in candles_4h]
        impulse = calc_impulse_system(h4_closes, period=13)
        impulse_signal = impulse.get('signal', 'BLUE')
        
        if direction == 'LONG' and impulse_signal == 'GREEN':
            bonus += 2
            details['impulse'] = '+2 (4H GREEN impulse — both EMA & MACD rising)'
        elif direction == 'SHORT' and impulse_signal == 'RED':
            bonus += 2
            details['impulse'] = '+2 (4H RED impulse — both EMA & MACD falling)'
        elif impulse_signal == 'BLUE':
            details['impulse'] = '+0 (4H BLUE impulse — mixed signals)'
        else:
            details['impulse'] = f'+0 (4H {impulse_signal} vs {direction} — counter-impulse)'
    except Exception as e:
        details['impulse'] = f'error: {e}'
    
    try:
        # === 3. ORDER BLOCK PROXIMITY (+1) ===
        # Convert klines to OHLC tuples for ict_indicators functions
        ohlc_1h = [(float(c[1]), float(c[2]), float(c[3]), float(c[4])) for c in candles_1h]
        ob = detect_order_block(ohlc_1h, direction)
        
        if ob.get('type') != 'none':
            zone_top = ob.get('zone_top', 0)
            zone_bottom = ob.get('zone_bottom', 0)
            if zone_top > 0 and zone_bottom > 0:
                # Check if current price is near or inside the OB zone
                ob_mid = (zone_top + zone_bottom) / 2
                ob_size = zone_top - zone_bottom
                price_dist = abs(current_price - ob_mid)
                # Price within 2x OB zone size = near
                if price_dist <= ob_size * 2 if ob_size > 0 else False:
                    bonus += 1
                    details['order_block'] = f'+1 (price near {ob["type"]} OB: {zone_bottom:.4f}-{zone_top:.4f})'
                else:
                    details['order_block'] = '+0 (OB exists but price not near)'
            else:
                details['order_block'] = '+0 (OB detected but invalid zone)'
        else:
            details['order_block'] = '+0 (no OB detected)'
    except Exception as e:
        details['order_block'] = f'error: {e}'
    
    try:
        # === 4. FVG CONFLUENCE (+1) ===
        # Check both 1H and 4H for FVG
        ohlc_4h = [(float(c[1]), float(c[2]), float(c[3]), float(c[4])) for c in candles_4h]
        
        fvg_1h = detect_fvg(ohlc_1h)
        fvg_4h = detect_fvg(ohlc_4h)
        
        fvg_found = False
        for label, fvg in [('1H', fvg_1h), ('4H', fvg_4h)]:
            if fvg.get('type') != 'none':
                gap_top = fvg.get('gap_top', 0)
                gap_bottom = fvg.get('gap_bottom', 0)
                if gap_top > 0 and gap_bottom > 0:
                    # Check if price is inside or near FVG
                    if gap_bottom <= current_price <= gap_top:
                        bonus += 1
                        details['fvg'] = f'+1 (price inside {fvg["type"]} FVG on {label}: {gap_bottom:.4f}-{gap_top:.4f})'
                        fvg_found = True
                        break
                    # Price within 1% of FVG
                    dist_to_fvg = min(abs(current_price - gap_top), abs(current_price - gap_bottom))
                    if dist_to_fvg / current_price < 0.01:
                        bonus += 1
                        details['fvg'] = f'+1 (price near {fvg["type"]} FVG on {label}: {gap_bottom:.4f}-{gap_top:.4f})'
                        fvg_found = True
                        break
        
        if not fvg_found:
            details['fvg'] = '+0 (no actionable FVG)'
    except Exception as e:
        details['fvg'] = f'error: {e}'
    
    try:
        # === 5. LIQUIDITY POOL SETUP (+1) ===
        # Use 4H candles for liquidity pools (more reliable)
        liq = detect_liquidity_pools(candles_4h, tolerance=0.005)
        
        if direction == 'LONG':
            # For LONG: want SSL (sell-side liquidity) below — stop hunts below → reversal up
            ssl_below = [p for p in liq.get('ssl', []) if p < current_price]
            if ssl_below:
                nearest_ssl = max(ssl_below)  # Nearest SSL below
                dist_pct = (current_price - nearest_ssl) / current_price * 100
                if dist_pct < 3:  # Within 3%
                    bonus += 1
                    details['liquidity'] = f'+1 (SSL below at {nearest_ssl:.4f}, {dist_pct:.1f}% away)'
                else:
                    details['liquidity'] = f'+0 (SSL too far: {dist_pct:.1f}%)'
            else:
                details['liquidity'] = '+0 (no SSL below)'
        else:  # SHORT
            # For SHORT: want BSL (buy-side liquidity) above — stop hunts above → reversal down
            bsl_above = [p for p in liq.get('bsl', []) if p > current_price]
            if bsl_above:
                nearest_bsl = min(bsl_above)  # Nearest BSL above
                dist_pct = (nearest_bsl - current_price) / current_price * 100
                if dist_pct < 3:
                    bonus += 1
                    details['liquidity'] = f'+1 (BSL above at {nearest_bsl:.4f}, {dist_pct:.1f}% away)'
                else:
                    details['liquidity'] = f'+0 (BSL too far: {dist_pct:.1f}%)'
            else:
                details['liquidity'] = '+0 (no BSL above)'
    except Exception as e:
        details['liquidity'] = f'error: {e}'
    
    try:
        # === 6. FIBONACCI OTE ZONE (+1) ===
        # Optimal Trade Entry: 0.382 - 0.618 retracement zone
        fib_levels = calc_fib_retracement(ohlc_1h)
        
        if fib_levels and 0.382 in fib_levels and 0.618 in fib_levels:
            fib_382 = fib_levels[0.382]
            fib_618 = fib_levels[0.618]
            
            if direction == 'LONG':
                # For LONG (retracement down from high): price between 0.382 and 0.618
                ote_low = min(fib_382, fib_618)
                ote_high = max(fib_382, fib_618)
                if ote_low <= current_price <= ote_high:
                    bonus += 1
                    details['fib_ote'] = f'+1 (price in OTE zone: {ote_low:.4f}-{ote_high:.4f})'
                else:
                    details['fib_ote'] = '+0 (price outside OTE zone)'
            elif direction == 'SHORT':
                # For SHORT: price in upper retracement zone
                ote_low = min(fib_382, fib_618)
                ote_high = max(fib_382, fib_618)
                if ote_low <= current_price <= ote_high:
                    bonus += 1
                    details['fib_ote'] = f'+1 (price in OTE zone: {ote_low:.4f}-{ote_high:.4f})'
                else:
                    details['fib_ote'] = '+0 (price outside OTE zone)'
        else:
            details['fib_ote'] = '+0 (insufficient data for Fibonacci)'
    except Exception as e:
        details['fib_ote'] = f'error: {e}'
    
    return bonus, details
