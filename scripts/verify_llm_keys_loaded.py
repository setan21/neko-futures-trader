#!/usr/bin/env python3
"""
verify_llm_keys_loaded.py — Health check script for Neko LLM key status.

Checks:
1. .env loaded correctly (NOUS_API_KEY, OPENROUTER_API_KEY, MINIMAX_API_KEY)
2. config.py LLM settings match expected values
3. llm_analyzer.py can import and has keys loaded
4. Optional: live API call to primary provider
5. Recent scanner.log for fail-open / LLM failure patterns

Usage:
  python3 scripts/verify_llm_keys_loaded.py          # Full check (keys + log scan)
  python3 scripts/verify_llm_keys_loaded.py --quick   # Keys only, no log scan
  python3 scripts/verify_llm_keys_loaded.py --test     # Keys + live API test

Exit codes:
  0 = all OK
  1 = warning (non-critical issue)
  2 = critical (LLM will fail-open)
"""

import os
import sys
import time
import json

# Ensure we're in the neko project dir
NEKO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(NEKO_DIR)
sys.path.insert(0, NEKO_DIR)

def load_dotenv_manual(path=".env"):
    """Load .env without python-dotenv dependency."""
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            env[key] = value
            if key not in os.environ:
                os.environ[key] = value
    return env


def check_env_keys():
    """Check .env has required LLM API keys."""
    print("=" * 50)
    print("1. ENV KEY CHECK")
    print("=" * 50)

    env = load_dotenv_manual()

    keys_to_check = {
        "NOUS_API_KEY": "Primary LLM provider (Nous Research)",
        "OPENROUTER_API_KEY": "Fallback 1 (OpenRouter) — DISABLED",
        "MINIMAX_API_KEY": "Fallback 2 (MiniMax) — DISABLED",
    }

    results = {}
    for key, desc in keys_to_check.items():
        val = os.environ.get(key, "")
        if val:
            masked = val[:8] + "..." + val[-4:] if len(val) > 12 else "***"
            print(f"  ✅ {key} = {masked} ({desc})")
            results[key] = True
        else:
            status = "⚠️" if "DISABLED" in desc else "❌"
            print(f"  {status} {key} = EMPTY ({desc})")
            results[key] = False

    return results


def check_config():
    """Check config.py LLM settings."""
    print()
    print("=" * 50)
    print("2. CONFIG CHECK")
    print("=" * 50)

    try:
        from config import (
            LLM_ENABLED, LLM_MODEL, LLM_BASE_URL,
            LLM_FALLBACK1_ENABLED, LLM_FALLBACK1_MODEL,
            LLM_FALLBACK2_ENABLED, LLM_FALLBACK2_MODEL,
            MAX_DAILY_LOSS
        )
    except ImportError as e:
        print(f"  ❌ Cannot import config.py: {e}")
        return False

    print(f"  LLM_ENABLED        = {LLM_ENABLED}")
    print(f"  LLM_MODEL          = {LLM_MODEL}")
    print(f"  LLM_BASE_URL       = {LLM_BASE_URL}")
    print(f"  LLM_FALLBACK1_EN   = {LLM_FALLBACK1_ENABLED}")
    print(f"  LLM_FALLBACK1_MDL  = {LLM_FALLBACK1_MODEL}")
    print(f"  LLM_FALLBACK2_EN   = {LLM_FALLBACK2_ENABLED}")
    print(f"  LLM_FALLBACK2_MDL  = {LLM_FALLBACK2_MODEL}")
    print(f"  MAX_DAILY_LOSS     = {MAX_DAILY_LOSS} USDT")

    # Validate
    issues = []
    if not LLM_ENABLED:
        issues.append("LLM_ENABLED is False — all signals auto-approved!")
    if "mimo-v2" in LLM_MODEL.lower():
        issues.append(f"LLM_MODEL={LLM_MODEL} is a reasoning model — will fail-open!")

    if issues:
        for issue in issues:
            print(f"  ❌ {issue}")
        return False
    else:
        print(f"  ✅ Config looks correct")
        return True


def check_llm_analyzer():
    """Check llm_analyzer.py can import and has keys loaded."""
    print()
    print("=" * 50)
    print("3. LLM ANALYZER IMPORT CHECK")
    print("=" * 50)

    try:
        import llm_analyzer
    except ImportError as e:
        print(f"  ❌ Cannot import llm_analyzer: {e}")
        return False

    key_status = {
        "NOUS (primary)": getattr(llm_analyzer, "LLM_API_KEY", ""),
        "OpenRouter (fallback1)": getattr(llm_analyzer, "LLM_FALLBACK1_API_KEY", ""),
        "MiniMax (fallback2)": getattr(llm_analyzer, "LLM_FALLBACK2_API_KEY", ""),
    }

    all_ok = True
    for name, key in key_status.items():
        if key:
            print(f"  ✅ {name}: loaded ({len(key)} chars)")
        else:
            is_primary = "primary" in name
            symbol = "❌" if is_primary else "⚠️"
            print(f"  {symbol} {name}: EMPTY {'← CRITICAL' if is_primary else '(disabled anyway)'}")
            if is_primary:
                all_ok = False

    # Check backup mode
    backup_mode = getattr(llm_analyzer, "LLM_BACKUP_MODE", "fail_open")
    print(f"  Backup mode: {backup_mode}")
    if backup_mode == "fail_open":
        print(f"  ⚠️ Backup mode is fail-open — if LLM dies, ALL signals auto-approved!")

    return all_ok


