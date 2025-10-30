# Beep It - Job Scanner Application

A Tkinter-based job scanner application for warehouse environments, designed to run on Raspberry Pi devices. Scans job numbers via barcode scanner and logs them to a PostgreSQL database.

## Features

- **Dynamic Location Management**: Pi devices fetch their assigned location from the database
- **Auto-Registration**: New Pis automatically register themselves in the database
- **Background Operations**: Database operations run in background threads to keep UI responsive
- **Auto-Updates**: Deployed devices automatically fetch updates from GitHub releases
- **Multi-Tenancy**: Support for multiple Pi devices with different locations
- **Persistent Display**: Shows location, hostname, and IP information

## Quick Start

### For Administrators

See [docs/ADMIN_GUIDE.md](docs/ADMIN_GUIDE.md) for:
- Database setup and migrations
- Managing Pi devices and locations
- SQL queries for common tasks

### For Deployment

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for:
- Installing on Raspberry Pi devices
- Configuring auto-start on boot
- Setting up auto-updates
- Troubleshooting common issues

### For Developers

See [WARP.md](WARP.md) for:
- Project architecture
- Development workflow
- Release process
- Common commands

## Architecture

```
┌─────────────────┐
│  Raspberry Pi   │
│  (scan_gui.py)  │
│                 │
│  • Fetch loc    │
│  • Scan jobs    │
│  • Auto-update  │
└────────┬────────┘
         │
         │ 10.69.1.52:5432
         │ (Internal Network)
         │
┌────────▼─────────┐
│   PostgreSQL     │
│  Windows Server  │
│                  │
│  • pi_devices    │
│  • scan_log      │
└──────────────────┘
```

## Database Schema

### `pi_devices` table
Tracks all registered Raspberry Pi devices and their location assignments.

| Column | Type | Description |
|--------|------|-------------|
| hostname | VARCHAR(255) | Primary key, Pi's hostname |
| location | VARCHAR(255) | Human-readable location |
| is_active | BOOLEAN | Whether Pi is currently in use |
| last_seen | TIMESTAMP | Last location fetch |
| created_at | TIMESTAMP | Registration date |
| updated_at | TIMESTAMP | Last modification |

### `scan_log` table
Records all job scans from all devices.

| Column | Type | Description |
|--------|------|-------------|
| job_number | VARCHAR | Scanned job number |
| barcode | VARCHAR | Scanned barcode value |
| pi_ip | VARCHAR | Pi's IP address |
| pi_hostname | VARCHAR | Pi's hostname |
| location | VARCHAR | Location at scan time |
| scanned_at | TIMESTAMP | Scan timestamp |

## Installation

**On Raspberry Pi:**

```bash
cd ~
git clone https://github.com/TheMadBotterINC/Maverick-Beep-It.git
cd Maverick-Beep-It
sudo ./scripts/install.sh
```

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for complete instructions.

## Development

**Run locally (Mac/Linux/Windows):**

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip3 install -r requirements.txt

# Run application
python3 scan_gui.py
```

**Test database connection:**

```bash
python3 test_db_setup.py
```

## Releasing Updates

1. Edit `scan_gui.py` in repository root
2. Copy to staging: `cp scan_gui.py updates/scan_gui.py`
3. Bump version: `echo "0.1.3" > updates/VERSION`
4. Commit and tag:
   ```bash
   git add updates/
   git commit -m "Release v0.1.3: description"
   git tag v0.1.3
   git push origin main --tags
   ```

GitHub Actions automatically creates a release. Deployed devices will update within 24 hours (or trigger manually).

## Configuration

Edit constants at the top of `scan_gui.py`:

```python
DB_HOST = "10.69.1.52"              # PostgreSQL server IP
DB_PORT = 5432                       # Database port
DB_NAME = "postgres"                 # Database name
DB_USER = "postgres"                 # Database user
DB_PASS = "your_password"            # Database password
LOCATION_REFRESH_INTERVAL = 300      # Refresh location every 5 minutes
```

## System Requirements

- **Raspberry Pi**: Pi 3 or later recommended
- **OS**: Raspberry Pi OS (Debian-based)
- **Python**: 3.7 or higher
- **Database**: PostgreSQL 10 or higher
- **Network**: Access to internal network (10.69.1.0/24) or Tailscale VPN

## Documentation

- [INSTALLATION.md](docs/INSTALLATION.md) - Pi deployment guide
- [ADMIN_GUIDE.md](docs/ADMIN_GUIDE.md) - Database and device management
- [WARP.md](WARP.md) - Project architecture and development

## License

Proprietary - All rights reserved by Maverick Molding

## Support

For issues or questions, contact the development team.
