-- Migration: Add pi_hostname to scan_log
-- Purpose: Track which Pi device performed each scan

ALTER TABLE scan_log ADD COLUMN IF NOT EXISTS pi_hostname VARCHAR(255);

-- Create index for hostname lookups
CREATE INDEX IF NOT EXISTS idx_scan_log_hostname ON scan_log(pi_hostname);

-- Optional: Create index for location-based queries
CREATE INDEX IF NOT EXISTS idx_scan_log_location ON scan_log(location);
