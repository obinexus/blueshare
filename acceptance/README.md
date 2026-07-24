# BlueShare Spatial MVP Acceptance

This directory contains the first executable proof for BlueShare's metre-based,
nonpolar spatial topology. It models devices as MMUKO nodes in three-dimensional
Cartesian space and verifies:

- known A-to-B distances at 1, 2, 5, and 10 metres;
- nonpolar symmetry (`A -> B` equals `B -> A`);
- monotonic movement of B away from A;
- nearest-neighbour switching after C joins;
- B disconnect and reconnect through `REMEMBER -> ACTIVE -> VERIFIED`;
- rejection of a stale coordinate after reconnection; and
- timestamped JSON and CSV evidence export.

## Run

From the repository root:

```powershell
python acceptance/run_spatial_acceptance.py
python -m unittest discover -s acceptance/tests -v
```

Reports are written to `acceptance/reports/` by default.

## Scope boundary

The current measurement source is `deterministic-coordinate-simulator`. It
validates spatial topology, lifecycle, ordering, and report semantics. It does
not claim that Bluetooth bandwidth, RSSI, GPS, UWB, or another physical ranging
source has been validated. A hardware adapter must provide timestamped metre
observations and uncertainty before the same acceptance contract can prove
real-world ranging accuracy.

