# BlueShare current status

Date: 2026-07-24

## Implemented

- A deterministic Python spatial model using three-dimensional positions in
  metres.
- Automated acceptance checks for A/B symmetry, movement, nearest-neighbour
  switching, disconnect/reconnect, MMUKO lifecycle state, and stale-coordinate
  rejection.
- Timestamped JSON and CSV evidence generation.
- A same-LAN Python HTTP service with pairing-code join, opaque session tokens,
  browser heartbeats, timeout/recovery, stale-coordinate rejection, explicit
  leave, and in-memory peer topology.
- A responsive dependency-free HTML/CSS/JavaScript client that shows MMUKO
  state, manual `(U,V,W)` metre coordinates, and symmetric peer distances.
- A single-track trusted-LAN media room with authenticated audio upload,
  capability-protected byte-range streaming, synchronized play/pause/seek/stop,
  per-device volume, and interactive control by any active peer.

The acceptance source is `deterministic-coordinate-simulator`; it does not
validate physical ranging hardware.

## Experimental

- A standalone C BlueShare session/cost-sharing demonstration.
- Standalone C and Python NSIGII demonstrations.
- A standalone OpenSSL Node-Zero demonstration.
- A Python BlueShare session/payment simulation.
- A NumPy graph-pruning operator.

These legacy demonstrations are separate from the LAN peer service. Several
printed claims inside them are illustrative and are not verified by the
repository.

## Research

The repository preserves BPETS, derivative tracing, NLM Atlas, graph-pruning,
freedom-of-dexterity, and topology material. Research documents do not prove
that corresponding runtime or hardware features exist.

## Planned

- A packaged desktop shell around the existing local service and web client.
- A persistent operating-system service with production identity and TLS.
- Rust-to-C FFI and a native service runtime.
- Android-compatible packaging.
- Real device discovery and ranging adapters.

No Rust, Vue, Vite, Turbo, NW.js, Java, or Android implementation is present
after repository cleanup.

## Incomplete or unavailable

- No packaged desktop application or NW.js manifest.
- No Bluetooth scan, pair, media, hotspot, routing, or Internet Connection
  Sharing implementation. Windows remains responsible for routing browser audio
  to each locally paired Bluetooth output.
- No persistent network daemon, encrypted transport, or production
  authentication. Protocol 0.1 is an in-memory trusted-LAN prototype.
- No physical metre-ranging adapter.
- No implemented C library behind `blueshare_core.h`.
- No `blueshare_cli` or `blueshare_test` executable.
- No Lightning Network integration or real payment processing.
- No package metadata for the historical npm release script.
- No Android SDK project or package.

## Compatibility

The public BlueShare2Go name remains at `blueshare2go/README.md`, which redirects
to the new native, Python, script, and documentation locations without
duplicating source.
