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
JOB_NUMBER = "JOB-2025-102"
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

def insert_scan(barcode):
    """Insert scan in background thread."""
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
                cur.execute(sql, (JOB_NUMBER, barcode, pi_ip, LOCATION, scanned_at))
                conn.commit()
        return True, f"[{scanned_at.strftime('%H:%M:%S')}] {barcode} → OK"
    except Exception as e:
        return False, f"[ERROR] {e}"

class ScanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Warehouse Scan Logger")
        self.geometry("800x480")
        self.configure(bg="#1e1e1e")

        # Header
        header = tk.Label(
            self,
            text=f"Job: {JOB_NUMBER}   |   Location: {LOCATION}",
            bg="#333333",
            fg="white",
            font=("Segoe UI", 16),
            pady=10
        )
        header.pack(fill=tk.X)

        # Barcode entry
        entry_frame = tk.Frame(self, bg="#1e1e1e")
        entry_frame.pack(pady=30)
        tk.Label(entry_frame, text="Scan Barcode:", fg="white", bg="#1e1e1e", font=("Segoe UI", 14)).pack()
        self.barcode_var = tk.StringVar()
        self.barcode_entry = ttk.Entry(entry_frame, textvariable=self.barcode_var, font=("Consolas", 20), width=30)
        self.barcode_entry.pack(pady=10)
        self.barcode_entry.focus_set()

        # Log display
        log_frame = tk.Frame(self, bg="#1e1e1e")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.log_box = tk.Text(log_frame, bg="#111111", fg="#00FF00", font=("Consolas", 12))
        self.log_box.pack(fill=tk.BOTH, expand=True)
        self.log_box.insert(tk.END, "System ready...\n")

        # Bind Enter key
        self.barcode_entry.bind("<Return>", self.handle_scan)

    def handle_scan(self, event):
        barcode = self.barcode_var.get().strip()
        if not barcode:
            return
        self.barcode_var.set("")
        self.log_message(f"Scanning: {barcode}")
        threading.Thread(target=self.log_to_db, args=(barcode,), daemon=True).start()

    def log_to_db(self, barcode):
        ok, msg = insert_scan(barcode)
        self.log_message(msg, error=not ok)

    def log_message(self, message, error=False):
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)
        if error:
            self.log_box.tag_add("err", "end-2l", "end-1l")
            self.log_box.tag_config("err", foreground="red")

if __name__ == "__main__":
    app = ScanApp()
    app.mainloop()

