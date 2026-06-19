#!/usr/bin/env python3
"""Test SMC/ICT functions"""
from ict_indicators import (
    detect_market_structure, detect_liquidity_pools, detect_order_block,
    detect_fvg, calc_fib_retracement, fib_zone_near_price,
    calc_impulse_system, detect_amd_cycle, detect_turtle_soup, detect_engulfing
)
from smc_scoring import calculate_smc_bonus
import random

# Generate mock candles in Binance kline format [time, open, high, low, close, vol]
random.seed(42)
price = 100.0
mock_1h = []
for i in range(50):
    o = price
    c = price + random.uniform(-2, 2.5)
    h = max(o, c) + random.uniform(0, 1)
    l = min(o, c) - random.uniform(0, 1)
    v = random.uniform(1000, 5000)
    mock_1h.append([1000000 + i*3600, o, h, l, c, v])
    price = c

price2 = 100.0
mock_4h = []
for i in range(50):
    o = price2
    c = price2 + random.uniform(-3, 3)
    h = max(o, c) + random.uniform(0, 1.5)
    l = min(o, c) - random.uniform(0, 1.5)
    v = random.uniform(5000, 20000)
    mock_4h.append([1000000 + i*14400, o, h, l, c, v])
    price2 = c

# Test individual functions
print("=== Individual Function Tests ===")
ms = detect_market_structure(mock_1h)
print(f"Market Structure: trend={ms['trend']}, swings={len(ms['swings'])}")

liq = detect_liquidity_pools(mock_4h)
print(f"Liquidity Pools: BSL={liq['bsl_count']}, SSL={liq['ssl_count']}")

imp = calc_impulse_system([float(c[4]) for c in mock_4h])
print(f"Impulse System: signal={imp['signal']}")

amd = detect_amd_cycle(mock_1h)
print(f"AMD Cycle: phase={amd['phase']}, range_pct={amd['range_pct']:.1f}%")

ts = detect_turtle_soup(mock_1h)
print(f"Turtle Soup: type={ts['type']}")

# Test SMC bonus calculation
print("\n=== SMC Bonus Test ===")
current_price = float(mock_1h[-1][4])
bonus, details = calculate_smc_bonus(mock_1h, mock_4h, "LONG", current_price)
print(f"LONG bonus: {bonus}")
for k, v in details.items():
    print(f"  {k}: {v}")

bonus2, details2 = calculate_smc_bonus(mock_1h, mock_4h, "SHORT", current_price)
print(f"\nSHORT bonus: {bonus2}")
for k, v in details2.items():
    print(f"  {k}: {v}")

# Edge case tests
print("\n=== Edge Case Tests ===")
b, d = calculate_smc_bonus([], [], "LONG", 100)
print(f"Empty candles: bonus={b}, details={d}")

b, d = calculate_smc_bonus(mock_1h[:5], mock_4h[:3], "SHORT", 100)
print(f"Insufficient data: bonus={b}, details={d}")

b, d = calculate_smc_bonus(mock_1h, mock_4h, "LONG", 0)
print(f"Zero price: bonus={b}, details={d}")

print("\n=== All tests passed! ===")
