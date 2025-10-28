-- Migration: Create pi_devices table
-- Purpose: Track Raspberry Pi devices and their assigned locations
-- Admins can manage Pi assignments by updating this table

CREATE TABLE IF NOT EXISTS pi_devices (
    hostname VARCHAR(255) PRIMARY KEY,
    location VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for active devices lookup
CREATE INDEX idx_pi_devices_active ON pi_devices(is_active);

-- Example data (update with your actual Pi hostnames)
-- INSERT INTO pi_devices (hostname, location, is_active) VALUES
--   ('raspberrypi-001', 'North Warehouse Aisle 3', TRUE),
--   ('raspberrypi-002', 'South Warehouse Dock 1', TRUE),
--   ('raspberrypi-003', 'East Loading Bay', TRUE);
