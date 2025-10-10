# Files in this folder are published to GitHub Pages for device updates

How to release an update:
- Edit your application code as needed (e.g., scan_gui.py in repo root).
- Copy the updated payload into this folder as scan_gui.py.
- Bump the VERSION file (e.g., 0.1.1 -> 0.1.2).
- Commit and push changes to main. The GitHub Action will publish:
  - VERSION
  - scan_gui.py
  - scan_gui.py.sha256 (generated)

Devices will fetch from:
  https://themadbotterinc.github.io/Maverick-Beep-It/

Payload expectations:
- The device-side updater downloads scan_gui.py and verifies scan_gui.py.sha256.
- It installs to /opt/beep_it/scan_gui.py and (optionally) restarts your service if SERVICE_NAME is configured on the device.
