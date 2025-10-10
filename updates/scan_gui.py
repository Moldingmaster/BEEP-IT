#!/usr/bin/env python3
# Copied from repo root at initial setup; keep this file updated with your latest application code
# This copy is published to GitHub Pages for devices to fetch.

#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import socket
from datetime import datetime
import threading

# ---------- CONFIG ----------
DB_HOST = "100.75.187.68"   # Windows Server (Tailscale IP)
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "your_password"
LOCATION = "North Warehouse Aisle 3"
# ----------------------------


def get_pi_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"


def insert_scan(job_number):
    """Insert scan in background thread. Scanned value is the job number."""
    pi_ip = get_pi_ip()
    scanned_at = datetime.utcnow()
    sql = """
        INSERT INTO scan_log (job_number, barcode, pi_ip, location, scanned_at)
        VALUES (%s, %s, %s, %s, %s)
    """
    try:
        with psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASS
        ) as conn:
            with conn.cursor() as cur:
                # Insert scanned value as the job_number. For compatibility, also store it in barcode.
                cur.execute(sql, (job_number, job_number,
                            pi_ip, LOCATION, scanned_at))
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

        loc_box = tk.Label(container, text=LOCATION, font=field_font, bg="#e6e6e6",
                           fg="#111", bd=2, relief="ridge", padx=18, pady=6)
        loc_box.grid(row=0, column=1, sticky="ew", pady=(0, 20))

        # Job scan row
        job_label = tk.Label(container, text="Job # Scan:", bg="#c9c9c9", fg="#111",
                             font=label_font, anchor="w")
        job_label.grid(row=1, column=0, padx=(0, 20), pady=(0, 20), sticky="w")

        self.barcode_var = tk.StringVar()
        self.barcode_entry = tk.Entry(container, textvariable=self.barcode_var,
                                      font=input_font, bd=2, relief="ridge")
        self.barcode_entry.grid(row=1, column=1, sticky="ew", pady=(0, 20))
        self.barcode_entry.focus_set()

        # Inline status message
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(container, textvariable=self.status_var,
                                     bg="#c9c9c9", fg="#444", font=("Segoe UI", 14))
        self.status_label.grid(row=2, column=0, columnspan=2, sticky="w")

        # Bottom bar with time and IP
        bottom = tk.Frame(self, bg="#c9c9c9")
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=16, pady=10)

        self.clock_label = tk.Label(bottom, text="", bg="#c9c9c9",
                                    fg="#111", font=("Segoe UI", 12))
        self.clock_label.pack(side=tk.LEFT)

        ip_text = f"IP: {get_pi_ip()}"
        self.ip_label = tk.Label(bottom, text=ip_text, bg="#c9c9c9",
                                 fg="#111", font=("Segoe UI", 12))
        self.ip_label.pack(side=tk.RIGHT)

        self.update_clock()

        # Bind Enter key
        self.barcode_entry.bind("<Return>", self.handle_scan)

    def handle_scan(self, event):
        job_number = self.barcode_var.get().strip()
        if not job_number:
            return
        self.status_var.set(f"Scanning: {job_number}")
        self.barcode_var.set("")
        threading.Thread(target=self.log_to_db, args=(
            job_number,), daemon=True).start()

    def log_to_db(self, job_number):
        ok, msg = insert_scan(job_number)
        self.log_message(msg, error=not ok)

    def log_message(self, message, error=False):
        self.status_var.set(message)
        self.status_label.config(fg=("red" if error else "#444"))
        self.barcode_entry.focus_set()

    def update_clock(self):
        now = datetime.now().strftime("%m/%d/%Y %I:%M %p")
        self.clock_label.config(text=now)
        self.after(1000, self.update_clock)


if __name__ == "__main__":
    app = ScanApp()
    app.mainloop()
