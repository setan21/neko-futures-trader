#!/bin/bash
SERVICE="neko-paper-scanner.service"
LOG="/root/neko-futures-trader/logs/watchdog.log"
if ! systemctl is-active --quiet "$SERVICE"; then
    echo "$(date): $SERVICE is not active. Restarting..." >> "$LOG"
    systemctl restart "$SERVICE"
    sleep 5
    if systemctl is-active --quiet "$SERVICE"; then
        echo "$(date): Restart successful." >> "$LOG"
    else
        echo "$(date): Restart failed." >> "$LOG"
    fi
fi
