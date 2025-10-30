#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import socket
from datetime import datetime
import threading
import time

# ---------- CONFIG ----------
DB_HOST = "10.69.1.52"   # Windows Server (Internal network)
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "RxpJcA7FZRiUCPXhLX8T"
LOCATION_REFRESH_INTERVAL = 300  # Refresh location from DB every 5 minutes (in seconds)
# ----------------------------


def get_hostname():
    """Get the Pi's hostname for unique identification."""
    try:
        return socket.gethostname()
    except Exception:
        return "unknown-pi"


def get_pi_ip():
    """Get the Pi's IP address for display purposes."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"


def ensure_pi_devices_table():
    """Check if pi_devices table exists and create it if not."""
    try:
        with psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASS
        ) as conn:
            with conn.cursor() as cur:
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'pi_devices'
                    )
                """)
                table_exists = cur.fetchone()[0]
                
                if not table_exists:
                    # Create the table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS pi_devices (
                            hostname VARCHAR(255) PRIMARY KEY,
                            location VARCHAR(255) NOT NULL,
                            is_active BOOLEAN DEFAULT TRUE,
                            last_seen TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    # Create index
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_pi_devices_active 
                        ON pi_devices(is_active)
                    """)
                    conn.commit()
                    print("✓ Created pi_devices table")
                    return True
                else:
                    return True
    except Exception as e:
        print(f"Error ensuring pi_devices table: {e}")
        return False


def fetch_location_from_db(hostname):
    """Fetch assigned location for this Pi from pi_devices table.
    
    Returns tuple: (location_string, error_message)
    If successful, error_message is None.
    """
    try:
        with psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASS
        ) as conn:
            with conn.cursor() as cur:
                # Fetch location and update last_seen
                cur.execute(
                    """SELECT location, is_active FROM pi_devices WHERE hostname = %s""",
                    (hostname,)
                )
                result = cur.fetchone()
                
                if result is None:
                    # Pi not registered - auto-register with placeholder location
                    placeholder = f"UNASSIGNED ({hostname})"
                    cur.execute(
                        """INSERT INTO pi_devices (hostname, location, is_active, last_seen) 
                           VALUES (%s, %s, FALSE, %s)
                           ON CONFLICT (hostname) DO NOTHING""",
                        (hostname, placeholder, datetime.utcnow())
                    )
                    conn.commit()
                    return placeholder, "⚠️  This Pi is not registered. Admin must assign a location."
                
                location, is_active = result
                
                if not is_active:
                    return location, "⚠️  This Pi is marked as inactive."
                
                # Update last_seen timestamp
                cur.execute(
                    """UPDATE pi_devices SET last_seen = %s WHERE hostname = %s""",
                    (datetime.utcnow(), hostname)
                )
                conn.commit()
                
                return location, None
                
    except Exception as e:
        return f"ERROR: {hostname}", f"Database error: {e}"


def insert_scan(job_number, hostname, location):
    """Insert scan in background thread. Scanned value is the job number."""
    pi_ip = get_pi_ip()
    scanned_at = datetime.utcnow()
    sql = """
        INSERT INTO scan_log (job_number, barcode, pi_ip, pi_hostname, location, scanned_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        with psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASS
        ) as conn:
            with conn.cursor() as cur:
                # Insert scanned value as the job_number. For compatibility, also store it in barcode.
                cur.execute(sql, (job_number, job_number, pi_ip, hostname, location, scanned_at))
                conn.commit()
        return True, f"[{scanned_at.strftime('%H:%M:%S')}] {job_number} → OK"
    except Exception as e:
        return False, f"[ERROR] {e}"


class ScanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Beep It – Job Scanner")
        self.geometry("1024x420")
        self.configure(bg="#c9c9c9")
        self.minsize(900, 360)
        
        # Pi identification
        self.hostname = get_hostname()
        self.location = "Loading..."
        self.location_error = None

        # Fonts
        label_font = ("Segoe UI", 28)
        field_font = ("Segoe UI", 36, "bold")
        input_font = ("Consolas", 32)

        container = tk.Frame(self, bg="#c9c9c9")
        container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Grid config
        container.grid_columnconfigure(0, weight=0)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=0)
        container.grid_rowconfigure(2, weight=1)

        # Location row
        loc_label = tk.Label(container, text="Location:", bg="#c9c9c9", fg="#111",
                             font=label_font, anchor="w")
        loc_label.grid(row=0, column=0, padx=(0, 20), pady=(0, 20), sticky="w")

        self.loc_var = tk.StringVar(value=self.location)
        self.loc_box = tk.Label(container, textvariable=self.loc_var, font=field_font, bg="#e6e6e6",
                           fg="#111", bd=2, relief="ridge", padx=18, pady=6)
        self.loc_box.grid(row=0, column=1, sticky="ew", pady=(0, 20))

        # Job scan row
        job_label = tk.Label(container, text="Job # Scan:", bg="#c9c9c9", fg="#111",
                             font=label_font, anchor="w")
        job_label.grid(row=1, column=0, padx=(0, 20), pady=(0, 20), sticky="w")

        self.barcode_var = tk.StringVar()
        self.barcode_entry = tk.Entry(container, textvariable=self.barcode_var,
                                      font=input_font, bd=2, relief="ridge")
        self.barcode_entry.grid(row=1, column=1, sticky="ew", pady=(0, 20))
        self.barcode_entry.focus_set()

        # Scanned value display (renders immediately before DB call)
        scanned_label = tk.Label(container, text="Scanned:", bg="#c9c9c9", fg="#111",
                                 font=label_font, anchor="w")
        scanned_label.grid(row=2, column=0, padx=(0, 20), pady=(0, 10), sticky="w")

        self.scanned_var = tk.StringVar(value="")
        self.scanned_box = tk.Label(container, textvariable=self.scanned_var, font=field_font,
                                    bg="#e6e6e6", fg="#111", bd=2, relief="ridge",
                                    padx=18, pady=6)
        self.scanned_box.grid(row=2, column=1, sticky="ew", pady=(0, 10))

        # Inline status message
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(container, textvariable=self.status_var,
                                     bg="#c9c9c9", fg="#444", font=("Segoe UI", 14))
        self.status_label.grid(row=3, column=0, columnspan=2, sticky="w")

        # Bottom bar with time, hostname, and IP
        bottom = tk.Frame(self, bg="#c9c9c9")
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=16, pady=10)

        self.clock_label = tk.Label(bottom, text="", bg="#c9c9c9",
                                    fg="#111", font=("Segoe UI", 12))
        self.clock_label.pack(side=tk.LEFT)

        hostname_text = f"Hostname: {self.hostname}"
        self.hostname_label = tk.Label(bottom, text=hostname_text, bg="#c9c9c9",
                                      fg="#111", font=("Segoe UI", 12))
        self.hostname_label.pack(side=tk.LEFT, padx=(20, 0))

        ip_text = f"IP: {get_pi_ip()}"
        self.ip_label = tk.Label(bottom, text=ip_text, bg="#c9c9c9",
                                 fg="#111", font=("Segoe UI", 12))
        self.ip_label.pack(side=tk.RIGHT)

        # Start background tasks
        self.update_clock()
        self.refresh_location()
        self.schedule_location_refresh()

        # Bind Enter key
        self.barcode_entry.bind("<Return>", self.handle_scan)

    def handle_scan(self, event):
        job_number = self.barcode_var.get().strip()
        if not job_number:
            return
        # Render scanned value immediately before starting DB call
        self.scanned_var.set(job_number)
        self.status_var.set(f"Scanning: {job_number}")
        self.barcode_var.set("")
        threading.Thread(target=self.log_to_db, args=(
            job_number,), daemon=True).start()

    def log_to_db(self, job_number):
        ok, msg = insert_scan(job_number, self.hostname, self.location)
        self.log_message(msg, error=not ok)

    def log_message(self, message, error=False):
        self.status_var.set(message)
        self.status_label.config(fg=("red" if error else "#444"))
        self.barcode_entry.focus_set()

    def update_clock(self):
        now = datetime.now().strftime("%m/%d/%Y %I:%M %p")
        self.clock_label.config(text=now)
        self.after(1000, self.update_clock)
    
    def refresh_location(self):
        """Fetch location from database in background thread."""
        threading.Thread(target=self._fetch_location_task, daemon=True).start()
    
    def _fetch_location_task(self):
        """Background task to fetch location from DB."""
        location, error = fetch_location_from_db(self.hostname)
        self.location = location
        self.location_error = error
        
        # Update UI on main thread
        self.after(0, self._update_location_ui)
    
    def _update_location_ui(self):
        """Update location display in UI (runs on main thread)."""
        self.loc_var.set(self.location)
        
        # Show warning in status if there's an error
        if self.location_error:
            self.status_var.set(self.location_error)
            self.status_label.config(fg="orange")
        elif "Loading" not in self.location:
            self.status_var.set("Ready")
            self.status_label.config(fg="#444")
    
    def schedule_location_refresh(self):
        """Periodically refresh location from database."""
        self.refresh_location()
        # Schedule next refresh
        self.after(LOCATION_REFRESH_INTERVAL * 1000, self.schedule_location_refresh)


if __name__ == "__main__":
    # Ensure database tables exist before starting GUI
    ensure_pi_devices_table()
    app = ScanApp()
    app.mainloop()
