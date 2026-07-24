#!/usr/bin/env python3
"""BlueShare LAN peer join and heartbeat service.

This is a small standard-library vertical slice. It provides a real HTTP
connection between browser peers on one trusted LAN while keeping positioning
explicitly manual and measured in metres.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, BinaryIO, Callable
from urllib.parse import parse_qs, unquote, urlsplit


SERVICE_VERSION = "0.2.0"
MAX_BODY_BYTES = 64 * 1024
DEFAULT_MAX_MEDIA_BYTES = 256 * 1024 * 1024
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,47}$")
CLIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
PAIRING_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{4,32}$")


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp suitable for protocol responses."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ProtocolError(Exception):
    """A client-visible protocol failure."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Position3D:
    """A manually supplied Cartesian node position in metres."""

    u: float
    v: float
    w: float

    def distance_to(self, other: "Position3D") -> float:
        return math.dist((self.u, self.v, self.w), (other.u, other.v, other.w))

    def as_dict(self) -> dict[str, float]:
        return {"u": self.u, "v": self.v, "w": self.w}


@dataclass
class PeerRecord:
    peer_id: str
    client_id: str
    session_token: str
    name: str
    position: Position3D
    position_seq: int
    state: str
    first_seen: float
    last_seen: float
    heartbeat_count: int = 0
    reconnect_count: int = 0
    remote_address: str = ""


