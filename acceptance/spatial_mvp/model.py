"""Deterministic spatial network model for the BlueShare MVP.

The model deliberately separates topology correctness from physical ranging.
Positions are expressed in metres and act as a deterministic ranging source for
the first acceptance slice. A hardware adapter can later provide observations
using the same distance-and-timestamp contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import dist
from typing import Dict, Optional


class MMUKOState(str, Enum):
    """Network-facing MMUKO lifecycle used by the BlueShare MVP."""

    SPARSE = "SPARSE"
    REMEMBER = "REMEMBER"
    ACTIVE = "ACTIVE"
    VERIFIED = "VERIFIED"


_ALLOWED_TRANSITIONS = {
    MMUKOState.SPARSE: {MMUKOState.REMEMBER},
    MMUKOState.REMEMBER: {MMUKOState.ACTIVE},
    MMUKOState.ACTIVE: {MMUKOState.VERIFIED, MMUKOState.REMEMBER},
    MMUKOState.VERIFIED: {MMUKOState.ACTIVE, MMUKOState.REMEMBER},
}


@dataclass(frozen=True)
class Position3D:
    """Cartesian position in metres."""

    x_m: float
    y_m: float = 0.0
    z_m: float = 0.0

    def distance_to(self, other: "Position3D") -> float:
        return dist(
            (self.x_m, self.y_m, self.z_m),
            (other.x_m, other.y_m, other.z_m),
        )

    def as_dict(self) -> Dict[str, float]:
        return {"x_m": self.x_m, "y_m": self.y_m, "z_m": self.z_m}


@dataclass
class DeviceNode:
    """A physical device indexed by the spatial topology."""

    node_id: str
    state: MMUKOState = MMUKOState.SPARSE
    connected: bool = False
    position: Optional[Position3D] = None
    last_observed_at: Optional[datetime] = None

    def transition(self, next_state: MMUKOState) -> None:
        if next_state == self.state:
            return
        allowed = _ALLOWED_TRANSITIONS[self.state]
        if next_state not in allowed:
            raise ValueError(
                f"illegal MMUKO transition for {self.node_id}: "
                f"{self.state.value} -> {next_state.value}"
            )
        self.state = next_state


@dataclass(frozen=True)
class PositionUpdateResult:
    accepted: bool
    reason: str


class SpatialNetwork:
    """Time-varying device graph with symmetric metre-based edge weights."""

    def __init__(self) -> None:
        self.nodes: Dict[str, DeviceNode] = {}

    def add_device(self, node_id: str) -> DeviceNode:
        if node_id in self.nodes:
            raise ValueError(f"duplicate device: {node_id}")
        node = DeviceNode(node_id=node_id)
        self.nodes[node_id] = node
        node.transition(MMUKOState.REMEMBER)
        return node

    def connect(
        self,
        node_id: str,
        position: Position3D,
        observed_at: datetime,
    ) -> PositionUpdateResult:
        node = self._node(node_id)
        if node.state == MMUKOState.VERIFIED:
            node.transition(MMUKOState.ACTIVE)
        elif node.state == MMUKOState.REMEMBER:
            node.transition(MMUKOState.ACTIVE)
        elif node.state != MMUKOState.ACTIVE:
            raise ValueError(
                f"device {node_id} cannot connect from {node.state.value}"
            )

        node.connected = True
        result = self.update_position(node_id, position, observed_at)
        if not result.accepted:
            node.connected = False
            node.transition(MMUKOState.REMEMBER)
            return result
        node.transition(MMUKOState.VERIFIED)
        return result

    def disconnect(self, node_id: str) -> None:
        node = self._node(node_id)
        node.connected = False
        if node.state in (MMUKOState.ACTIVE, MMUKOState.VERIFIED):
            node.transition(MMUKOState.REMEMBER)

    def update_position(
        self,
        node_id: str,
        position: Position3D,
        observed_at: datetime,
    ) -> PositionUpdateResult:
        node = self._node(node_id)
        if not node.connected or node.state not in (
            MMUKOState.ACTIVE,
            MMUKOState.VERIFIED,
        ):
            return PositionUpdateResult(False, "node_not_active")
        if (
            node.last_observed_at is not None
            and observed_at <= node.last_observed_at
        ):
            return PositionUpdateResult(False, "stale_observation")
        node.position = position
        node.last_observed_at = observed_at
        return PositionUpdateResult(True, "accepted")

    def distance_m(self, node_a: str, node_b: str) -> float:
        """Return a symmetric Euclidean edge weight in metres."""

        a = self._verified_position(node_a)
        b = self._verified_position(node_b)
        return a.distance_to(b)

    def nearest_neighbor(self, node_id: str) -> Optional[str]:
        origin = self._verified_position(node_id)
        candidates = []
        for candidate_id, candidate in self.nodes.items():
            if candidate_id == node_id or not self._is_verified(candidate):
                continue
            assert candidate.position is not None
            candidates.append(
                (origin.distance_to(candidate.position), candidate_id)
            )
        if not candidates:
            return None
        return min(candidates)[1]

    def state_snapshot(self) -> Dict[str, str]:
        return {
            node_id: node.state.value
            for node_id, node in sorted(self.nodes.items())
        }

    def _node(self, node_id: str) -> DeviceNode:
        try:
            return self.nodes[node_id]
        except KeyError as error:
            raise KeyError(f"unknown device: {node_id}") from error

    @staticmethod
    def _is_verified(node: DeviceNode) -> bool:
        return (
            node.connected
            and node.state == MMUKOState.VERIFIED
            and node.position is not None
        )

    def _verified_position(self, node_id: str) -> Position3D:
        node = self._node(node_id)
        if not self._is_verified(node):
            raise ValueError(f"device {node_id} has no verified position")
        assert node.position is not None
        return node.position

