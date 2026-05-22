#!/usr/bin/env python3
"""
LLM Analyzer — Second opinion layer for Neko Scanner
Cheap, fast LLM check before trade execution.
Uses Nous + 9router + MiniMax (default: openai/gpt-4o-mini)

FALLBACK: When all LLM providers fail, uses rule_based_backup() instead of
fail-open. Rules are strictly derived from technical indicators.
"""

import os
import json
import re

# Load .env at import time so API keys are populated regardless of import order.
# Fixes the "import-before-.env-load" silent LLM kill bug (2026-05-22):
# scanner.py imports this module at line 18, but its inline .env loader runs at
# line 45 — so module-level os.environ.get(...) calls below would return empty
# strings without this load_dotenv() call.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    # python-dotenv not installed — fall back to manual parse
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.isfile(_env_path):
        try:
            with open(_env_path) as _f:
                for _line in _f:
                    _line = _line.strip()
                    if not _line or _line.startswith("#") or "=" not in _line:
                        continue
                    _k, _v = _line.split("=", 1)
                    _k = _k.strip()
                    _v = _v.strip().strip('"').strip("'")
                    if _k and _k not in os.environ:
                        os.environ[_k] = _v
        except Exception:
            pass
import time
import requests

# === CONFIG (override from config.py if available) ===
try:
    from config import (LLM_ENABLED, LLM_MODEL, LLM_BASE_URL, LLM_MIN_SCORE,
                        LLM_TEMPERATURE, LLM_FALLBACK1_ENABLED,
                        LLM_FALLBACK1_BASE_URL, LLM_FALLBACK1_MODEL,
                        LLM_FALLBACK2_ENABLED,
                        LLM_FALLBACK2_BASE_URL, LLM_FALLBACK2_MODEL,
                        LLM_BACKUP_MODE, LLM_BACKUP_MIN_SCORE,
                        LLM_BACKUP_MAX_CHASE, LLM_BACKUP_MAX_RSI_LONG,
                        LLM_BACKUP_MIN_RSI_LONG, LLM_BACKUP_MAX_RSI_SHORT,
                        LLM_BACKUP_MIN_RSI_SHORT, LLM_BACKUP_MIN_VOL_RATIO,
                        LLM_BACKUP_MAX_FUNDING_LONG, LLM_BACKUP_MAX_FUNDING_SHORT)
except ImportError:
    LLM_ENABLED = True
    LLM_MODEL = "xiaomi/mimo-v2-pro"
    LLM_BASE_URL = "https://inference-api.nousresearch.com/v1/chat/completions"
    LLM_MIN_SCORE = 4
    LLM_TEMPERATURE = 0.1
    LLM_FALLBACK1_ENABLED = True
    LLM_FALLBACK1_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    LLM_FALLBACK1_MODEL = "nousresearch/hermes-4-70b"
    LLM_FALLBACK2_ENABLED = True
    LLM_FALLBACK2_BASE_URL = "https://api.minimaxi.chat/v1/chat/completions"
    LLM_FALLBACK2_MODEL = "MiniMax-M2.5"
    LLM_BACKUP_MODE = "rule_based"     # "rule_based" | "fail_open" | "fail_closed"
    LLM_BACKUP_MIN_SCORE = 8           # Higher bar than normal MIN_SCORE
    LLM_BACKUP_MAX_CHASE = 5.0         # Max % change before rejecting (chase filter)
    LLM_BACKUP_MAX_RSI_LONG = 68.0     # Reject LONG if RSI above this
    LLM_BACKUP_MIN_RSI_LONG = 30.0     # Reject LONG if RSI below this (falling knife)
    LLM_BACKUP_MAX_RSI_SHORT = 78.0    # Reject SHORT if RSI above this (too overbought)
    LLM_BACKUP_MIN_RSI_SHORT = 32.0    # Reject SHORT if RSI below this (oversold)
    LLM_BACKUP_MIN_VOL_RATIO = 1.0     # Minimum volume ratio
    LLM_BACKUP_MAX_FUNDING_LONG = 0.08 # Max funding rate for LONG (%)
    LLM_BACKUP_MAX_FUNDING_SHORT = -0.08  # Max funding rate for SHORT (%)

