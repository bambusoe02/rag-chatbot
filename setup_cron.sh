#!/bin/bash

# Setup cron job for automated backups

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Setting up automated backup cron job..."

# Add to crontab (runs daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * cd ${SCRIPT_DIR} && ./backup.sh >> ${SCRIPT_DIR}/backup.log 2>&1") | crontab -

echo "✅ Cron job added:"
echo "   Runs daily at 2:00 AM"
echo "   Logs to: ${SCRIPT_DIR}/backup.log"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove cron job: crontab -e (then delete the line)"

