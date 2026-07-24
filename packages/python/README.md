# Experimental Python package

`packages/python/blueshare/` contains the LAN service and two legacy Python
demonstrations:

- `peer_service.py` provides a standard-library HTTP join, heartbeat, audio
  upload, byte-range streaming, and synchronized media-control service for
  browser peers on one trusted LAN.
- `blueshare.py` models a cost-sharing session in memory.
- `nsiggi.py` models YES/NO/MAYBE echo behaviour.

The peer service is a real LAN transport and media prototype, but it does not
discover or pair Bluetooth devices, select Windows audio outputs, provide TLS,
run as a persistent daemon, or ship as a published package. No packaging
metadata exists yet. Run from the repository root with:

```powershell
python packages/python/blueshare/peer_service.py --bind 127.0.0.1 --port 8765 --pairing-code 246810
python packages/python/blueshare/blueshare.py
python packages/python/blueshare/nsiggi.py
```

The spatial acceptance model remains separate under `acceptance/`.

Run the peer registry tests with:

```powershell
python -m unittest packages.python.tests.test_peer_service packages.python.tests.test_media_room -v
```
