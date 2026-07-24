from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from acceptance.spatial_mvp.model import MMUKOState, Position3D, SpatialNetwork
from acceptance.spatial_mvp.scenario import run_acceptance


BASE_TIME = datetime(2026, 7, 24, 0, 0, tzinfo=timezone.utc)


class SpatialNetworkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.network = SpatialNetwork()
        self.network.add_device("A")
        self.network.add_device("B")
        self.network.connect("A", Position3D(0.0), BASE_TIME)
        self.network.connect("B", Position3D(1.0), BASE_TIME)

    def test_known_distances_are_symmetric_and_in_metres(self) -> None:
        for offset_s, expected_m in enumerate((1.0, 2.0, 5.0, 10.0), start=1):
            result = self.network.update_position(
                "B",
                Position3D(expected_m),
                BASE_TIME + timedelta(seconds=offset_s),
            )
            self.assertTrue(result.accepted)
            self.assertAlmostEqual(self.network.distance_m("A", "B"), expected_m)
            self.assertAlmostEqual(
                self.network.distance_m("A", "B"),
                self.network.distance_m("B", "A"),
            )

    def test_nearest_neighbor_switches_when_b_moves_past_c(self) -> None:
        self.network.add_device("C")
        self.network.connect("C", Position3D(4.25), BASE_TIME)
        self.network.update_position(
            "B", Position3D(4.0), BASE_TIME + timedelta(seconds=1)
        )
        self.assertEqual(self.network.nearest_neighbor("A"), "B")
        self.network.update_position(
            "B", Position3D(5.0), BASE_TIME + timedelta(seconds=2)
        )
        self.assertEqual(self.network.nearest_neighbor("A"), "C")

    def test_disconnect_reconnect_and_stale_rejection(self) -> None:
        self.network.disconnect("B")
        self.assertEqual(self.network.nodes["B"].state, MMUKOState.REMEMBER)
        self.assertFalse(self.network.nodes["B"].connected)

        fresh_at = BASE_TIME + timedelta(seconds=10)
        result = self.network.connect("B", Position3D(2.5), fresh_at)
        self.assertTrue(result.accepted)
        self.assertEqual(self.network.nodes["B"].state, MMUKOState.VERIFIED)

        stale = self.network.update_position(
            "B", Position3D(99.0), BASE_TIME + timedelta(seconds=5)
        )
        self.assertFalse(stale.accepted)
        self.assertEqual(stale.reason, "stale_observation")
        self.assertEqual(self.network.nodes["B"].position, Position3D(2.5))

    def test_unverified_device_is_excluded_from_topology(self) -> None:
        self.network.disconnect("B")
        self.assertIsNone(self.network.nearest_neighbor("A"))
        with self.assertRaisesRegex(ValueError, "no verified position"):
            self.network.distance_m("A", "B")


class AcceptanceScenarioTests(unittest.TestCase):
    def test_complete_scenario_exports_passing_json_and_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            report, json_path, csv_path = run_acceptance(
                Path(temporary_directory), generated_at=BASE_TIME
            )
            self.assertEqual(report["summary"]["status"], "PASS")
            self.assertEqual(
                report["summary"]["checkpoints_observed_m"],
                [1.0, 2.0, 5.0, 10.0],
            )
            self.assertTrue(report["summary"]["movement_monotonic"])
            self.assertTrue(
                report["summary"]["nearest_neighbor_switch"]["passed"]
            )
            self.assertTrue(report["summary"]["stale_coordinate_rejected"])
            self.assertFalse(report["hardware_ranging_validated"])
            self.assertTrue(json_path.exists())
            self.assertTrue(csv_path.exists())

            persisted = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["summary"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()

