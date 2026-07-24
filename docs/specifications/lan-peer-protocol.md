# BlueShare LAN peer and media protocol 0.2

Status: implemented vertical slice

Transport: same-origin HTTP/1.1 and JSON on a trusted LAN
Reference service: `packages/python/blueshare/peer_service.py`

## Purpose

The protocol establishes a real browser-to-host connection for two or more
laptops. It provides peer join, periodic heartbeat, timeout, MMUKO-style
recovery, manual spatial coordinates, nonpolar distance symmetry,
stale-coordinate rejection, explicit leave, audio upload, byte-range delivery,
and synchronized room transport controls.

It does not define Bluetooth discovery or pairing, Windows output-device
routing, Internet sharing, physical tomography, TLS deployment, or production
identity. Each peer's operating system routes browser audio to its locally
selected Bluetooth or wired output.

## Security boundary

- The host binds to an explicitly selected trusted-LAN address.
- A temporary pairing code authorizes `/api/join`.
- Successful join returns an opaque peer ID and random session token.
- Session-token and pairing-code comparisons are constant-time.
- Tokens are sent only in JSON request bodies and are not written to logs.
- Audio upload requires an active peer ID and session token in request headers.
- Audio streams use a random, track-specific capability key; query strings are
  redacted from service logs and the key expires when the track is replaced.
- Request bodies are limited to 64 KiB.
- Audio uploads have a configurable size limit, defaulting to 256 MiB.
- Peer names and coordinates are validated and bounded.
- The service has no CORS allowance, external scripts, telemetry, or cloud call.

HTTP is not encrypted. Do not use this version on an untrusted network or for
sensitive data.

## Coordinate model

Each peer provides a manual node embedding:

```text
T_G: N -> R^3
T_G(n) = (U_n, V_n, W_n)
```

Coordinates are finite numbers measured in metres. For peers `i` and `j`:

```text
d(i,j) = ||T_G(i) - T_G(j)||_2
d(i,j) = d(j,i)
```

The browser sends a strictly increasing `position_seq`. A coordinate with a
sequence less than or equal to the last accepted value is rejected while the
heartbeat itself remains valid.

## Lifecycle

```text
JOIN -> ACTIVE -> VERIFIED
                    |
                    | heartbeat timeout
                    v
                 REMEMBER
                    |
                    | valid heartbeat
                    v
                  ACTIVE -> VERIFIED
```

An explicit leave enters `LEFT` and removes the peer from public topology
snapshots. Rejoining with the same browser client ID retains the peer ID, rotates
the session token, and increments the reconnect counter.

## Endpoints

### `GET /api/health`

Returns service version, server time, timeout, and connected-peer count. It does
not disclose the pairing code or session tokens.

### `POST /api/join`

Request:

```json
{
  "pairing_code": "246810",
  "client_id": "browser-generated-url-safe-id",
  "name": "Laptop-B",
  "position": {"u": 3.0, "v": 4.0, "w": 0.0},
  "position_seq": 1
}
```

Response includes `peer_id`, `session_token`, state, heartbeat interval, timeout,
next position sequence, recovery status, and the current public topology.

### `POST /api/heartbeat`

Request:

```json
{
  "peer_id": "opaque-uuid",
  "session_token": "opaque-random-token",
  "position": {"u": 3.5, "v": 4.0, "w": 0.0},
  "position_seq": 2
}
```

Response reports `VERIFIED` or recovered `ACTIVE` state, coordinate acceptance,
the next sequence value, and the current public topology. A stale position
returns `position_accepted: false` with
`position_rejection: "stale_position_seq"`.

### `POST /api/leave`

Request contains `peer_id` and `session_token`. The response confirms `LEFT`.

### `POST /api/media/upload`

Uploads one audio file as the current room track. The request body is the raw
audio bytes. Required headers are `Content-Type: audio/*`,
`X-BlueShare-Peer-Id`, `X-BlueShare-Session-Token`, and a URI-encoded
`X-BlueShare-Filename`. A successful upload replaces the previous room track
and returns HTTP 201 with the shared media state.

### `POST /api/media/state`

An authenticated peer polls this endpoint for the room transport snapshot. The
browser client polls every 750 ms. The response includes track identity,
filename, content type, size, `READY`, `PLAYING`, or `PAUSED` state, current
position in seconds, revision, controller identity, and the capability-protected
stream URL.

### `POST /api/media/control`

Any active peer may send `play`, `pause`, `seek`, or `stop`. `seek` requires a
finite non-negative `position_seconds`. Play and pause may include the local
player position so the shared monotonic clock begins from the user's visible
position.

### `GET|HEAD /api/media/stream/{media_id}?key={capability}`

Returns the current audio stream. Single HTTP byte ranges are supported so
browsers can buffer and seek without downloading the complete track first.
Invalid or expired capabilities return 404.

## Media synchronization model

The host owns a monotonic room clock. While state is `PLAYING`:

```text
room_position = base_position + (host_now - started_at)
```

Peers poll the state, correct local drift above 650 ms, and use their local HTML
media decoder. Local volume is never broadcast. Browser autoplay rules require
each peer to select **Enable this speaker** once before remote play commands can
produce sound.

## Topology response

Public peer records include:

- opaque peer ID and display name;
- `ACTIVE`, `VERIFIED`, or `REMEMBER` state;
- manual `(U,V,W)` position and accepted sequence;
- distance from the requesting peer in metres;
- last-seen age, heartbeat count, and reconnect count; and
- whether the record represents the requesting browser.

Client IDs, session tokens, pairing codes, and remote IP addresses are never
included in topology responses.

## Persistence and failure behavior

State is held only in host memory. Restarting the process creates a new session
universe and requires all peers to join again. A browser can survive temporary
packet loss or a server-side heartbeat timeout; its next authorized heartbeat
recovers the retained node through `ACTIVE` before returning to `VERIFIED`.
