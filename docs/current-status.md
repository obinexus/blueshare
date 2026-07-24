# BlueShare current status

Date: 2026-07-24

## Implemented

- A deterministic Python spatial model using three-dimensional positions in
  metres.
- Automated acceptance checks for A/B symmetry, movement, nearest-neighbour
  switching, disconnect/reconnect, MMUKO lifecycle state, and stale-coordinate
  rejection.
- Timestamped JSON and CSV evidence generation.

The acceptance source is `deterministic-coordinate-simulator`; it does not
validate physical ranging hardware.

## Experimental

- A standalone C BlueShare session/cost-sharing demonstration.
- Standalone C and Python NSIGII demonstrations.
- A standalone OpenSSL Node-Zero demonstration.
- A Python BlueShare session/payment simulation.
- A NumPy graph-pruning operator.

These are disconnected demonstrations, not an integrated service. Several
printed claims inside the legacy demos are illustrative and are not verified by
the repository.

## Research

The repository preserves BPETS, derivative tracing, NLM Atlas, graph-pruning,
freedom-of-dexterity, and topology material. Research documents do not prove
that corresponding runtime or hardware features exist.

## Planned

- A desktop-first local BlueShare service.
- A versioned frontend/backend protocol.
- Plain web assets or another approved desktop UI.
- Rust-to-C FFI and a native service runtime.
- Android-compatible packaging.
- Real device discovery and ranging adapters.

No Rust, Vue, Vite, Turbo, NW.js, Java, or Android implementation is present
after repository cleanup.

## Incomplete or unavailable

- No desktop application or NW.js manifest.
- No Bluetooth scan, pair, media, hotspot, routing, or Internet Connection
  Sharing implementation.
- No real network daemon or host-to-host protocol.
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
