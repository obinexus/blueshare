# BlueShare

BlueShare is an OBINexus research and prototype repository for representing
nearby devices as topology nodes, measuring simulated spatial relationships in
metres, and exploring MMUKO/NSIGII lifecycle and consensus ideas.

The repository is organized by responsibility and now includes a working
same-LAN browser peer service. It does **not** yet contain a packaged desktop
application, Bluetooth service, physical ranging adapter, Android package, Rust
FFI layer, or production network daemon.

## What currently works

- A deterministic Python spatial MVP with positions and distances in metres.
- Acceptance tests for 1, 2, 5, and 10 metre checkpoints, A/B symmetry,
  continuous movement, nearest-neighbour switching, reconnect recovery, and
  stale-coordinate rejection.
- Timestamped JSON and CSV acceptance reports.
- A standard-library Python LAN service and HTML/CSS/JavaScript client with
  pairing, session tokens, heartbeat, timeout recovery, manual coordinates,
  symmetric peer distances, stale-coordinate rejection, and explicit leave.
- An interactive single-track media room with authenticated audio upload,
  byte-range delivery, and synchronized play/pause/seek/stop across peers.
- Three independent native demonstrations: BlueShare mixed-consent flow,
  Linux NSIGII sampling, and an OpenSSL Node-Zero example.
- Experimental Python NSIGII/BlueShare demonstrations and NumPy graph pruning.

The spatial acceptance source is a deterministic coordinate simulator. Passing
it does not prove real-world Bluetooth, radio, or hardware ranging accuracy.

## Repository map

```text
apps/desktop/                 Same-LAN HTML/CSS/JavaScript peer client
native/blueshare-core/        C sources, public headers, CMake, constitutional driver
packages/python/blueshare/    LAN peer service and Python demonstrations
acceptance/                   Spatial MVP, tests, and retained evidence reports
research/                     Derivative tracing, pruning, and NLM Atlas material
docs/                         Architecture, deployment, specifications, vision, reference
assets/                       Unmodified audio and image references
scripts/                      Build, release, and network compatibility scripts
.github/workflows/            Pruning CI
```

BlueShare2Go remains as a compatibility name at
[`blueshare2go/README.md`](blueshare2go/README.md); canonical source now lives in
the directories above.

## LAN peer service

On a trusted local network, bind the service to the host laptop's LAN address
and choose a temporary pairing code:

```powershell
python packages\python\blueshare\peer_service.py `
  --bind 192.168.1.117 `
  --port 8765 `
  --pairing-code 246810
```

Both laptops open `http://192.168.1.117:8765/`, enter distinct names and the
same pairing code, then join. Coordinates are entered manually in metres; this
version does not infer physical distance from Wi-Fi or Bluetooth signals. Use
the service only on a trusted LAN because protocol version 0.2 uses HTTP rather
than TLS.

To share music, pair one Bluetooth headset to each Windows peer, select it as
that device's Windows sound output, and select **Enable this speaker** in every
BlueShare browser. Any verified peer can then upload an audio file and control
the shared room. See the
[`Windows media-room guide`](docs/deployment/windows-media-room.md).

## Spatial acceptance

From the repository root on Windows:

```powershell
py -3.14 -m unittest discover -s acceptance/tests -v
py -3.14 acceptance/run_spatial_acceptance.py
```

The runner writes timestamped reports to `acceptance/reports/` by default. Four
existing evidence files are intentionally versioned and are not ignored.

## Native build

Windows with CMake and a C compiler:

```powershell
cmake -S . -B build
cmake --build build --config Debug
ctest --test-dir build -C Debug --output-on-failure
```

WSL/Linux:

```bash
bash scripts/build/build-blueshare-core.sh Release
```

Platform-dependent targets are enabled only when their dependencies exist:
OpenSSL controls the Node-Zero demonstration, and Linux `getrandom()` controls
the NSIGII C demonstration. The public header describes a future library API;
no source currently implements that API as a linkable library.

## Python service and demonstrations

```powershell
python packages/python/blueshare/peer_service.py --bind 127.0.0.1 --port 8765 --pairing-code 246810
python packages/python/blueshare/nsiggi.py
python packages/python/blueshare/blueshare.py
```

The first command starts the working browser-to-host LAN prototype. The other
two commands are standalone in-memory simulations.

## Documentation

- [`README2.md`](README2.md) provides detailed Windows, WSL/Linux, CMake,
  Python, test, run, and troubleshooting instructions.
- [`docs/current-status.md`](docs/current-status.md) separates implemented,
  experimental, research, planned, and incomplete work.
- [`docs/repository-audit.md`](docs/repository-audit.md) records the pre-move
  evidence and duplicate analysis.
- [`docs/repository-migration-map.md`](docs/repository-migration-map.md) records
  every executed relocation and removal.
- [`docs/repository-cleanup-report.md`](docs/repository-cleanup-report.md)
  records validation results and remaining gaps.
- [`docs/README.md`](docs/README.md) indexes product and research documents.

## Known incomplete interfaces

The LAN prototype is an interactive foreground process, not an installed
operating-system daemon or `blueshare --desktop` executable. Compatibility
scripts for `blueshare_cli` and `blueshare_test` stop with exit code 2 because
those binaries do not exist. The historical release script is retained but
cannot run without package metadata. See [`scripts/README.md`](scripts/README.md)
and [`native/blueshare-core/README.md`](native/blueshare-core/README.md).

## Project identity

Created by Nnamdi Michael Okpala for OBINexus Computing.

> Share moments that matter.
