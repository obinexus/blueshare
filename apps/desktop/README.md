# BlueShare LAN browser client

This directory contains the first working web client for the BlueShare LAN peer
service:

- `index.html`: accessible join and topology interface;
- `styles.css`: responsive local-only presentation; and
- `app.js`: pairing, session, heartbeat, recovery, position, media-room, and
  leave flow.

The client is served by
`packages/python/blueshare/peer_service.py`. It has no external JavaScript,
font, analytics, telemetry, or cloud dependency. A second laptop needs only a
modern browser on the same trusted LAN.

## Run

From the repository root, choose a temporary pairing code and bind to the host's
trusted LAN address:

```powershell
python packages\python\blueshare\peer_service.py `
  --bind 192.168.1.117 `
  --port 8765 `
  --pairing-code 246810
```

Both laptops then open `http://192.168.1.117:8765/`, enter distinct device
names, enter the same pairing code, and provide manual `(U,V,W)` coordinates in
metres.

After joining, each Windows peer selects **Enable this speaker**. Any verified
peer can choose an audio file, upload it to the room, and use the shared
play/pause/seek/stop controls. Each device keeps its own volume and sends audio
to the output selected in Windows Sound settings, including a locally paired
Bluetooth headset.

## Scope

This is a real browser-to-host HTTP connection with join, heartbeat, peer
expiry, session recovery, stale-coordinate rejection, in-memory topology,
single-track audio upload, byte-range streaming, and synchronized room control.
It is not a packaged desktop shell, operating-system service, Bluetooth
discovery/pairing adapter, physical ranging implementation, Windows audio
router, hotspot controller, or production authentication system.

The current HTTP transport and pairing code are suitable only for a trusted
local network. Session tokens and coordinates are held in memory and disappear
when the host process stops.
