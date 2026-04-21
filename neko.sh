#!/bin/bash
# ==========================================
# 🐱 Neko Futures Trader - Command Helper
# ==========================================
# Usage: ./neko.sh <command>
# ==========================================

WORKDIR="/root/workspace/neko-futures-trader"

case "$1" in
    # ── POSITIONS & BALANCE ───────────────
    pos|position)
        cd "$WORKDIR" && python3 position_command.py
        ;;
    balance|bal)
        cd "$WORKDIR" && python3 scripts/check_balance.py
        ;;
    
    # ── SERVICE MANAGEMENT ────────────────
    status)
        echo "🐱 Neko Futures Trader - Service Status"
        echo "========================================="
        systemctl status neko-scanner neko-monitor neko-dashboard --no-pager
        ;;
    restart)
        echo "🔄 Restarting all services..."
        systemctl restart neko-scanner neko-monitor neko-dashboard
        sleep 2
        systemctl status neko-scanner neko-monitor neko-dashboard --no-pager | grep -E "●|Active:"
        ;;
    restart-scanner)
        systemctl restart neko-scanner
        echo "✅ Scanner restarted"
        ;;
    restart-monitor)
        systemctl restart neko-monitor
        echo "✅ Monitor restarted"
        ;;
    restart-dashboard)
        systemctl restart neko-dashboard
        echo "✅ Dashboard restarted"
        ;;
    stop)
        echo "⛔ Stopping all services..."
        systemctl stop neko-scanner neko-monitor neko-dashboard
        echo "✅ All services stopped"
        ;;
    start)
        echo "🚀 Starting all services..."
        systemctl start neko-scanner neko-monitor neko-dashboard
        sleep 2
        systemctl status neko-scanner neko-monitor neko-dashboard --no-pager | grep -E "●|Active:"
        ;;
    
    # ── SLEEP MODE ────────────────────────
    sleep-on)
        echo "🟡 Enabling SLEEP MODE..."
        sed -i 's/SLEEP_MODE = False/SLEEP_MODE = True/' "$WORKDIR/config.py"
        systemctl restart neko-scanner
        echo "✅ Sleep Mode ON — Max 4 posisi, Min score 7"
        ;;
    sleep-off)
        echo "🟢 Disabling SLEEP MODE..."
        sed -i 's/SLEEP_MODE = True/SLEEP_MODE = False/' "$WORKDIR/config.py"
        systemctl restart neko-scanner
        echo "✅ Sleep Mode OFF — Max 8 posisi, Min score 6"
        ;;
    sleep-status)
        grep "SLEEP_MODE" "$WORKDIR/config.py" | head -1
        ;;
    
    # ── LOGS ──────────────────────────────
    logs)
        echo "📜 Recent logs (last 30 lines each):"
        echo ""
        echo "=== SCANNER ==="
        journalctl -u neko-scanner --no-pager -n 30
        echo ""
        echo "=== MONITOR ==="
        journalctl -u neko-monitor --no-pager -n 30
        ;;
    logs-scanner)
        journalctl -u neko-scanner -f
        ;;
    logs-monitor)
        journalctl -u neko-monitor -f
        ;;
    logs-dashboard)
        journalctl -u neko-dashboard -f
        ;;
    
    # ── EMERGENCY ─────────────────────────
    close-all)
        echo "🚨 EMERGENCY CLOSE ALL POSITIONS"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            cd "$WORKDIR" && python3 emergency_close.py
        else
            echo "❌ Cancelled"
        fi
        ;;
    
    # ── ANALYSIS ──────────────────────────
    backtest)
        cd "$WORKDIR" && python3 backtester.py
        ;;
    analyze)
        cd "$WORKDIR" && python3 advanced_analysis.py
        ;;
    
    # ── HELP ──────────────────────────────
    help|*)
        echo "🐱 Neko Futures Trader Commands"
        echo "================================"
        echo ""
        echo "📊 Status & Info:"
        echo "  pos, position     — Cek posisi terbuka"
        echo "  balance, bal      — Cek balance"
        echo "  status            — Status semua service"
        echo ""
        echo "🔄 Service Control:"
        echo "  start             — Start semua service"
        echo "  stop              — Stop semua service"
        echo "  restart           — Restart semua service"
        echo "  restart-scanner   — Restart scanner only"
        echo "  restart-monitor   — Restart monitor only"
        echo "  restart-dashboard — Restart dashboard only"
        echo ""
        echo "🌙 Sleep Mode:"
        echo "  sleep-on          — Aktifkan sleep mode"
        echo "  sleep-off         — Matikan sleep mode"
        echo "  sleep-status      — Cek sleep mode status"
        echo ""
        echo "📜 Logs:"
        echo "  logs              — Recent logs (semua)"
        echo "  logs-scanner      — Follow scanner logs"
        echo "  logs-monitor      — Follow monitor logs"
        echo "  logs-dashboard    — Follow dashboard logs"
        echo ""
        echo "🚨 Emergency:"
        echo "  close-all         — Emergency close semua posisi"
        echo ""
        echo "📈 Analysis:"
        echo "  backtest          — Jalankan backtesting"
        echo "  analyze           — Advanced analysis"
        echo ""
        echo "Usage: ./neko.sh <command>"
        ;;
esac