# Load API keys from env
LLM_API_KEY = os.environ.get("NOUS_API_KEY", "")
LLM_FALLBACK1_API_KEY = os.environ.get("9ROUTER_API_KEY", "")
LLM_FALLBACK2_API_KEY = os.environ.get("MINIMAX_API_KEY", "")

# === CACHE ===
_analysis_cache = {}
CACHE_TTL = 300  # 5 min cache


def _get_cache_key(symbol, direction, score):
    return f"{symbol}:{direction}:{score}"


def _is_cache_valid(key):
    if key in _analysis_cache:
        entry = _analysis_cache[key]
        return (time.time() - entry['ts']) < CACHE_TTL
    return False


def format_analysis_prompt(analysis):
    """Build a concise prompt from analysis dict."""

    sym = analysis.get('symbol', 'UNKNOWN')
    direction = analysis.get('direction', 'LONG')
    score = analysis.get('runner_score', 0)

    prompt = f"""Analyze this crypto futures {direction} signal for {sym}.

TECHNICAL DATA:
- Price: ${analysis.get('current', 0):.6f}
- 24h Change: {analysis.get('price_change', 0):+.2f}%
- 1h Momentum: {analysis.get('change_1h', 0):+.2f}%
- RSI(14): {analysis.get('rsi', 50):.1f}
- MACD Histogram: {analysis.get('macd_histogram', 0):+.4f}
- EMA21: {analysis.get('ema_21', 0):.6f} | EMA50: {analysis.get('ema_50', 0):.6f}
- ATR%: {analysis.get('atr_pct', 0):.2f}%
- Volume Ratio: {analysis.get('vol_ratio', 1):.1f}x avg
- Open Interest Change: {analysis.get('oi_change', 0):+.1f}%
- Funding Rate: {analysis.get('funding_rate', 0):.4f}%
- Trend: {analysis.get('trend', 'N/A')} | Structure: {analysis.get('structure', 'N/A')}
- Breakout: {'Yes' if analysis.get('breakout') else 'No'}
- Weekly Change: {analysis.get('weekly_change', 0):+.1f}%
- Score: {score}/19
- SL: ${analysis.get('sl', 0):.6f} | TP: ${analysis.get('tp1', 0):.6f}
- SL Method: {analysis.get('sl_method', 'PRICE')}

|RULES:
1. Is this a good {direction} entry RIGHT NOW?
2. Is momentum aligned? (1h and 24h should agree with direction)
3. For LONG: RSI 30-65 is ACCEPTABLE (40-60 optimal, 30-40 and 60-65 valid). For SHORT: RSI 40-70 is VALID (dropping from high), only reject if RSI < 30
4. Is the SL reasonable (not too tight, not too wide)?
5. Any red flags? (funding extreme, divergence, exhaustion)
6. For SHORT: If price_change < -3%, momentum drop is real — approve if other indicators align
7. ANTI-CHASING: If price_change > 5% (LONG) or < -5% (SHORT), the move is already extended — REJECT unless strong reversal setup

Reply in JSON ONLY:
{{"decision": "YES" or "NO", "confidence": 0.0-1.0, "reason": "one line reason"}}
"""
    return prompt


