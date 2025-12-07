# Cron Job Setup Guide

## Setting up Daily Balance Fetch at 1 AM

### Option 1: Using the Shell Script (Recommended)

1. **Open your crontab editor:**
   ```bash
   crontab -e
   ```

2. **Add this line to run daily at 1:00 AM:**
   ```
   0 1 * * * /mnt/Storage/maruf/git/electricity-bill-tracker/run_fetch_balance.sh
   ```

3. **Save and exit** (in vim: press `Esc`, type `:wq`, press Enter)

4. **Verify the cron job is installed:**
   ```bash
   crontab -l
   ```

### Option 2: Direct Command (Alternative)

If you prefer not to use the shell script, add this line instead:
```
0 1 * * * cd /mnt/Storage/maruf/git/electricity-bill-tracker/dpdc_tracker && /mnt/Storage/maruf/git/electricity-bill-tracker/.venv/bin/python manage.py fetch_balance >> /mnt/Storage/maruf/git/electricity-bill-tracker/logs/fetch_balance.log 2>&1
```

### Cron Schedule Explanation

The cron format is: `minute hour day month weekday command`

- `0 1 * * *` means: at minute 0, hour 1 (1 AM), every day, every month, every weekday

### Other Useful Schedules

**Every hour (on the hour):**
```
0 * * * * /mnt/Storage/maruf/git/electricity-bill-tracker/run_fetch_balance.sh
```

**Every 30 minutes:**
```
*/30 * * * * /mnt/Storage/maruf/git/electricity-bill-tracker/run_fetch_balance.sh
```

**Twice daily (1 AM and 1 PM):**
```
0 1,13 * * * /mnt/Storage/maruf/git/electricity-bill-tracker/run_fetch_balance.sh
```

**Every day at 2:30 AM:**
```
30 2 * * * /mnt/Storage/maruf/git/electricity-bill-tracker/run_fetch_balance.sh
```

### Testing Your Setup

1. **Test the script manually first:**
   ```bash
   /mnt/Storage/maruf/git/electricity-bill-tracker/run_fetch_balance.sh
   ```

2. **Check the log file:**
   ```bash
   tail -f /mnt/Storage/maruf/git/electricity-bill-tracker/logs/fetch_balance.log
   ```

3. **Test with a shorter interval** (e.g., every 5 minutes) temporarily:
   ```
   */5 * * * * /mnt/Storage/maruf/git/electricity-bill-tracker/run_fetch_balance.sh
   ```
   
   After confirming it works, change it back to your desired schedule.

### Viewing Logs

**View the last 20 lines of the log:**
```bash
tail -20 /mnt/Storage/maruf/git/electricity-bill-tracker/logs/fetch_balance.log
```

**Watch logs in real-time:**
```bash
tail -f /mnt/Storage/maruf/git/electricity-bill-tracker/logs/fetch_balance.log
```

**Check cron system logs (if needed):**
```bash
sudo journalctl -u cron -f
```
or
```bash
grep CRON /var/log/syslog
```

### Troubleshooting

1. **Cron not running?**
   - Make sure cron service is running:
     ```bash
     sudo systemctl status cron
     ```
   - Start cron if needed:
     ```bash
     sudo systemctl start cron
     ```

2. **Script not executing?**
   - Verify script permissions:
     ```bash
     ls -la /mnt/Storage/maruf/git/electricity-bill-tracker/run_fetch_balance.sh
     ```
   - Ensure the script is executable (should show `-rwxr-xr-x`)

3. **Check for errors:**
   - Look at the log file for error messages
   - Test the management command directly:
     ```bash
     cd /mnt/Storage/maruf/git/electricity-bill-tracker/dpdc_tracker
     source ../.venv/bin/activate
     python manage.py fetch_balance
     ```

4. **Environment variables not loading?**
   - Make sure your `.env` file exists in the project root
   - The shell script will automatically load it

### Using systemd Timer (Advanced Alternative)

If you prefer systemd timers over cron, see `SYSTEMD_TIMER_SETUP.md` for details.

### Important Notes

- Make sure your `.env` file contains the correct `DPDC_CUSTOMER_NUMBER`
- The logs directory will be created automatically
- Logs are appended, so they will grow over time - consider setting up log rotation
- The script uses the virtual environment Python, so dependencies are properly loaded
