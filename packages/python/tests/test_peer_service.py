from __future__ import annotations

import sys
import unittest
from pathlib import Path


PYTHON_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_PACKAGE_ROOT))

from blueshare.peer_service import PeerRegistry, ProtocolError  # noqa: E402


class FakeClock:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def join_payload(
    client_id: str,
    name: str,
    position: tuple[float, float, float],
    position_seq: int = 1,
    pairing_code: str = "246810",
) -> dict[str, object]:
    return {
        "pairing_code": pairing_code,
        "client_id": client_id,
        "name": name,
        "position": {"u": position[0], "v": position[1], "w": position[2]},
        "position_seq": position_seq,
    }


def heartbeat_payload(
    session: dict[str, object],
    position: tuple[float, float, float],
    position_seq: int,
) -> dict[str, object]:
    return {
        "peer_id": session["peer_id"],
        "session_token": session["session_token"],
        "position": {"u": position[0], "v": position[1], "w": position[2]},
        "position_seq": position_seq,
    }


class PeerRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.registry = PeerRegistry("246810", timeout_seconds=8.0, clock=self.clock)

    def test_pairing_code_is_required(self) -> None:
        with self.assertRaises(ProtocolError) as context:
            self.registry.join(join_payload("client-0001", "Laptop-A", (0, 0, 0), pairing_code="wrong"))
        self.assertEqual(context.exception.status, 401)
        self.assertEqual(context.exception.code, "pairing_denied")

    def test_join_and_heartbeat_reach_verified(self) -> None:
        joined = self.registry.join(join_payload("client-0001", "Laptop-A", (0, 0, 0)))
        self.assertEqual(joined["state"], "ACTIVE")
        self.assertEqual(joined["connected_peer_count"], 1)

        heartbeat = self.registry.heartbeat(heartbeat_payload(joined, (1, 0, 0), 2))
        self.assertEqual(heartbeat["state"], "VERIFIED")
        self.assertTrue(heartbeat["position_accepted"])
        own_peer = next(peer for peer in heartbeat["peers"] if peer["is_self"])
        self.assertEqual(own_peer["position"], {"u": 1.0, "v": 0.0, "w": 0.0})

    def test_stale_coordinate_is_rejected_without_losing_heartbeat(self) -> None:
        joined = self.registry.join(join_payload("client-0001", "Laptop-A", (1, 2, 3), position_seq=5))
        response = self.registry.heartbeat(heartbeat_payload(joined, (9, 9, 9), 5))
        self.assertEqual(response["state"], "VERIFIED")
        self.assertFalse(response["position_accepted"])
        self.assertEqual(response["position_rejection"], "stale_position_seq")
        own_peer = next(peer for peer in response["peers"] if peer["is_self"])
        self.assertEqual(own_peer["position"], {"u": 1.0, "v": 2.0, "w": 3.0})

    def test_distance_is_symmetric_between_two_peers(self) -> None:
        laptop_a = self.registry.join(join_payload("client-0001", "Laptop-A", (0, 0, 0)))
        laptop_b = self.registry.join(join_payload("client-0002", "Laptop-B", (3, 4, 0)))

        distance_b_to_a = next(
            peer["distance_from_requester_m"] for peer in laptop_b["peers"] if peer["name"] == "Laptop-A"
        )
        view_from_a = self.registry.heartbeat(heartbeat_payload(laptop_a, (0, 0, 0), 2))
        distance_a_to_b = next(
            peer["distance_from_requester_m"] for peer in view_from_a["peers"] if peer["name"] == "Laptop-B"
        )
        self.assertEqual(distance_a_to_b, 5.0)
        self.assertEqual(distance_b_to_a, 5.0)

    def test_timeout_enters_remember_and_heartbeat_recovers(self) -> None:
        joined = self.registry.join(join_payload("client-0001", "Laptop-A", (0, 0, 0)))
        self.registry.heartbeat(heartbeat_payload(joined, (0, 0, 0), 2))
        self.clock.advance(9.0)

        health = self.registry.health()
        self.assertEqual(health["connected_peer_count"], 0)

        recovered = self.registry.heartbeat(heartbeat_payload(joined, (1, 0, 0), 3))
        self.assertTrue(recovered["recovered"])
        self.assertEqual(recovered["state"], "ACTIVE")
        verified = self.registry.heartbeat(heartbeat_payload(joined, (2, 0, 0), 4))
        self.assertFalse(verified["recovered"])
        self.assertEqual(verified["state"], "VERIFIED")

    def test_rejoin_rotates_session_and_rejects_old_token(self) -> None:
        first = self.registry.join(join_payload("client-0001", "Laptop-A", (0, 0, 0)))
        second = self.registry.join(join_payload("client-0001", "Laptop-A", (1, 0, 0), position_seq=2))
        self.assertEqual(first["peer_id"], second["peer_id"])
        self.assertNotEqual(first["session_token"], second["session_token"])
        with self.assertRaises(ProtocolError) as context:
            self.registry.heartbeat(heartbeat_payload(first, (2, 0, 0), 3))
        self.assertEqual(context.exception.code, "invalid_session")

    def test_leave_removes_peer_from_topology(self) -> None:
        joined = self.registry.join(join_payload("client-0001", "Laptop-A", (0, 0, 0)))
        left = self.registry.leave({"peer_id": joined["peer_id"], "session_token": joined["session_token"]})
        self.assertEqual(left["state"], "LEFT")
        self.assertEqual(self.registry.health()["connected_peer_count"], 0)


if __name__ == "__main__":
    unittest.main()
