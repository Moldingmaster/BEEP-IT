#!/usr/bin/env python3
"""
Test script to verify database connectivity and setup pi_devices table.
Run this before testing scan_gui.py on your Mac.
"""
import psycopg2
import socket

# Database config (same as scan_gui.py)
DB_HOST = "10.69.1.52"
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "RxpJcA7FZRiUCPXhLX8T"

def test_connection():
    """Test basic database connection."""
    print(f"Testing connection to {DB_HOST}:{DB_PORT}...")
    try:
        with psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASS,
            connect_timeout=5
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"✅ Connected successfully!")
                print(f"   PostgreSQL version: {version[:50]}...")
                return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def check_tables():
    """Check if required tables exist."""
    print("\nChecking database schema...")
    try:
        with psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASS
        ) as conn:
            with conn.cursor() as cur:
                # Check scan_log table
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'scan_log'
                    ORDER BY ordinal_position;
                """)
                scan_log_cols = [row[0] for row in cur.fetchall()]
                
                if scan_log_cols:
                    print(f"✅ scan_log table exists with columns: {', '.join(scan_log_cols)}")
                    if 'pi_hostname' not in scan_log_cols:
                        print("   ⚠️  Missing 'pi_hostname' column - run migration 002")
                else:
                    print("❌ scan_log table not found")
                
                # Check pi_devices table
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'pi_devices'
                    ORDER BY ordinal_position;
                """)
                pi_devices_cols = [row[0] for row in cur.fetchall()]
                
                if pi_devices_cols:
                    print(f"✅ pi_devices table exists with columns: {', '.join(pi_devices_cols)}")
                else:
                    print("⚠️  pi_devices table not found - run migration 001")
                
                return True
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

def check_hostname_registration():
    """Check if this Mac's hostname is registered."""
    hostname = socket.gethostname()
    print(f"\nChecking registration for hostname: {hostname}")
    try:
        with psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASS
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT location, is_active FROM pi_devices WHERE hostname = %s",
                    (hostname,)
                )
                result = cur.fetchone()
                
                if result:
                    location, is_active = result
                    status = "active" if is_active else "inactive"
                    print(f"✅ Registered as: {location} ({status})")
                else:
                    print(f"ℹ️  Not registered - will auto-register as 'UNASSIGNED ({hostname})' on first run")
                
                return True
    except Exception as e:
        print(f"❌ Error checking registration: {e}")
        return False

def run_migrations_check():
    """Provide instructions for running migrations."""
    print("\n" + "="*60)
    print("MIGRATION INSTRUCTIONS")
    print("="*60)
    print("\nIf tables are missing, run these commands:")
    print("\n1. Run migration 001 (creates pi_devices table):")
    print(f"   psql -h {DB_HOST} -U {DB_USER} -d {DB_NAME} -f migrations/001_create_pi_devices.sql")
    print("\n2. Run migration 002 (adds pi_hostname to scan_log):")
    print(f"   psql -h {DB_HOST} -U {DB_USER} -d {DB_NAME} -f migrations/002_add_hostname_to_scan_log.sql")
    print("\nOr run both at once:")
    print(f"   for f in migrations/*.sql; do psql -h {DB_HOST} -U {DB_USER} -d {DB_NAME} -f $f; done")
    print("\n" + "="*60)

if __name__ == "__main__":
    print("="*60)
    print("Beep It - Database Setup Test")
    print("="*60)
    
    if not test_connection():
        print("\n⚠️  Cannot proceed without database connection.")
        print("Check that:")
        print("  1. Tailscale is running and connected")
        print("  2. Database credentials in this file are correct")
        print("  3. PostgreSQL is running on the server")
        exit(1)
    
    check_tables()
    check_hostname_registration()
    run_migrations_check()
    
    print("\n" + "="*60)
    print("Next steps:")
    print("  1. Run migrations if needed (see above)")
    print("  2. Update DB_PASS in scan_gui.py with the real password")
    print("  3. Run: .venv/bin/python3 scan_gui.py")
    print("="*60)
