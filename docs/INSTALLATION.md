# Beep It - Installation Guide

This guide covers installing Beep It on Raspberry Pi devices to run automatically on startup.

## Prerequisites

- Raspberry Pi with Raspberry Pi OS (or similar Debian-based OS)
- Network connectivity to PostgreSQL database server (IP: 10.69.1.52)
- Python 3.7 or higher
- Git installed (`sudo apt install git`)
- GitHub Personal Access Token with read access to this private repository

## Quick Installation

1. **Clone the repository on the Raspberry Pi:**

   ```bash
   cd ~
   git clone https://github.com/TheMadBotterINC/Maverick-Beep-It.git
   cd Maverick-Beep-It
   ```

2. **Run the installation script:**

   ```bash
   sudo ./scripts/install.sh
   ```

3. **Configure the GitHub token for auto-updates:**

   Edit `/etc/default/beep-it-update` and add your GitHub Personal Access Token:

   ```bash
   sudo nano /etc/default/beep-it-update
   ```

   Set the token:
   ```bash
   GITHUB_TOKEN_RO=ghp_your_token_here
   ```

   Save and exit (Ctrl+X, then Y, then Enter).

4. **Start the application:**

   ```bash
   sudo systemctl start beep-it.service
   sudo systemctl start beep-it-update.timer
   ```

5. **Verify installation:**

   ```bash
   sudo systemctl status beep-it.service
   ```

## What Gets Installed

The installation script will:

1. Create `/opt/beep_it/` directory with the application files
2. Install Python dependencies (psycopg2-binary)
3. Install systemd services:
   - `beep-it.service` - Main application that runs on startup
   - `beep-it-update.service` - Update checker
   - `beep-it-update.timer` - Daily update scheduler
4. Configure the application to start automatically on boot

## Post-Installation

### Verify the Application is Running

The Beep It GUI should appear automatically on the screen. If not:

```bash
# Check service status
sudo systemctl status beep-it.service

# View logs
sudo journalctl -u beep-it.service -f
```

### Test Database Connection

The application will attempt to connect to the database and register the Pi. Check the GUI for:
- Location showing (might be "UNASSIGNED" initially - this is normal)
- Hostname displayed at the bottom
- IP address displayed at the bottom

If you see database connection errors, verify:
1. The Pi can reach the database server: `ping 10.69.1.52`
2. Database credentials are correct in `/opt/beep_it/scan_gui.py`
3. PostgreSQL is running on the server

### Register the Pi in the Database

New Pis auto-register with location "UNASSIGNED". An admin must assign a proper location via SQL:

```sql
-- Connect to the database
psql -h 10.69.1.52 -U postgres -d postgres

-- List unassigned Pis
SELECT hostname, location, last_seen FROM pi_devices WHERE location LIKE 'UNASSIGNED%';

-- Assign a location
UPDATE pi_devices
SET location = 'North Warehouse Dock 1',
    is_active = TRUE
WHERE hostname = 'the-pi-hostname';
```

The Pi will pick up the new location within 5 minutes (or restart the service to update immediately).

## Managing the Application

### Start/Stop/Restart

```bash
# Start
sudo systemctl start beep-it.service

# Stop
sudo systemctl stop beep-it.service

# Restart
sudo systemctl restart beep-it.service

# View status
sudo systemctl status beep-it.service
```

### View Logs

```bash
# Follow logs in real-time
sudo journalctl -u beep-it.service -f

# View recent logs
sudo journalctl -u beep-it.service -n 100
```

### Disable Auto-Start

```bash
sudo systemctl disable beep-it.service
```

### Re-enable Auto-Start

```bash
sudo systemctl enable beep-it.service
```

## Auto-Updates

The installation includes an auto-update mechanism that checks for new releases daily.

### How It Works

1. A systemd timer runs `beep-it-update` once per day
2. The script checks GitHub for the latest release
3. If a new version is found:
   - Downloads the new `scan_gui.py`
   - Verifies the SHA256 checksum
   - Installs it to `/opt/beep_it/scan_gui.py`
   - Restarts `beep-it.service` automatically

### Manual Update Check

```bash
# Trigger an update check immediately
sudo systemctl start beep-it-update.service

# View update logs
sudo journalctl -u beep-it-update.service -n 50
```

### Check Update Timer Status

```bash
sudo systemctl list-timers beep-it-update.timer
```

### Disable Auto-Updates

```bash
sudo systemctl stop beep-it-update.timer
sudo systemctl disable beep-it-update.timer
```

## Troubleshooting

### Application won't start

1. Check for errors in logs:
   ```bash
   sudo journalctl -u beep-it.service -n 100
   ```

2. Verify Python dependencies:
   ```bash
   pip3 list | grep psycopg2
   ```

3. Try running manually to see errors:
   ```bash
   cd /opt/beep_it
   python3 scan_gui.py
   ```

### GUI not appearing on screen

1. Verify the Pi is running with a graphical desktop environment
2. Check that the `DISPLAY` environment variable is correct in `/etc/systemd/system/beep-it.service`
3. For auto-login issues, ensure the Pi user has permission to access X display

### Database connection errors

1. Test network connectivity: `ping 10.69.1.52`
2. Test database connection:
   ```bash
   python3 -c "import psycopg2; psycopg2.connect(host='10.69.1.52', port=5432, dbname='postgres', user='postgres', password='RxpJcA7FZRiUCPXhLX8T')"
   ```
3. Verify credentials in `/opt/beep_it/scan_gui.py`

### Auto-updates not working

1. Verify GitHub token is set: `sudo cat /etc/default/beep-it-update`
2. Check update logs: `sudo journalctl -u beep-it-update.service -n 50`
3. Manually trigger an update: `sudo systemctl start beep-it-update.service`
4. Verify timer is enabled: `sudo systemctl list-timers beep-it-update.timer`

## Uninstallation

To remove Beep It from a Raspberry Pi:

```bash
# Stop and disable services
sudo systemctl stop beep-it.service beep-it-update.timer
sudo systemctl disable beep-it.service beep-it-update.timer beep-it-update.service

# Remove systemd units
sudo rm /etc/systemd/system/beep-it.service
sudo rm /etc/systemd/system/beep-it-update.service
sudo rm /etc/systemd/system/beep-it-update.timer
sudo rm /usr/local/sbin/beep-it-update

# Reload systemd
sudo systemctl daemon-reload

# Remove application files
sudo rm -rf /opt/beep_it

# Remove configuration
sudo rm /etc/default/beep-it-update

# Optionally remove from database
psql -h 10.69.1.52 -U postgres -d postgres -c "DELETE FROM pi_devices WHERE hostname='your-pi-hostname';"
```

## Security Notes

- The GitHub token in `/etc/default/beep-it-update` should have **read-only** access
- Database credentials are stored in plain text in `/opt/beep_it/scan_gui.py` - protect this file appropriately
- Consider using firewall rules to restrict database access to only necessary IPs
- The application runs as the `pi` user (not root) for security

## Support

For issues or questions, see:
- [ADMIN_GUIDE.md](ADMIN_GUIDE.md) - Database and Pi management
- [WARP.md](../WARP.md) - Project architecture and configuration
