# Admin Guide: Managing Pi Devices

This guide covers how to manage Raspberry Pi devices and their location assignments using PostgreSQL.

## Overview

Each Pi is uniquely identified by its **hostname**. Admins manage Pi-to-location assignments through the `pi_devices` table in the PostgreSQL database.

## Database Setup

### Network Configuration

The PostgreSQL database server is accessible via:

- **Internal Network IP**: `10.69.1.52` (primary, used by default)
- **Tailscale VPN IP**: `100.75.187.68` (alternative for remote access)
- **DNS**: `internal.maverickmolding.com`

Pis on the internal network will use `10.69.1.52`. For remote administration or testing via Tailscale, use `100.75.187.68`.

### 1. Run Migrations

Connect to your PostgreSQL database and run the migration scripts in order:

```bash
# From the repository root
psql -h 10.69.1.52 -U postgres -d postgres -f migrations/001_create_pi_devices.sql
psql -h 10.69.1.52 -U postgres -d postgres -f migrations/002_add_hostname_to_scan_log.sql
```

Or connect to psql and run manually:

```sql
\i migrations/001_create_pi_devices.sql
\i migrations/002_add_hostname_to_scan_log.sql
```

## Managing Pi Devices

### View All Registered Pis

```sql
SELECT hostname, location, is_active, last_seen, created_at
FROM pi_devices
ORDER BY last_seen DESC;
```

### Register a New Pi

When a new Pi starts up for the first time, it will auto-register with an "UNASSIGNED" location. To assign it properly:

```sql
-- Option 1: Update the auto-registered Pi
UPDATE pi_devices
SET location = 'South Warehouse Dock 1',
    is_active = TRUE
WHERE hostname = 'raspberrypi-002';

-- Option 2: Manually register before deployment
INSERT INTO pi_devices (hostname, location, is_active)
VALUES ('raspberrypi-003', 'East Loading Bay', TRUE);
```

### Reassign a Pi to a Different Location

```sql
UPDATE pi_devices
SET location = 'West Warehouse Aisle 5',
    updated_at = CURRENT_TIMESTAMP
WHERE hostname = 'raspberrypi-001';
```

The Pi will automatically pick up the new location within 5 minutes (configurable via `LOCATION_REFRESH_INTERVAL`).

### Deactivate a Pi

```sql
UPDATE pi_devices
SET is_active = FALSE
WHERE hostname = 'raspberrypi-old';
```

The Pi will continue to run but display a warning. Scans will still be recorded.

### Reactivate a Pi

```sql
UPDATE pi_devices
SET is_active = TRUE
WHERE hostname = 'raspberrypi-001';
```

### View Pi Activity

Check which Pis are currently active:

```sql
-- Pis that have checked in within the last 10 minutes
SELECT hostname, location, last_seen
FROM pi_devices
WHERE last_seen > NOW() - INTERVAL '10 minutes'
ORDER BY last_seen DESC;
```

### View Scan History by Pi

```sql
-- View all scans from a specific Pi
SELECT job_number, pi_hostname, location, scanned_at
FROM scan_log
WHERE pi_hostname = 'raspberrypi-001'
ORDER BY scanned_at DESC
LIMIT 100;

-- View scan counts by Pi today
SELECT pi_hostname, location, COUNT(*) as scan_count
FROM scan_log
WHERE DATE(scanned_at) = CURRENT_DATE
GROUP BY pi_hostname, location
ORDER BY scan_count DESC;
```

## Finding Pi Hostnames

### On the Pi itself

SSH into the Pi and run:

```bash
hostname
```

### From the database

After a Pi has started up once, it will appear in the `pi_devices` table:

```sql
SELECT hostname, location, is_active, last_seen
FROM pi_devices
ORDER BY created_at DESC;
```

### On the Pi's screen

The hostname is displayed at the bottom of the Beep It GUI:
```
Hostname: raspberrypi-001    IP: 100.75.187.45
```

## Changing a Pi's Hostname

If you need to rename a Pi:

1. SSH into the Pi
2. Edit the hostname:
   ```bash
   sudo hostnamectl set-hostname new-pi-name
   ```
3. Restart the Pi:
   ```bash
   sudo reboot
   ```
4. Update the database record:
   ```sql
   UPDATE pi_devices
   SET hostname = 'new-pi-name'
   WHERE hostname = 'old-pi-name';
   
   -- Also update scan_log history if needed
   UPDATE scan_log
   SET pi_hostname = 'new-pi-name'
   WHERE pi_hostname = 'old-pi-name';
   ```

## Troubleshooting

### Pi shows "UNASSIGNED" location

The Pi is not registered. Assign it a location:

```sql
UPDATE pi_devices
SET location = 'Your Location Here',
    is_active = TRUE
WHERE hostname = 'the-hostname-shown';
```

### Pi shows warning: "This Pi is marked as inactive"

Reactivate it:

```sql
UPDATE pi_devices
SET is_active = TRUE
WHERE hostname = 'the-hostname';
```

### Database connection errors

1. Check that the Pi can reach the database server:
   - Internal network: `ping 10.69.1.52`
   - Tailscale VPN: `ping 100.75.187.68`
2. Verify database credentials in `scan_gui.py`
3. Check PostgreSQL logs on the server
4. If connecting remotely via Tailscale, ensure Tailscale is running and connected

### Location not updating after reassignment

- Location refreshes every 5 minutes by default
- To force an immediate update, restart the Beep It application on the Pi:
  ```bash
  sudo systemctl restart beep-it.service
  ```

## Best Practices

1. **Use descriptive hostnames**: Name Pis by location or number (e.g., `warehouse-north-01`)
2. **Track last_seen**: Monitor the `last_seen` timestamp to identify offline devices
3. **Document location changes**: Keep a log of when Pis are moved
4. **Test before deployment**: Register and test each Pi before deploying to the warehouse floor
5. **Regular audits**: Periodically review `pi_devices` to remove decommissioned units

## Database Schema Reference

### pi_devices table

| Column | Type | Description |
|--------|------|-------------|
| hostname | VARCHAR(255) | Primary key, Pi's hostname |
| location | VARCHAR(255) | Human-readable location description |
| is_active | BOOLEAN | Whether the Pi is currently in use |
| last_seen | TIMESTAMP | Last time Pi fetched its location |
| created_at | TIMESTAMP | When record was created |
| updated_at | TIMESTAMP | When record was last modified |

### scan_log additions

| Column | Type | Description |
|--------|------|-------------|
| pi_hostname | VARCHAR(255) | Which Pi performed the scan |
