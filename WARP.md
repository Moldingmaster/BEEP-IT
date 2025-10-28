# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Beep It is a job scanner application for warehouse environments. It consists of a Python/Tkinter GUI (`scan_gui.py`) that runs on Raspberry Pi devices, scans job numbers via barcode scanner, and logs them to a PostgreSQL database over Tailscale.

The project includes a GitHub Actions-based auto-update mechanism that allows deployed devices to fetch updates from private GitHub releases.

## Architecture

### Application Layer
- **scan_gui.py**: Main GUI application (Tkinter) that:
  - Displays location information
  - Accepts barcode scans via keyboard entry
  - Inserts scan records to PostgreSQL (job_number, barcode, pi_ip, location, scanned_at)
  - Runs database operations in background threads to avoid blocking UI
  - Shows real-time clock and device IP address

### Database Layer
- PostgreSQL database hosted on Windows Server (Tailscale network)
- Table: `scan_log` with columns: job_number, barcode, pi_ip, location, scanned_at
- Connection uses psycopg2-binary

### Update/Distribution Architecture
- **Development**: Edit `scan_gui.py` in repo root
- **Staging**: Copy updated file to `updates/scan_gui.py`
- **Versioning**: Bump `updates/VERSION` file (semantic versioning: 0.1.0)
- **Release**: Push git tag (e.g., `v0.1.2`) to trigger GitHub Actions workflow
- **Distribution**: GitHub workflow creates release with assets:
  - `scan_gui.py` (payload)
  - `scan_gui.py.sha256` (checksum)
  - `VERSION` (version string)
- **Device Updates**: Systemd timer runs `beep-it-update` script daily to:
  - Check latest GitHub release via API
  - Download assets if version changed
  - Verify SHA256 checksum
  - Install to `/opt/beep_it/scan_gui.py`
  - Optionally restart service

## Common Commands

### Running the Application
```bash
python3 scan_gui.py
```

### Installing Dependencies
```bash
pip3 install -r requirements.txt
```

### Testing Database Connection
```bash
# Edit DB_HOST, DB_PASS, etc. in scan_gui.py first
python3 -c "import psycopg2; psycopg2.connect(host='100.75.187.68', port=5432, dbname='postgres', user='postgres', password='your_password')"
```

## Releasing Updates

1. Edit `scan_gui.py` in repository root
2. Copy the updated file to `updates/scan_gui.py`:
   ```bash
   cp scan_gui.py updates/scan_gui.py
   ```
3. Bump the version in `updates/VERSION`:
   ```bash
   echo "0.1.2" > updates/VERSION
   ```
4. Commit changes:
   ```bash
   git add updates/
   git commit -m "Release v0.1.2: description of changes"
   ```
5. Create and push tag:
   ```bash
   git tag v0.1.2
   git push origin main --tags
   ```

The GitHub Actions workflow will automatically create a release with the necessary assets.

## Deployment Setup (Raspberry Pi)

### Installation Script Location
- Update script: `scripts/beep-it-update` → install to `/usr/local/sbin/beep-it-update`
- Systemd service: `contrib/systemd/beep-it-update.service` → `/etc/systemd/system/`
- Systemd timer: `contrib/systemd/beep-it-update.timer` → `/etc/systemd/system/`

### Required Environment
- Create `/etc/default/beep-it-update` with:
  ```bash
  GITHUB_TOKEN_RO=ghp_xxxxxxxxxxxxxxxxxxxxx
  ```
- Token must have read-only access to private repo releases

### Service Management
```bash
# Enable and start the update timer
systemctl enable beep-it-update.timer
systemctl start beep-it-update.timer

# Check timer status
systemctl list-timers beep-it-update.timer

# Manually trigger update check
systemctl start beep-it-update.service
```

## Configuration

### Application Configuration (scan_gui.py)
Edit these constants at the top of the file:
- `DB_HOST`: PostgreSQL server IP (Tailscale)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASS`: Database password
- `LOCATION`: Physical location string (e.g., "North Warehouse Aisle 3")

### Update Script Configuration (scripts/beep-it-update)
- `OWNER`: GitHub organization/username
- `REPO`: Repository name
- `LOCAL_DIR`: Installation directory on device (default: `/opt/beep_it`)
- `SERVICE_NAME`: Optional systemd service to restart after update

## Code Style

- Use idiomatic Python with snake_case naming
- Follow Flake8 style guidelines
- Keep threading operations for database calls to prevent UI blocking
- Use context managers (`with` statements) for database connections
