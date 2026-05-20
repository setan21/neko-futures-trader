# Changelog

All notable changes are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) ·
Versioning: [SemVer](https://semver.org/spec/v2.0.0.html)

## [1.4.0] — 2026-05-19

### ✨ Features
- Bear-market SHORT filters: direction-conflict allowed, RSI guard 35→15, MACD-flat exception with vol ≥ 1.0x (`ee79965`)
- 30-bar **range position** protection — LONG rejected if range_pos > 70% (crypto) / 85% (TradFi); SHORT rejected if range_pos < 30% (crypto) / 15% (TradFi). Skipped when |price_change| > 7% (`ee79965`)
- Result: WR jumped 19% → 67% on next batch

### 📝 Docs
- README full rewrite to portfolio-grade structure (`7d55fa5`)
- README accuracy audit — 13 corrections (scan interval 60s, LLM order, coin coverage, project tree, pipeline) (`ea8222b`)
- `AI_CONTRIBUTORS.md` — transparent AI-assistance attribution (`c811db2`)
- `.github/git-commit-template.txt` — Co-Authored-By trailer for AI credit (`c811db2`)
- `SKILL.md` rewrite — match actual code, paths, params; added pitfalls + diagnosis playbook

## [1.3.0] — 2026-05-18

### ✨ Features
- Dynamic coin universe (Binance API, $2M min volume), replacing static `SAFE_COINS` (`3a4c462`)
- BTC regime check — skip crypto LONGs when BTC 4H EMA9 < EMA21
- EMA9/21 strong-trend filter — LONG needs EMA9 > EMA21 (and inverse for SHORT)
- 48h loss cooldown / 24h win cooldown
- `MAX_DAILY_LOSS=-30` USDT auto-stop

### 🐛 Fixes
- Tightened SL 5% → **3%**, TP 15% → **8%** (realistic targets, higher hit rate)
- `MIN_VOLUME_RATIO` 1.0 → **1.5** (entries at <1x vol were all losers)
- `CHASE_LIMIT_CRYPTO` 6% → **4%**, `CHASE_LIMIT_TRADFI` 8% → **5%** (NO EXCEPTION)
- `MIN_SCORE_NORMAL` back to **7** (6 produced 22% WR, -$117)
- Removed >15% breakout chase exception (caused FIDA -$65)

## [1.2.0] — 2026-05-13

### ✨ Features
- Re-enabled LLM gate with relaxed anti-chasing (3% → 5%)
- Crypto index perps: `BTCDOMUSDT`, `ALLUSDT` (`af1b0c5`)
- TradFi-tuned filters for stocks/commodities/indices (`0a60ce1`)
- Delisting monitor + TradFi whitelist (`1a45279`)

## [1.1.0] — 2026-05-06

### 🐛 Fixes
- Disabled LLM gate temporarily (was rejecting 98.5% of valid signals) (`9cbd1a1`)
- Trailing TP pullback detection — don't close immediately on activation (`3955012`)
- SL+ protection overhaul: trailing SL order fix, auto-calc missing SL/TP, persist state (`99fdbfa`)
- MACD calculation + volume ratio + anti-chasing filter (`ffb6380`)

## [1.0.0] — 2026-04-21

### ✨ Features
- Hybrid AI gate + trailing SL + path migration (`6b6ec7e`)
- EMA 9/21 crossover scanner + funding rate monitoring (`6f51819`)
- Multi-timeframe analysis, partial TPs, top-trader ratio (`3aa442e`)
- Algo-order migration (`/fapi/v1/algoOrder`) (`3db07e5`)
- MARKET entry + separate SL/TP (replaces batch orders) (`b50912e`)

### 🎨 UI
- Glassmorphism dashboard, sparklines, dark/light theme

---

*Manually maintained. Use the `Co-Authored-By` trailer (`.github/git-commit-template.txt`) on every commit so AI contributions stay attributable.*
