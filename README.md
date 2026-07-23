# OBINexus BlueShare

**Created by:** Nnamdi Michael Okpala<br>
**Division:** OBINexus Computing<br>
**Motto:** Share moments that matter.

## What It Is

BlueShare is a real-time tethering and sharing platform intended to turn nearby devices into a small, resilient network. Instead of every person relying on an isolated connection or playback device, BlueShare aims to let participants share media timing, files, folders, connectivity, and live session state.

It is designed for connection that feels natural:
a house full of people working quietly, a team syncing ideas, or friends sharing the same track at the same second.

## How It Works

BlueShare builds sessions from nodes and links arranged as bus, ring, mesh, or other resolved topologies. The intended desktop application will use the MMUKO boot lifecycle to determine whether its local node and current topology are ready:

```text
SPARSE -> REMEMBER -> ACTIVE -> VERIFY
```

Readiness is reported using NSIGII-style outcomes:

- `YES`: topology and node readiness are verified.
- `NO`: a deterministic failure occurred.
- `MAYBE`: discovery or verification is incomplete.

These terms describe application state and topology resolution. They must not be presented as physical quantum computing.

## Why It Exists

BlueShare is not limited to Bluetooth. Its broader purpose is to provide a transport-independent sharing protocol that can eventually work across Bluetooth, local networking, Wi-Fi, and other supported links.

The first desktop iteration will use a deterministic simulated transport. Simulation must be labelled honestly; it is not real Bluetooth support.

## Repository Status

BlueShare is currently in the repository-audit and architecture stage. A complete desktop application does not yet exist in this repository.

Current material includes:

- Product and research documentation under `blueshare-polyglot-exosketelon/`.
- An untracked legacy C/Python prototype under `blueshare2go/`.
- Standalone demonstrations of topology, NSIGII-style state, privacy concepts, and graph pruning.

The legacy prototype is not a production implementation. Its existing CMake file references missing sources, its C programs are disconnected demonstrations, and its Python files are not an automated test suite.

## Target Architecture

The planned desktop monorepo separates responsibilities across these layers:

```text
apps/desktop/                 Vue, Vite, plain CSS, and NW.js shell
packages/protocol/            Versioned frontend/backend message contract
crates/blueshare-runtime/     Safe Rust runtime, daemon, transport, and FFI
native/blueshare-core/        Deterministic C11 MMUKO and topology core
docs/                         Audit, architecture, protocol, build, and test records
```

The first working vertical slice will:

1. Start the local NW.js desktop application.
2. Launch the Rust backend.
3. Load the native C core.
4. Create a privacy-preserving local node identity.
5. Run MMUKO boot and display phase events.
6. Add a simulated peer and resolve a two-node topology.
7. Simulate shared-media timing and peer reconnection.
8. Shut down without leaving a backend process running.

## Source-of-Truth Policy

Implementation semantics must come from:

- Files already present in this repository.
- Static OBINexus documentation available locally.
- Repositories and documentation owned by [`obinexus`](https://github.com/obinexus) or [`obinexusmk2`](https://github.com/obinexusmk2).
- In particular, [`obinexus/mmuko-os`](https://github.com/obinexus/mmuko-os) and its `boot/mmuko_boot.psc` specification.

Undefined terms and temporary engineering interpretations must be recorded in `docs/OPEN_QUESTIONS.md`. The project must not invent hardware identity, topology, or MMUKO semantics and present them as verified OBINexus rules.

## Safety and Privacy

- Never log, display, or transmit a raw motherboard serial, MAC address, machine GUID, or operating-system hardware identifier.
- Keep unsafe Rust isolated to the FFI boundary with explicit safety documentation.
- Validate all frontend input in the Rust backend.
- Use bounded retries and deadlines; never retry forever.
- Require local frontend assets and avoid telemetry or cloud dependencies.
- Preserve existing user work and do not change project licences as part of implementation.

## Planned Developer Interface

Once the desktop scaffold is implemented, the repository root will provide:

```text
npm run dev
npm run build
npm run preview
npm run test
npm run check
npm run desktop
```

These commands are targets, not claims about the repository's current runnable state.

## Learn More

You can explore the ongoing work at [github.com/obinexus/blueshare](https://github.com/obinexus/blueshare).

The future is shared.
**Share with BlueShare.**
