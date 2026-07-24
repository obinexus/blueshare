"""Executable A/B/C spatial acceptance scenario and evidence export."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .model import MMUKOState, Position3D, SpatialNetwork


MEASUREMENT_SOURCE = "deterministic-coordinate-simulator"
REQUIRED_CHECKPOINTS_M = (1.0, 2.0, 5.0, 10.0)


@dataclass
class AcceptanceEvent:
    timestamp: str
    elapsed_s: float
    event: str
    node_a: str = ""
    node_b: str = ""
    ground_truth_m: Optional[float] = None
    reported_ab_m: Optional[float] = None
    reported_ba_m: Optional[float] = None
    absolute_error_m: Optional[float] = None
    symmetry_delta_m: Optional[float] = None
    tolerance_m: Optional[float] = None
    nearest_to_a: Optional[str] = None
    mmuko_states: Optional[Dict[str, str]] = None
    passed: bool = True
    note: str = ""


def _iso(timestamp: datetime) -> str:
    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _time(base: datetime, elapsed_s: float) -> datetime:
    return base + timedelta(seconds=elapsed_s)


def _record_distance(
    events: List[AcceptanceEvent],
    network: SpatialNetwork,
    base: datetime,
    elapsed_s: float,
    expected_m: float,
    tolerance_m: float,
    event_name: str = "movement_sample",
) -> AcceptanceEvent:
    reported_ab = network.distance_m("A", "B")
    reported_ba = network.distance_m("B", "A")
    error = abs(reported_ab - expected_m)
    symmetry_delta = abs(reported_ab - reported_ba)
    event = AcceptanceEvent(
        timestamp=_iso(_time(base, elapsed_s)),
        elapsed_s=elapsed_s,
        event=event_name,
        node_a="A",
        node_b="B",
        ground_truth_m=expected_m,
        reported_ab_m=reported_ab,
        reported_ba_m=reported_ba,
        absolute_error_m=error,
        symmetry_delta_m=symmetry_delta,
        tolerance_m=tolerance_m,
        nearest_to_a=network.nearest_neighbor("A"),
        mmuko_states=network.state_snapshot(),
        passed=error <= tolerance_m and symmetry_delta <= tolerance_m,
        note="metre checkpoint" if expected_m in REQUIRED_CHECKPOINTS_M else "path sample",
    )
    events.append(event)
    return event


def _write_reports(
    report: Dict[str, Any], output_dir: Path, generated_at: datetime
) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = generated_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"blueshare-spatial-acceptance-{stamp}"
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    rows = report["events"]
    fieldnames = [field.name for field in AcceptanceEvent.__dataclass_fields__.values()]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            csv_row = dict(row)
            csv_row["mmuko_states"] = json.dumps(
                csv_row.get("mmuko_states"), sort_keys=True
            )
            writer.writerow(csv_row)

    return json_path, csv_path


def run_acceptance(
    output_dir: Path,
    *,
    generated_at: Optional[datetime] = None,
    tolerance_m: float = 0.01,
) -> Tuple[Dict[str, Any], Path, Path]:
    """Run the deterministic spatial proof and export JSON/CSV evidence."""

    if tolerance_m < 0:
        raise ValueError("tolerance_m must be non-negative")
    generated_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0)
    if generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")

    network = SpatialNetwork()
    events: List[AcceptanceEvent] = []

    # A is the fixed origin. B begins one metre away.
    network.add_device("A")
    network.add_device("B")
    a_result = network.connect("A", Position3D(0.0), _time(generated_at, 0.0))
    b_result = network.connect("B", Position3D(1.0), _time(generated_at, 0.0))
    events.append(
        AcceptanceEvent(
            timestamp=_iso(generated_at),
            elapsed_s=0.0,
            event="mmuko_bootstrap",
            mmuko_states=network.state_snapshot(),
            passed=(
                a_result.accepted
                and b_result.accepted
                and network.nodes["A"].state == MMUKOState.VERIFIED
                and network.nodes["B"].state == MMUKOState.VERIFIED
            ),
            note="A and B reached VERIFIED",
        )
    )
    _record_distance(events, network, generated_at, 0.0, 1.0, tolerance_m)

    # B moves away at one-metre samples. Required checkpoints are 1, 2, 5, 10.
    # C enters at 4.25 m after B reaches 2 m, causing A's nearest neighbour to
    # switch from B to C when B passes C.
    previous_distance = 1.0
    movement_monotonic = True
    nearest_before_switch: Optional[str] = None
    nearest_after_switch: Optional[str] = None
    for distance_m in range(2, 11):
        elapsed_s = float(distance_m - 1)
        update = network.update_position(
            "B", Position3D(float(distance_m)), _time(generated_at, elapsed_s)
        )
        movement_monotonic = movement_monotonic and update.accepted and distance_m > previous_distance
        previous_distance = float(distance_m)
        sample = _record_distance(
            events,
            network,
            generated_at,
            elapsed_s,
            float(distance_m),
            tolerance_m,
        )

        if distance_m == 2:
            network.add_device("C")
            c_result = network.connect(
                "C", Position3D(4.25), _time(generated_at, elapsed_s + 0.25)
            )
            nearest_before_switch = network.nearest_neighbor("A")
            events.append(
                AcceptanceEvent(
                    timestamp=_iso(_time(generated_at, elapsed_s + 0.25)),
                    elapsed_s=elapsed_s + 0.25,
                    event="device_c_added",
                    node_a="A",
                    node_b="C",
                    ground_truth_m=4.25,
                    reported_ab_m=network.distance_m("A", "C"),
                    absolute_error_m=abs(network.distance_m("A", "C") - 4.25),
                    tolerance_m=tolerance_m,
                    nearest_to_a=nearest_before_switch,
                    mmuko_states=network.state_snapshot(),
                    passed=c_result.accepted and nearest_before_switch == "B",
                    note="B must remain A's nearest neighbour",
                )
            )
        elif distance_m == 5:
            nearest_after_switch = sample.nearest_to_a
            sample.passed = sample.passed and nearest_after_switch == "C"
            sample.note = "nearest neighbour must switch from B to C"

    events.append(
        AcceptanceEvent(
            timestamp=_iso(_time(generated_at, 9.25)),
            elapsed_s=9.25,
            event="movement_monotonicity",
            node_a="A",
            node_b="B",
            mmuko_states=network.state_snapshot(),
            passed=movement_monotonic,
            note="B moved monotonically from 1 m to 10 m",
        )
    )

    # Disconnect B. Identity is remembered but its last coordinate is no longer
    # eligible for topology calculations.
    network.disconnect("B")
    remembered = network.nodes["B"].state == MMUKOState.REMEMBER
    events.append(
        AcceptanceEvent(
            timestamp=_iso(_time(generated_at, 10.0)),
            elapsed_s=10.0,
            event="device_b_disconnected",
            node_a="A",
            node_b="B",
            nearest_to_a=network.nearest_neighbor("A"),
            mmuko_states=network.state_snapshot(),
            passed=remembered and network.nearest_neighbor("A") == "C",
            note="B is REMEMBER and excluded from active topology",
        )
    )

    # Reconnect B at 2.5 m with a fresh timestamp, then attempt to overwrite the
    # position with an older observation. The stale update must be rejected.
    reconnect_at = _time(generated_at, 11.0)
    reconnect = network.connect("B", Position3D(2.5), reconnect_at)
    recovered_position = network.nodes["B"].position
    events.append(
        AcceptanceEvent(
            timestamp=_iso(reconnect_at),
            elapsed_s=11.0,
            event="device_b_reconnected",
            node_a="A",
            node_b="B",
            ground_truth_m=2.5,
            reported_ab_m=network.distance_m("A", "B"),
            absolute_error_m=abs(network.distance_m("A", "B") - 2.5),
            tolerance_m=tolerance_m,
            nearest_to_a=network.nearest_neighbor("A"),
            mmuko_states=network.state_snapshot(),
            passed=(
                reconnect.accepted
                and network.nodes["B"].state == MMUKOState.VERIFIED
                and network.nearest_neighbor("A") == "B"
            ),
            note="fresh observation restores B to VERIFIED",
        )
    )

    stale = network.update_position(
        "B", Position3D(99.0), _time(generated_at, 8.0)
    )
    events.append(
        AcceptanceEvent(
            timestamp=_iso(_time(generated_at, 12.0)),
            elapsed_s=12.0,
            event="stale_coordinate_rejected",
            node_a="A",
            node_b="B",
            reported_ab_m=network.distance_m("A", "B"),
            tolerance_m=tolerance_m,
            nearest_to_a=network.nearest_neighbor("A"),
            mmuko_states=network.state_snapshot(),
            passed=(
                not stale.accepted
                and stale.reason == "stale_observation"
                and network.nodes["B"].position == recovered_position
                and network.distance_m("A", "B") == 2.5
            ),
            note="an older 99 m coordinate did not replace the fresh 2.5 m coordinate",
        )
    )

    event_dicts = [asdict(event) for event in events]
    distance_events = [event for event in events if event.reported_ab_m is not None]
    checkpoint_events = [
        event
        for event in events
        if event.event == "movement_sample"
        and event.ground_truth_m in REQUIRED_CHECKPOINTS_M
    ]
    report_passed = all(event.passed for event in events)
    report = {
        "schema_version": "1.0.0",
        "generated_at": _iso(generated_at),
        "measurement_source": MEASUREMENT_SOURCE,
        "units": "metres",
        "hardware_ranging_validated": False,
        "tolerance_m": tolerance_m,
        "summary": {
            "status": "PASS" if report_passed else "FAIL",
            "events": len(events),
            "distance_samples": len(distance_events),
            "required_checkpoints_m": list(REQUIRED_CHECKPOINTS_M),
            "checkpoints_observed_m": [
                event.ground_truth_m for event in checkpoint_events
            ],
            "max_absolute_error_m": max(
                (event.absolute_error_m or 0.0) for event in distance_events
            ),
            "max_symmetry_delta_m": max(
                (event.symmetry_delta_m or 0.0) for event in distance_events
            ),
            "movement_monotonic": movement_monotonic,
            "nearest_neighbor_switch": {
                "from": nearest_before_switch,
                "to": nearest_after_switch,
                "passed": nearest_before_switch == "B" and nearest_after_switch == "C",
            },
            "disconnect_reconnect_passed": remembered and reconnect.accepted,
            "stale_coordinate_rejected": not stale.accepted,
        },
        "limitations": [
            "This run validates topology logic against deterministic coordinates.",
            "It does not validate Bluetooth, GPS, UWB, RSSI, or other hardware ranging accuracy.",
        ],
        "events": event_dicts,
    }
    json_path, csv_path = _write_reports(report, output_dir, generated_at)
    return report, json_path, csv_path

