# Private update artifacts (for GitHub Releases)

How to release an update:
- Edit your application code as needed (e.g., scan_gui.py in repo root).
- Copy the updated payload into this folder as scan_gui.py.
- Bump the VERSION file (e.g., 0.1.1 -> 0.1.2).
- Create and push a tag (e.g., v0.1.2). The workflow will:
  - Create a GitHub Release for the tag
  - Attach assets:
    - scan_gui.py
    - scan_gui.py.sha256 (generated)
    - VERSION

Devices fetch from the private GitHub Releases API using a read-only token and will not expose these files publicly.

Payload expectations:
- The device-side updater downloads scan_gui.py and verifies scan_gui.py.sha256.
- It installs to /opt/beep_it/scan_gui.py and (optionally) restarts your service if SERVICE_NAME is configured on the device.