class PeerRegistry:
    """Thread-safe in-memory peer lifecycle and topology registry."""

    def __init__(
        self,
        pairing_code: str,
        timeout_seconds: float = 8.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not PAIRING_CODE_PATTERN.fullmatch(pairing_code):
            raise ValueError("pairing code must be 4-32 letters, numbers, '_' or '-'")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._pairing_code = pairing_code
        self.timeout_seconds = float(timeout_seconds)
        self._clock = clock
        self._lock = threading.RLock()
        self._by_peer_id: dict[str, PeerRecord] = {}
        self._peer_id_by_client_id: dict[str, str] = {}

    @staticmethod
    def _require_object(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ProtocolError(HTTPStatus.BAD_REQUEST, "invalid_payload", "JSON object required")
        return payload

    @staticmethod
    def _validated_name(value: Any) -> str:
        if not isinstance(value, str) or not NAME_PATTERN.fullmatch(value.strip()):
            raise ProtocolError(
                HTTPStatus.BAD_REQUEST,
                "invalid_name",
                "name must be 1-48 safe display characters",
            )
        return value.strip()

    @staticmethod
    def _validated_client_id(value: Any) -> str:
        if not isinstance(value, str) or not CLIENT_ID_PATTERN.fullmatch(value):
            raise ProtocolError(
                HTTPStatus.BAD_REQUEST,
                "invalid_client_id",
                "client_id must be 8-128 URL-safe characters",
            )
        return value

    @staticmethod
    def _validated_position(value: Any) -> Position3D:
        if not isinstance(value, dict):
            raise ProtocolError(HTTPStatus.BAD_REQUEST, "invalid_position", "position object required")
        coordinates: list[float] = []
        for axis in ("u", "v", "w"):
            raw = value.get(axis)
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                raise ProtocolError(
                    HTTPStatus.BAD_REQUEST,
                    "invalid_position",
                    f"position.{axis} must be a finite number",
                )
            coordinate = float(raw)
            if not math.isfinite(coordinate) or abs(coordinate) > 1_000_000:
                raise ProtocolError(
                    HTTPStatus.BAD_REQUEST,
                    "invalid_position",
                    f"position.{axis} is outside the supported metre range",
                )
            coordinates.append(coordinate)
        return Position3D(*coordinates)

    @staticmethod
    def _validated_position_seq(value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ProtocolError(
                HTTPStatus.BAD_REQUEST,
                "invalid_position_seq",
                "position_seq must be a non-negative integer",
            )
        return value

    def _authorize_pairing_code(self, value: Any) -> None:
        if not isinstance(value, str) or not secrets.compare_digest(value, self._pairing_code):
            raise ProtocolError(HTTPStatus.UNAUTHORIZED, "pairing_denied", "pairing code rejected")

    def _authorized_peer(self, payload: dict[str, Any]) -> PeerRecord:
        peer_id = payload.get("peer_id")
        token = payload.get("session_token")
        if not isinstance(peer_id, str) or not isinstance(token, str):
            raise ProtocolError(HTTPStatus.UNAUTHORIZED, "session_required", "peer session required")
        record = self._by_peer_id.get(peer_id)
        if record is None or not secrets.compare_digest(record.session_token, token):
            raise ProtocolError(HTTPStatus.UNAUTHORIZED, "invalid_session", "peer session rejected")
        return record

    def authorize_session(self, payload: Any) -> PeerRecord:
        """Return an active peer for an authenticated non-heartbeat operation."""

        body = self._require_object(payload)
        now = self._clock()
        with self._lock:
            self._refresh_states(now)
            record = self._authorized_peer(body)
            if record.state not in {"ACTIVE", "VERIFIED"}:
                raise ProtocolError(
                    HTTPStatus.CONFLICT,
                    "peer_not_active",
                    "peer must have an active heartbeat before using media controls",
                )
            return record

    def _refresh_states(self, now: float) -> None:
        for record in self._by_peer_id.values():
            if record.state in {"ACTIVE", "VERIFIED"} and now - record.last_seen > self.timeout_seconds:
                record.state = "REMEMBER"

    def _public_peer(self, record: PeerRecord, requester: PeerRecord | None, now: float) -> dict[str, Any]:
        distance = None
        if requester is not None:
            distance = round(requester.position.distance_to(record.position), 6)
        return {
            "peer_id": record.peer_id,
            "name": record.name,
            "state": record.state,
            "connected": record.state in {"ACTIVE", "VERIFIED"},
            "position": record.position.as_dict(),
            "position_seq": record.position_seq,
            "position_source": "manual-cartesian-metres",
            "distance_from_requester_m": distance,
            "last_seen_age_s": round(max(0.0, now - record.last_seen), 3),
            "heartbeat_count": record.heartbeat_count,
            "reconnect_count": record.reconnect_count,
            "is_self": requester is not None and requester.peer_id == record.peer_id,
        }

    def _snapshot(self, requester: PeerRecord | None, now: float) -> dict[str, Any]:
        self._refresh_states(now)
        peers = [
            self._public_peer(record, requester, now)
            for record in sorted(self._by_peer_id.values(), key=lambda item: (item.name.lower(), item.peer_id))
            if record.state != "LEFT"
        ]
        return {
            "topology": "lan-star-host",
            "coordinate_units": "metres",
            "coordinate_model": "manual T_G(n)=(U_n,V_n,W_n)",
            "peer_count": len(peers),
            "connected_peer_count": sum(peer["connected"] for peer in peers),
            "peers": peers,
        }

    def join(self, payload: Any, remote_address: str = "") -> dict[str, Any]:
        body = self._require_object(payload)
        self._authorize_pairing_code(body.get("pairing_code"))
        client_id = self._validated_client_id(body.get("client_id"))
        name = self._validated_name(body.get("name"))
        position = self._validated_position(body.get("position"))
        position_seq = self._validated_position_seq(body.get("position_seq"))
        now = self._clock()

        with self._lock:
            self._refresh_states(now)
            existing_peer_id = self._peer_id_by_client_id.get(client_id)
            position_accepted = True
            if existing_peer_id is None:
                record = PeerRecord(
                    peer_id=str(uuid.uuid4()),
                    client_id=client_id,
                    session_token=secrets.token_urlsafe(32),
                    name=name,
                    position=position,
                    position_seq=position_seq,
                    state="ACTIVE",
                    first_seen=now,
                    last_seen=now,
                    remote_address=remote_address,
                )
                self._by_peer_id[record.peer_id] = record
                self._peer_id_by_client_id[client_id] = record.peer_id
                recovered = False
            else:
                record = self._by_peer_id[existing_peer_id]
                recovered = record.state in {"REMEMBER", "LEFT"}
                record.session_token = secrets.token_urlsafe(32)
                record.name = name
                record.state = "ACTIVE"
                record.last_seen = now
                record.heartbeat_count = 0
                record.reconnect_count += 1
                record.remote_address = remote_address
                if position_seq > record.position_seq:
                    record.position = position
                    record.position_seq = position_seq
                else:
                    position_accepted = False

            return {
                "status": "joined",
                "service_version": SERVICE_VERSION,
                "server_time": utc_now(),
                "peer_id": record.peer_id,
                "session_token": record.session_token,
                "state": record.state,
                "recovered": recovered,
                "position_accepted": position_accepted,
                "next_position_seq": record.position_seq + 1,
                "heartbeat_interval_ms": 2_000,
                "peer_timeout_ms": int(self.timeout_seconds * 1_000),
                **self._snapshot(record, now),
            }

    def heartbeat(self, payload: Any, remote_address: str = "") -> dict[str, Any]:
        body = self._require_object(payload)
        position = self._validated_position(body.get("position"))
        position_seq = self._validated_position_seq(body.get("position_seq"))
        now = self._clock()

        with self._lock:
            self._refresh_states(now)
            record = self._authorized_peer(body)
            recovered = record.state == "REMEMBER"
            position_accepted = position_seq > record.position_seq
            if position_accepted:
                record.position = position
                record.position_seq = position_seq
            record.last_seen = now
            record.remote_address = remote_address
            record.heartbeat_count += 1
            if recovered:
                record.state = "ACTIVE"
            elif record.heartbeat_count >= 1:
                record.state = "VERIFIED"

            return {
                "status": "heartbeat",
                "service_version": SERVICE_VERSION,
                "server_time": utc_now(),
                "peer_id": record.peer_id,
                "state": record.state,
                "recovered": recovered,
                "position_accepted": position_accepted,
                "position_rejection": None if position_accepted else "stale_position_seq",
                "next_position_seq": record.position_seq + 1,
                **self._snapshot(record, now),
            }

    def leave(self, payload: Any) -> dict[str, Any]:
        body = self._require_object(payload)
        now = self._clock()
        with self._lock:
            record = self._authorized_peer(body)
            record.state = "LEFT"
            record.last_seen = now
            return {
                "status": "left",
                "server_time": utc_now(),
                "peer_id": record.peer_id,
                "state": record.state,
            }

    def health(self) -> dict[str, Any]:
        now = self._clock()
        with self._lock:
            snapshot = self._snapshot(None, now)
            return {
                "status": "ok",
                "service": "blueshare-peer",
                "service_version": SERVICE_VERSION,
                "server_time": utc_now(),
                "peer_timeout_ms": int(self.timeout_seconds * 1_000),
                "connected_peer_count": snapshot["connected_peer_count"],
            }


@dataclass
class MediaTrack:
    media_id: str
    stream_key: str
    filename: str
    content_type: str
    size_bytes: int
    path: Path
    duration_seconds: float | None
    status: str
    base_position_seconds: float
    started_at: float | None
    revision: int
    uploaded_at: str
    updated_at: str
    updated_by_peer_id: str
    updated_by_name: str


class MediaRoom:
    """Single-track, authenticated LAN media room with a shared transport clock."""

    def __init__(
        self,
        storage_directory: Path,
        max_media_bytes: int = DEFAULT_MAX_MEDIA_BYTES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_media_bytes <= 0:
            raise ValueError("max_media_bytes must be positive")
        self.storage_directory = storage_directory.resolve()
        self.storage_directory.mkdir(parents=True, exist_ok=True)
        self.max_media_bytes = int(max_media_bytes)
        self._clock = clock
        self._lock = threading.RLock()
        self._track: MediaTrack | None = None

    @staticmethod
    def _validated_filename(value: Any) -> str:
        if not isinstance(value, str):
            raise ProtocolError(HTTPStatus.BAD_REQUEST, "invalid_filename", "media filename required")
        decoded = unquote(value).replace("\\", "/")
        filename = Path(decoded).name.strip()
        if not filename or len(filename) > 128 or any(ord(character) < 32 for character in filename):
            raise ProtocolError(
                HTTPStatus.BAD_REQUEST,
                "invalid_filename",
                "media filename must be 1-128 safe display characters",
            )
        return filename

    @staticmethod
    def _validated_content_type(value: Any) -> str:
        if not isinstance(value, str):
            raise ProtocolError(HTTPStatus.BAD_REQUEST, "invalid_media_type", "audio content type required")
        content_type = value.split(";", 1)[0].strip().lower()
        if not re.fullmatch(r"audio/[a-z0-9.+-]+", content_type) or len(content_type) > 96:
            raise ProtocolError(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                "invalid_media_type",
                "BlueShare media version 0.2 accepts audio content types only",
            )
        return content_type

    @staticmethod
    def _validated_duration(value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            duration = float(value)
        except (TypeError, ValueError) as error:
            raise ProtocolError(
                HTTPStatus.BAD_REQUEST,
                "invalid_duration",
                "media duration must be a finite number of seconds",
            ) from error
        if not math.isfinite(duration) or duration <= 0 or duration > 7 * 24 * 60 * 60:
            raise ProtocolError(
                HTTPStatus.BAD_REQUEST,
                "invalid_duration",
                "media duration is outside the supported range",
            )
        return duration

    @staticmethod
    def _validated_position(value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ProtocolError(
                HTTPStatus.BAD_REQUEST,
                "invalid_media_position",
                "media position must be a finite number of seconds",
            )
        position = float(value)
        if not math.isfinite(position) or position < 0 or position > 7 * 24 * 60 * 60:
            raise ProtocolError(
                HTTPStatus.BAD_REQUEST,
                "invalid_media_position",
                "media position is outside the supported range",
            )
        return position

    @staticmethod
    def _public_empty() -> dict[str, Any]:
        return {
            "media_id": None,
            "filename": None,
            "content_type": None,
            "size_bytes": 0,
            "duration_seconds": None,
            "status": "EMPTY",
            "position_seconds": 0.0,
            "revision": 0,
            "stream_url": None,
            "updated_at": None,
            "updated_by": None,
        }

    def _position_locked(self, track: MediaTrack, now: float) -> float:
        position = track.base_position_seconds
        if track.status == "PLAYING" and track.started_at is not None:
            position += max(0.0, now - track.started_at)
        if track.duration_seconds is not None:
            position = min(position, track.duration_seconds)
        return max(0.0, position)

    def _snapshot_locked(self, now: float) -> dict[str, Any]:
        track = self._track
        if track is None:
            return self._public_empty()
        status = track.status
        position = self._position_locked(track, now)
        if track.duration_seconds is not None and position >= track.duration_seconds and status == "PLAYING":
            track.status = "PAUSED"
            track.base_position_seconds = track.duration_seconds
            track.started_at = None
            track.revision += 1
            track.updated_at = utc_now()
            status = track.status
        return {
            "media_id": track.media_id,
            "filename": track.filename,
            "content_type": track.content_type,
            "size_bytes": track.size_bytes,
            "duration_seconds": track.duration_seconds,
            "status": status,
            "position_seconds": round(position, 3),
            "revision": track.revision,
            "stream_url": f"/api/media/stream/{track.media_id}?key={track.stream_key}",
            "uploaded_at": track.uploaded_at,
            "updated_at": track.updated_at,
            "updated_by": {
                "peer_id": track.updated_by_peer_id,
                "name": track.updated_by_name,
            },
        }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._snapshot_locked(self._clock())

    def store_upload(
        self,
        peer: PeerRecord,
        filename_value: Any,
        content_type_value: Any,
        duration_value: Any,
        content_length: int,
        source: BinaryIO,
    ) -> dict[str, Any]:
        filename = self._validated_filename(filename_value)
        content_type = self._validated_content_type(content_type_value)
        duration = self._validated_duration(duration_value)
        if content_length <= 0:
            raise ProtocolError(HTTPStatus.BAD_REQUEST, "empty_media", "audio file is empty")
        if content_length > self.max_media_bytes:
            raise ProtocolError(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "media_too_large",
                f"audio file exceeds the {self.max_media_bytes // (1024 * 1024)} MiB limit",
            )

        media_id = str(uuid.uuid4())
        suffix = Path(filename).suffix.lower()
        if len(suffix) > 12 or not re.fullmatch(r"\.[a-z0-9]+", suffix):
            suffix = ".audio"
        target = self.storage_directory / f"{media_id}{suffix}"
        remaining = content_length
        try:
            with target.open("wb") as destination:
                while remaining:
                    chunk = source.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ProtocolError(
                            HTTPStatus.BAD_REQUEST,
                            "incomplete_media",
                            "audio upload ended before Content-Length bytes were received",
                        )
                    destination.write(chunk)
                    remaining -= len(chunk)
        except Exception:
            target.unlink(missing_ok=True)
            raise

        timestamp = utc_now()
        track = MediaTrack(
            media_id=media_id,
            stream_key=secrets.token_urlsafe(24),
            filename=filename,
            content_type=content_type,
            size_bytes=content_length,
            path=target,
            duration_seconds=duration,
            status="READY",
            base_position_seconds=0.0,
            started_at=None,
            revision=1,
            uploaded_at=timestamp,
            updated_at=timestamp,
            updated_by_peer_id=peer.peer_id,
            updated_by_name=peer.name,
        )
        with self._lock:
            previous = self._track
            self._track = track
            snapshot = self._snapshot_locked(self._clock())
        if previous is not None and previous.path != target:
            try:
                previous.path.unlink(missing_ok=True)
            except OSError:
                # Windows may retain an old stream file until existing readers close it.
                pass
        return snapshot

    def control(self, peer: PeerRecord, payload: Any) -> dict[str, Any]:
        body = PeerRegistry._require_object(payload)
        action = body.get("action")
        if action not in {"play", "pause", "seek", "stop"}:
            raise ProtocolError(
                HTTPStatus.BAD_REQUEST,
                "invalid_media_action",
                "media action must be play, pause, seek, or stop",
            )
        requested_position = body.get("position_seconds")
        if action == "seek" and requested_position is None:
            raise ProtocolError(
                HTTPStatus.BAD_REQUEST,
                "media_position_required",
                "seek requires position_seconds",
            )

        with self._lock:
            track = self._track
            if track is None:
                raise ProtocolError(HTTPStatus.CONFLICT, "no_media", "upload an audio file first")
            now = self._clock()
            current_position = self._position_locked(track, now)
            position = (
                self._validated_position(requested_position)
                if requested_position is not None
                else current_position
            )
            if track.duration_seconds is not None:
                position = min(position, track.duration_seconds)

            if action == "play":
                track.status = "PLAYING"
                track.base_position_seconds = position
                track.started_at = now
            elif action == "pause":
                track.status = "PAUSED"
                track.base_position_seconds = position
                track.started_at = None
            elif action == "seek":
                track.base_position_seconds = position
                track.started_at = now if track.status == "PLAYING" else None
            else:
                track.status = "READY"
                track.base_position_seconds = 0.0
                track.started_at = None

            track.revision += 1
            track.updated_at = utc_now()
            track.updated_by_peer_id = peer.peer_id
            track.updated_by_name = peer.name
            return self._snapshot_locked(now)

    def authorized_stream(self, media_id: str, stream_key: str) -> MediaTrack:
        with self._lock:
            track = self._track
            if (
                track is None
                or not secrets.compare_digest(track.media_id, media_id)
                or not secrets.compare_digest(track.stream_key, stream_key)
                or not track.path.is_file()
            ):
                raise ProtocolError(HTTPStatus.NOT_FOUND, "media_not_found", "media stream not found")
            return track


class BlueShareHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        address: tuple[str, int],
        handler: Any,
        registry: PeerRegistry,
        media_room: MediaRoom,
    ) -> None:
        super().__init__(address, handler)
        self.registry = registry
        self.media_room = media_room


class BlueShareRequestHandler(SimpleHTTPRequestHandler):
    """Serve the local web client and same-origin JSON protocol."""

    server_version = "BlueSharePeer/0.2"
    sys_version = ""

    @property
    def registry(self) -> PeerRegistry:
        return self.server.registry  # type: ignore[attr-defined]

    @property
    def media_room(self) -> MediaRoom:
        return self.server.media_room  # type: ignore[attr-defined]

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; media-src 'self' blob:; img-src 'self' data:",
        )
        super().end_headers()

    def list_directory(self, path: str) -> None:
        self.send_error(HTTPStatus.NOT_FOUND)
        return None

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _content_length(self, maximum: int) -> int:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ProtocolError(HTTPStatus.LENGTH_REQUIRED, "length_required", "Content-Length required")
        try:
            length = int(raw_length)
        except ValueError as error:
            raise ProtocolError(HTTPStatus.BAD_REQUEST, "invalid_length", "invalid Content-Length") from error
        if length < 0 or length > maximum:
            raise ProtocolError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "payload_too_large", "request too large")
        return length

    def _read_json(self) -> dict[str, Any]:
        length = self._content_length(MAX_BODY_BYTES)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProtocolError(HTTPStatus.BAD_REQUEST, "invalid_json", "valid UTF-8 JSON required") from error
        if not isinstance(payload, dict):
            raise ProtocolError(HTTPStatus.BAD_REQUEST, "invalid_payload", "JSON object required")
        return payload

    def _send_media_stream(self, head_only: bool = False) -> None:
        parsed = urlsplit(self.path)
        media_id = parsed.path.rsplit("/", 1)[-1]
        stream_key = parse_qs(parsed.query).get("key", [""])[0]
        track = self.media_room.authorized_stream(media_id, stream_key)
        total = track.size_bytes
        start = 0
        end = total - 1
        status = HTTPStatus.OK
        range_header = self.headers.get("Range")
        if range_header:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
            if match is None or (not match.group(1) and not match.group(2)):
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{total}")
                self.end_headers()
                return
            if match.group(1):
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else total - 1
            else:
                suffix_length = int(match.group(2))
                start = max(0, total - suffix_length)
                end = total - 1
            if start >= total or end < start:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{total}")
                self.end_headers()
                return
            end = min(end, total - 1)
            status = HTTPStatus.PARTIAL_CONTENT

        content_length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", track.content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "private, no-store")
        if status == HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
        self.end_headers()
        if head_only:
            return

        try:
            with track.path.open("rb") as source:
                source.seek(start)
                remaining = content_length
                while remaining:
                    chunk = source.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _handle_media_upload(self) -> None:
        peer = self.registry.authorize_session(
            {
                "peer_id": self.headers.get("X-BlueShare-Peer-Id"),
                "session_token": self.headers.get("X-BlueShare-Session-Token"),
            }
        )
        length = self._content_length(self.media_room.max_media_bytes)
        media = self.media_room.store_upload(
            peer=peer,
            filename_value=self.headers.get("X-BlueShare-Filename"),
            content_type_value=self.headers.get("Content-Type"),
            duration_value=self.headers.get("X-BlueShare-Duration"),
            content_length=length,
            source=self.rfile,
        )
        self._send_json(
            HTTPStatus.CREATED,
            {"status": "media_uploaded", "server_time": utc_now(), "media": media},
        )

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        try:
            if path == "/api/health":
                health = self.registry.health()
                health["media_status"] = self.media_room.snapshot()["status"]
                self._send_json(HTTPStatus.OK, health)
                return
            if path.startswith("/api/media/stream/"):
                self._send_media_stream()
                return
            if path.startswith("/api/"):
                raise ProtocolError(HTTPStatus.NOT_FOUND, "not_found", "API route not found")
            super().do_GET()
        except ProtocolError as error:
            self._send_json(error.status, {"error": error.code, "message": error.message})

    def do_HEAD(self) -> None:
        path = urlsplit(self.path).path
        try:
            if path.startswith("/api/media/stream/"):
                self._send_media_stream(head_only=True)
                return
            super().do_HEAD()
        except ProtocolError as error:
            self._send_json(error.status, {"error": error.code, "message": error.message})

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        try:
            if path == "/api/media/upload":
                self._handle_media_upload()
                return
            body = self._read_json()
            remote_address = self.client_address[0]
            if path == "/api/join":
                response = self.registry.join(body, remote_address)
            elif path == "/api/heartbeat":
                response = self.registry.heartbeat(body, remote_address)
            elif path == "/api/leave":
                response = self.registry.leave(body)
            elif path == "/api/media/state":
                self.registry.authorize_session(body)
                response = {
                    "status": "media_state",
                    "server_time": utc_now(),
                    "media": self.media_room.snapshot(),
                }
            elif path == "/api/media/control":
                peer = self.registry.authorize_session(body)
                response = {
                    "status": "media_controlled",
                    "server_time": utc_now(),
                    "media": self.media_room.control(peer, body),
                }
            else:
                raise ProtocolError(HTTPStatus.NOT_FOUND, "not_found", "API route not found")
            self._send_json(HTTPStatus.OK, response)
        except ProtocolError as error:
            self._send_json(error.status, {"error": error.code, "message": error.message})
        except Exception:
            self.log_error("unhandled request failure")
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "internal_error", "message": "internal service error"},
            )

    def log_message(self, format_string: str, *args: Any) -> None:
        # Do not log query strings: media stream capability keys live there.
        safe_path = urlsplit(self.path).path
        status = args[1] if len(args) > 1 else "-"
        print(f'{self.address_string()} - "{self.command} {safe_path}" {status}', flush=True)


def default_static_directory() -> Path:
    return Path(__file__).resolve().parents[3] / "apps" / "desktop"


def default_media_directory() -> Path:
    return Path(__file__).resolve().parents[3] / "build" / "peer-media"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the BlueShare LAN peer join/heartbeat service")
    parser.add_argument("--bind", default="127.0.0.1", help="Address to bind; use a trusted LAN address")
    parser.add_argument("--port", type=int, default=8765, help="TCP port")
    parser.add_argument("--static-dir", type=Path, default=default_static_directory())
    parser.add_argument("--media-dir", type=Path, default=default_media_directory())
    parser.add_argument("--max-media-mb", type=int, default=256, help="Maximum audio upload size in MiB")
    parser.add_argument(
        "--pairing-code",
        default=os.environ.get("BLUESHARE_PAIRING_CODE"),
        help="4-32 character code; generated when omitted",
    )
    parser.add_argument("--peer-timeout", type=float, default=8.0, help="Seconds before a peer enters REMEMBER")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    static_directory = args.static_dir.resolve()
    if not static_directory.is_dir():
        raise SystemExit(f"static directory does not exist: {static_directory}")
    if args.max_media_mb <= 0 or args.max_media_mb > 4096:
        raise SystemExit("--max-media-mb must be between 1 and 4096")
    pairing_code = args.pairing_code or f"{secrets.randbelow(900_000) + 100_000:06d}"
    registry = PeerRegistry(pairing_code, timeout_seconds=args.peer_timeout)
    media_room = MediaRoom(args.media_dir, max_media_bytes=args.max_media_mb * 1024 * 1024)
    handler = partial(BlueShareRequestHandler, directory=str(static_directory))
    server = BlueShareHTTPServer((args.bind, args.port), handler, registry, media_room)

    print(f"BlueShare peer service {SERVICE_VERSION}", flush=True)
    print(f"URL: http://{args.bind}:{args.port}/", flush=True)
    print(f"Pairing code: {pairing_code}", flush=True)
    print(f"Static directory: {static_directory}", flush=True)
    print(f"Media directory: {media_room.storage_directory}", flush=True)
    print(f"Maximum audio upload: {args.max_media_mb} MiB", flush=True)
    print("Position source: manual-cartesian-metres", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("Stopping BlueShare peer service", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