def _do_api_call(url, api_key, model, payload, timeout, max_retries=2):
    """Make a single API call with retry on rate limit (429). Returns response dict or None."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    for attempt in range(max_retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content')
                if not content:
                    # Model used reasoning field instead of content (e.g. xiaomi/mimo)
                    reasoning = data.get('choices', [{}])[0].get('message', {}).get('reasoning', '')
                    if reasoning:
                        # Try to extract JSON from reasoning
                        content = reasoning
                    else:
                        return None
                usage = data.get('usage', {})
                # Strip MiniMax/other thinking tags
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                return {
                    'content': content,
                    'tokens_in': usage.get('prompt_tokens', 0),
                    'tokens_out': usage.get('completion_tokens', 0),
                }
            elif r.status_code == 429:
                # Rate limited — parse retry-after if available
                retry_after = int(r.headers.get('Retry-After', 3 * (attempt + 1)))
                if attempt < max_retries:
                    print(f"  ⏳ Rate limited ({url.split('/')[2]}), retry in {retry_after}s... (attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"  ⚠️ Rate limited ({url.split('/')[2]}), max retries exceeded")
                    return None
            else:
                print(f"  ⚠️ LLM API error ({url.split('/')[2]}): {r.status_code} — {r.text[:100]}")
                return None
        except requests.Timeout:
            if attempt < max_retries:
                print(f"  ⏳ LLM timeout ({url.split('/')[2]}), retrying... (attempt {attempt+1}/{max_retries})")
                time.sleep(2 * (attempt + 1))
                continue
            print(f"  ⚠️ LLM timeout ({url.split('/')[2]})")
            return None
        except Exception as e:
            print(f"  ⚠️ LLM error ({url.split('/')[2]}): {e}")
            return None
    return None


def call_llm(prompt, model=None, timeout=15):
    """Call LLM with 3-tier fallback: Nous → OpenRouter → MiniMax."""

    model = model or LLM_MODEL
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a crypto futures trading analyst. "
                    "For LONG entries: RSI 30-65 is ACCEPTABLE (not suboptimal), >70 is risky. "
                    "RSI 40-60 is optimal for LONG, RSI 30-40 and 60-65 are still valid. "
                    "For SHORT entries: RSI 40-70 is NORMAL (coin dropping from high), "
                    "do NOT reject SHORT just because RSI > 60 — that's where short setups happen. "
                    "Only reject SHORT if RSI < 30 (oversold, too late). "
                    "Be balanced — approve setups with clear momentum alignment. "
                    "During market-wide drops (price_change < -3%), SHORT signals are VALID even with higher RSI. "
                    "CRITICAL: Reject if price has already moved >3% in the signal direction (chasing extended moves). "
                    "Respond ONLY with valid JSON, no markdown."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": LLM_TEMPERATURE,
        "max_tokens": 300,
    }

    # ── Tier 1: Nous Research (Primary) ──────────────────────────────────
    if LLM_API_KEY:
        print(f"  🧠 LLM → Nous ({model})...")
        result = _do_api_call(LLM_BASE_URL, LLM_API_KEY, model, payload, timeout)
        if result:
            result['provider'] = 'nous'
            return result
        print("  ⚠️ Nous failed, trying OpenRouter...")
    else:
        print("  ⚠️ No Nous API key, skipping primary...")

    # ── Tier 2: OpenRouter (Fallback 1) ──────────────────────────────────
    if LLM_FALLBACK1_ENABLED and LLM_FALLBACK1_API_KEY:
        fb1_model = LLM_FALLBACK1_MODEL
        payload_fb1 = {**payload, "model": fb1_model}
        print(f"  🧠 LLM → 9router ({fb1_model})...")
        result = _do_api_call(LLM_FALLBACK1_BASE_URL, LLM_FALLBACK1_API_KEY,
                              fb1_model, payload_fb1, timeout)
        if result:
            result['provider'] = 'openrouter'
            return result
        print("  ⚠️ 9router failed, trying MiniMax...")
    else:
        print("  ⚠️ 9router disabled or no key, skipping...")

    # ── Tier 3: MiniMax (Fallback 2) ─────────────────────────────────────
    if LLM_FALLBACK2_ENABLED and LLM_FALLBACK2_API_KEY:
        fb2_model = LLM_FALLBACK2_MODEL
        payload_fb2 = {**payload, "model": fb2_model}
        print(f"  🧠 LLM → MiniMax ({fb2_model})...")
        result = _do_api_call(LLM_FALLBACK2_BASE_URL, LLM_FALLBACK2_API_KEY,
                              fb2_model, payload_fb2, timeout)
        if result:
            result['provider'] = 'minimax'
            return result
        print("  ⚠️ MiniMax also failed")
    else:
        print("  ⚠️ MiniMax disabled or no key")

    return None


def rule_based_backup(analysis):
    """
    Rule-based backup analyzer — fires when ALL LLM providers are down.
    Uses technical indicators already available in the analysis dict.
    Much more conservative than fail-open: requires alignment across
    multiple indicators to approve a trade.

    Returns dict with same shape as LLM result: approved, reason, model, etc.
    """
    symbol = analysis.get('symbol', '?')
    direction = analysis.get('direction', 'LONG')
    score = analysis.get('runner_score', 0)
    price_change = analysis.get('price_change', 0)
    change_1h = analysis.get('change_1h', 0)
    rsi = analysis.get('rsi', 50)
    vol_ratio = analysis.get('vol_ratio', 0)
    funding = analysis.get('funding_rate', 0)
    ema_21 = analysis.get('ema_21', 0)
    ema_50 = analysis.get('ema_50', 0)
    current = analysis.get('current', 0)
    macd_hist = analysis.get('macd_histogram', 0)
    oi_change = analysis.get('oi_change', 0)
    trend = analysis.get('trend', 'N/A')
    breakout = analysis.get('breakout', False)

    reasons = []

    # ── Gate 1: Score threshold (higher bar than normal) ─────────────────
    if score < LLM_BACKUP_MIN_SCORE:
        return _backup_reject(symbol, direction,
            f"Score {score} < backup min {LLM_BACKUP_MIN_SCORE}")

    # ── Gate 2: Anti-chase ───────────────────────────────────────────────
    if direction == 'LONG' and price_change > LLM_BACKUP_MAX_CHASE:
        return _backup_reject(symbol, direction,
            f"Chase LONG: +{price_change:.1f}% > {LLM_BACKUP_MAX_CHASE}%")
    if direction == 'SHORT' and price_change < -LLM_BACKUP_MAX_CHASE:
        return _backup_reject(symbol, direction,
            f"Chase SHORT: {price_change:.1f}% < -{LLM_BACKUP_MAX_CHASE}%")

    # ── Gate 3: RSI bounds ───────────────────────────────────────────────
    if direction == 'LONG':
        if rsi > LLM_BACKUP_MAX_RSI_LONG:
            return _backup_reject(symbol, direction,
                f"RSI {rsi:.1f} > {LLM_BACKUP_MAX_RSI_LONG} (overbought for LONG)")
        if rsi < LLM_BACKUP_MIN_RSI_LONG:
            return _backup_reject(symbol, direction,
                f"RSI {rsi:.1f} < {LLM_BACKUP_MIN_RSI_LONG} (falling knife)")
    else:  # SHORT
        if rsi < LLM_BACKUP_MIN_RSI_SHORT:
            return _backup_reject(symbol, direction,
                f"RSI {rsi:.1f} < {LLM_BACKUP_MIN_RSI_SHORT} (oversold for SHORT)")
        if rsi > LLM_BACKUP_MAX_RSI_SHORT:
            return _backup_reject(symbol, direction,
                f"RSI {rsi:.1f} > {LLM_BACKUP_MAX_RSI_SHORT} (too overbought, squeeze risk)")

    # ── Gate 4: Volume ───────────────────────────────────────────────────
    if vol_ratio < LLM_BACKUP_MIN_VOL_RATIO:
        return _backup_reject(symbol, direction,
            f"Volume {vol_ratio:.1f}x < {LLM_BACKUP_MIN_VOL_RATIO}x (no conviction)")

    # ── Gate 5: Funding rate extremes ────────────────────────────────────
    if direction == 'LONG' and funding > LLM_BACKUP_MAX_FUNDING_LONG:
        return _backup_reject(symbol, direction,
            f"Funding {funding:.4f}% > {LLM_BACKUP_MAX_FUNDING_LONG}% (crowded LONG)")
    if direction == 'SHORT' and funding < LLM_BACKUP_MAX_FUNDING_SHORT:
        return _backup_reject(symbol, direction,
            f"Funding {funding:.4f}% < {LLM_BACKUP_MAX_FUNDING_SHORT}% (crowded SHORT)")

    # ── Gate 6: Momentum alignment (1h should agree with direction) ──────
    if direction == 'LONG' and change_1h < -1.0:
        return _backup_reject(symbol, direction,
            f"1h momentum {change_1h:+.2f}% bearish vs LONG signal")
    if direction == 'SHORT' and change_1h > 1.0:
        return _backup_reject(symbol, direction,
            f"1h momentum {change_1h:+.2f}% bullish vs SHORT signal")

    # ── Gate 7: EMA confirmation ─────────────────────────────────────────
    if direction == 'LONG' and ema_50 > 0 and current < ema_50 * 0.97:
        return _backup_reject(symbol, direction,
            f"Price {current:.6f} < EMA50*0.97 {ema_50*0.97:.6f} (below trend)")
    if direction == 'SHORT' and ema_50 > 0 and current > ema_50 * 1.03:
        return _backup_reject(symbol, direction,
            f"Price {current:.6f} > EMA50*1.03 {ema_50*1.03:.6f} (above trend)")

    # ── All gates passed — approve with backup confidence ────────────────
    # Build a reason string from the key indicators
    conf = 0.4  # Lower confidence than LLM (we're less sophisticated)
    reason_parts = [
        f"score={score}",
        f"RSI={rsi:.0f}",
        f"vol={vol_ratio:.1f}x",
        f"1h={change_1h:+.1f}%",
    ]
    if breakout:
        reason_parts.append("breakout")
        conf += 0.1
    if vol_ratio > 2.0:
        conf += 0.1  # High volume = more confident

    reason = f"🛡️ BACKUP OK: {', '.join(reason_parts)}"

    result = {
        'approved': True,
        'reason': reason,
        'confidence': min(conf, 0.6),  # Cap confidence at 0.6 for backup
        'model': 'rule_based_backup',
        'provider': 'backup',
        'tokens_in': 0,
        'tokens_out': 0,
        'latency_ms': 0,
    }
    print(f"  🛡️ BACKUP APPROVED {symbol} {direction}: {reason}")
    return result


def _backup_reject(symbol, direction, reason):
    """Helper: return a rejection result from the backup analyzer."""
    full_reason = f"🛡️ BACKUP REJECT: {reason}"
    print(f"  🛡️ BACKUP REJECTED {symbol} {direction}: {reason}")
    return {
        'approved': False,
        'reason': full_reason,
        'confidence': 0.0,
        'model': 'rule_based_backup',
        'provider': 'backup',
        'tokens_in': 0,
        'tokens_out': 0,
        'latency_ms': 0,
    }


def parse_llm_response(content):
    """Parse JSON from LLM response. Returns dict or None."""

    if not content:
        return None

    # Clean up — remove markdown code blocks if present
    text = content.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text
        text = text.replace('```json', '').replace('```', '').strip()

    try:
        result = json.loads(text)
        if 'decision' in result and 'reason' in result:
            return result
    except json.JSONDecodeError:
        pass

    # Fallback: try to find YES/NO in text
    if 'YES' in text.upper() and 'NO' not in text.upper().replace('YES', ''):
        return {'decision': 'YES', 'confidence': 0.5, 'reason': text[:100]}
    elif 'NO' in text.upper():
        return {'decision': 'NO', 'confidence': 0.5, 'reason': text[:100]}

    return None


def analyze_signal(analysis, force=False):
    """
    Main entry point — analyze a signal with LLM.

    Args:
        analysis: dict from analyze_symbol() with all indicators
        force: bypass cache and minimum score check

    Returns:
        dict with keys: approved (bool), reason (str), model (str),
                         tokens_in (int), tokens_out (int), latency_ms (int)
    """

    symbol = analysis.get('symbol', '')
    direction = analysis.get('direction', '')
    score = analysis.get('runner_score', 0)

    # Check if enabled
    if not LLM_ENABLED and not force:
        return {
            'approved': True,
            'reason': 'LLM disabled',
            'model': None,
            'tokens_in': 0,
            'tokens_out': 0,
            'latency_ms': 0,
        }

    # Check minimum score
    if score < LLM_MIN_SCORE and not force:
        return {
            'approved': True,
            'reason': f'Score {score} < {LLM_MIN_SCORE}, skipped LLM',
            'model': 'skipped',
            'confidence': 0,
            'tokens_in': 0,
            'tokens_out': 0,
            'latency_ms': 0,
        }

    # Check cache
    cache_key = _get_cache_key(symbol, direction, score)
    if _is_cache_valid(cache_key):
        cached = _analysis_cache[cache_key]
        print(f"  🧠 LLM cache hit: {symbol}")
        return cached['result']

    # Build prompt and call
    prompt = format_analysis_prompt(analysis)
    print(f"  🧠 LLM analyzing {symbol} {direction} (score:{score})...")

    start = time.time()
    response = call_llm(prompt)
    latency_ms = int((time.time() - start) * 1000)

    if not response:
        # ── All LLM providers failed — use configured backup mode ────────
        if LLM_BACKUP_MODE == "fail_closed":
            result = {
                'approved': False,
                'reason': 'LLM unavailable + fail-closed mode',
                'model': LLM_MODEL,
                'provider': None,
                'tokens_in': 0,
                'tokens_out': 0,
                'latency_ms': latency_ms,
            }
            print(f"  🔒 FAIL-CLOSED: rejected {symbol} {direction} (all LLM down)")
        elif LLM_BACKUP_MODE == "fail_open":
            result = {
                'approved': True,
                'reason': 'LLM call failed, fail-open',
                'model': LLM_MODEL,
                'provider': None,
                'tokens_in': 0,
                'tokens_out': 0,
                'latency_ms': latency_ms,
            }
            print(f"  ⚠️ FAIL-OPEN: approved {symbol} {direction} (all LLM down)")
        else:
            # Default: rule_based backup
            result = rule_based_backup(analysis)
            result['latency_ms'] = latency_ms

        _analysis_cache[cache_key] = {'result': result, 'ts': time.time()}
        return result

    # Parse response
    parsed = parse_llm_response(response['content'])

    if not parsed:
        # Parse failed — use backup mode instead of blind fail-open
        if LLM_BACKUP_MODE == "fail_closed":
            result = {
                'approved': False,
                'reason': f'Parse failed: {response["content"][:80]}',
                'model': LLM_MODEL,
                'provider': response.get('provider', 'unknown'),
                'tokens_in': response['tokens_in'],
                'tokens_out': response['tokens_out'],
                'latency_ms': latency_ms,
            }
        elif LLM_BACKUP_MODE == "fail_open":
            result = {
                'approved': True,
                'reason': f'Parse failed: {response["content"][:80]}',
                'model': LLM_MODEL,
                'provider': response.get('provider', 'unknown'),
                'tokens_in': response['tokens_in'],
                'tokens_out': response['tokens_out'],
                'latency_ms': latency_ms,
            }
        else:
            # rule_based: LLM responded but garbage — run backup rules
            result = rule_based_backup(analysis)
            result['latency_ms'] = latency_ms
            result['tokens_in'] = response['tokens_in']
            result['tokens_out'] = response['tokens_out']

        _analysis_cache[cache_key] = {'result': result, 'ts': time.time()}
        return result

    # Build result
    decision = parsed.get('decision', 'YES').upper()
    approved = decision == 'YES'
    reason = parsed.get('reason', 'No reason given')
    confidence = parsed.get('confidence', 0.5)

    result = {
        'approved': approved,
        'reason': reason,
        'confidence': confidence,
        'model': LLM_MODEL,
        'provider': response.get('provider', 'unknown'),
        'tokens_in': response['tokens_in'],
        'tokens_out': response['tokens_out'],
        'latency_ms': latency_ms,
    }

    # Cache result
    _analysis_cache[cache_key] = {'result': result, 'ts': time.time()}

    status = "✅ APPROVED" if approved else "❌ REJECTED"
    print(f"  🧠 LLM: {status} — {reason} ({latency_ms}ms)")

    return result


def batch_analyze(signals, max_concurrent=3):
    """
    Analyze multiple signals sequentially.
    (Kept simple — no async needed for 3-5 candidates)

    Args:
        signals: list of analysis dicts from analyze_symbol()

    Returns:
        list of (analysis, llm_result) tuples
    """
    results = []
    for analysis in signals:
        result = analyze_signal(analysis)
        results.append((analysis, result))
    return results


# === CLI test ===
if __name__ == "__main__":
    # Quick test with fake data
    test_analysis = {
        'symbol': 'SOLUSDT',
        'direction': 'LONG',
        'current': 142.50,
        'price_change': 5.2,
        'change_1h': 1.8,
        'rsi': 45.3,
        'macd_histogram': 0.0045,
        'ema_21': 140.2,
        'ema_50': 138.0,
        'atr': 3.5,
        'atr_pct': 2.45,
        'vol_ratio': 3.2,
        'oi_change': 12.5,
        'funding_rate': 0.03,
        'trend': 'BULLISH',
        'structure': 'BREAKOUT',
        'breakout': True,
        'weekly_change': 8.5,
        'runner_score': 8,
        'sl': 136.5,
        'tp1': 155.0,
        'sl_method': 'PRICE',
    }

    print("=== LLM Analyzer Test ===")
    result = analyze_signal(test_analysis, force=True)
    print(json.dumps(result, indent=2))
