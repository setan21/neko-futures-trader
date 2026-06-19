"""
Position monitor for Neko paper trading.
Calls paper_trader.check_positions() every loop and executes exit actions.
This was the MISSING piece: run_paper_scanner only scanned for entries and
never monitored open positions for SL/TP/timeout, so positions never closed.
"""
import json
import urllib.request

from paper_trader import load_positions, check_positions, close_position


def _price(symbol, fallback):
    try:
        r = json.load(urllib.request.urlopen(
            "https://fapi.binance.com/fapi/v1/ticker/price?symbol=" + symbol, timeout=8))
        return float(r["price"])
    except Exception:
        return fallback


def monitor_positions():
    """Check all OPEN paper positions and execute exits. Returns list of closes."""
    positions = load_positions()
    open_pos = {k: v for k, v in positions.items() if v.get("status") == "OPEN"}
    if not open_pos:
        return []

    # Build current price map
    prices = {}
    for v in open_pos.values():
        sym = v["symbol"]
        if sym not in prices:
            prices[sym] = _price(sym, v["entry_price"])

    actions = check_positions(prices)
    closed = []
    for act in actions:
        oid = act["order_id"]
        px = act["price"]
        reason = act["reason"]
        if act["action"] in ("CLOSE",):
            res = close_position(oid, px, reason)
            if res.get("success"):
                pos = load_positions().get(oid, {})
                closed.append({
                    "symbol": pos.get("symbol", "?"),
                    "reason": reason,
                    "pnl": res.get("pnl"),
                    "pnl_pct": res.get("pnl_pct"),
                })
        # PARTIAL_TP: mark tp level hit so it doesn't re-fire; full exit handled
        # by later CLOSE rules. (Paper partials simplified — record the level.)
        elif act["action"] == "PARTIAL_TP":
            positions = load_positions()
            if oid in positions:
                tps = positions[oid].setdefault("take_profits", [])
                lvl = positions[oid].get("tp1") if reason == "TP1" else positions[oid].get("tp2")
                if lvl is not None and lvl not in tps:
                    tps.append(lvl)
                from paper_trader import save_positions
                save_positions(positions)
    return closed


if __name__ == "__main__":
    res = monitor_positions()
    if res:
        for c in res:
            print("CLOSED %-12s %-14s pnl=%.2f (%.2f%%)" % (
                c["symbol"], c["reason"], c["pnl"] or 0, c["pnl_pct"] or 0))
    else:
        print("No exits this cycle.")