def test_api_call():
    """Make a minimal API call to test connectivity."""
    print()
    print("=" * 50)
    print("4. LIVE API TEST")
    print("=" * 50)

    api_key = os.environ.get("NOUS_API_KEY", "")
    if not api_key:
        print("  ⏭️ Skipped — NOUS_API_KEY is empty")
        return False

    import urllib.request
    import urllib.error

    # Use model from config if available
    try:
        from config import LLM_MODEL, LLM_BASE_URL
        model = LLM_MODEL
        url = LLM_BASE_URL
    except ImportError:
        model = "hermes-4-70b"
        url = "https://inference-api.nousresearch.com/v1/chat/completions"

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
        "max_tokens": 5,
        "temperature": 0,
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })

    start = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        latency = int((time.time() - start) * 1000)
        data = json.loads(resp.read())
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        provider = data.get("model", "unknown")
        tokens = data.get("usage", {}).get("total_tokens", 0)

        if content:
            print(f"  ✅ API responded in {latency}ms")
            print(f"     Model: {provider}, Tokens: {tokens}")
            print(f"     Response: {content[:50]}")
            return True
        else:
            print(f"  ⚠️ API responded but empty content (reasoning model?)")
            print(f"     Latency: {latency}ms")
            return False

    except urllib.error.HTTPError as e:
        latency = int((time.time() - start) * 1000)
        body = ""
        try:
            body = e.read().decode()[:200]
        except:
            pass
        print(f"  ❌ HTTP {e.code} in {latency}ms")
        print(f"     {body}")
        return False
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        print(f"  ❌ Error after {latency}ms: {e}")
        return False


def check_scanner_logs():
    """Check recent scanner.log for LLM failure patterns."""
    print()
    print("=" * 50)
    print("5. SCANNER LOG ANALYSIS")
    print("=" * 50)

    log_path = os.path.join(NEKO_DIR, "logs", "scanner.log")
    if not os.path.exists(log_path):
        print("  ⚠️ scanner.log not found")
        return True

    # Read last 5000 lines
    with open(log_path, "r") as f:
        lines = f.readlines()[-5000:]

    # Count patterns
    patterns = {
        "fail-open": 0,
        "LLM call failed": 0,
        "LLM API error": 0,
        "No Nous API key": 0,
        "Parse failed": 0,
        "LLM APPROVED": 0,
        "LLM REJECTED": 0,
        "BACKUP APPROVED": 0,
        "BACKUP REJECT": 0,
        "DAILY LOSS LIMIT": 0,
    }

    for line in lines:
        for pat in patterns:
            if pat in line:
                patterns[pat] += 1

    # Report
    critical = False

    # Fail-open count
    fail_open = patterns["fail-open"]
    if fail_open > 0:
        print(f"  ❌ fail-open count: {fail_open} ← LLM was down, signals auto-approved!")
        critical = True
    else:
        print(f"  ✅ fail-open count: 0")

    # LLM call failures
    llm_failed = patterns["LLM call failed"]
    if llm_failed > 0:
        print(f"  ❌ LLM call failed: {llm_failed}")
        critical = True
    else:
        print(f"  ✅ LLM call failed: 0")

    # API errors
    api_errors = patterns["LLM API error"]
    if api_errors > 0:
        print(f"  ⚠️ LLM API errors: {api_errors}")
    else:
        print(f"  ✅ LLM API errors: 0")

    # Key loading
    no_key = patterns["No Nous API key"]
    if no_key > 0:
        print(f"  ❌ 'No Nous API key' messages: {no_key} ← key not loading!")
        critical = True
    else:
        print(f"  ✅ Key loading: no 'No Nous API key' messages")

    # Parse failures
    parse_fails = patterns["Parse failed"]
    if parse_fails > 0:
        print(f"  ⚠️ Parse failures: {parse_fails} ← possible reasoning model issue")

    # Approval stats
    approved = patterns["LLM APPROVED"]
    rejected = patterns["LLM REJECTED"]
    total = approved + rejected
    if total > 0:
        reject_rate = rejected / total * 100
        print(f"  📊 LLM decisions: {approved} approved, {rejected} rejected ({reject_rate:.1f}% reject rate)")
        if reject_rate > 95:
            print(f"  ⚠️ Very high reject rate — check LLM prompt or model")
    else:
        print(f"  📊 No LLM decisions in recent logs")

    # Daily loss limit
    dll = patterns["DAILY LOSS LIMIT"]
    if dll > 0:
        print(f"  📊 Daily loss limit hits: {dll} (scanner blocked for rest of day)")

    return not critical


def main():
    args = sys.argv[1:]
    quick = "--quick" in args
    test = "--test" in args

    print("🔍 NEKO LLM KEY VERIFICATION")
    print(f"   Project: {NEKO_DIR}")
    print(f"   Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print()

    results = {}

    # 1. Env keys
    env_results = check_env_keys()
    results["env"] = all(env_results.values())

    # 2. Config
    results["config"] = check_config()

    # 3. Import check
    results["import"] = check_llm_analyzer()

    # 4. Live test (optional)
    if test:
        results["api"] = test_api_call()
    else:
        print()
        print("=" * 50)
        print("4. LIVE API TEST (skipped, use --test to enable)")
        print("=" * 50)

    # 5. Log scan (unless --quick)
    if not quick:
        results["logs"] = check_scanner_logs()
    else:
        print()
        print("=" * 50)
        print("5. SCANNER LOG (skipped, --quick mode)")
        print("=" * 50)

    # Summary
    print()
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)

    all_ok = True
    critical = False

    for check, passed in results.items():
        symbol = "✅" if passed else "❌"
        print(f"  {symbol} {check}")
        if not passed:
            if check in ("env", "import"):
                critical = True
            all_ok = False

    if critical:
        print("\n❌ CRITICAL: LLM will fail-open — primary key missing or broken!")
        sys.exit(2)
    elif not all_ok:
        print("\n⚠️ WARNING: Non-critical issues found")
        sys.exit(1)
    else:
        print("\n✅ All LLM key checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
