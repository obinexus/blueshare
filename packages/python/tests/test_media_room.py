from __future__ import annotations

import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path


PYTHON_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_PACKAGE_ROOT))

from blueshare.peer_service import MediaRoom, PeerRegistry, ProtocolError  # noqa: E402


class FakeClock:
    def __init__(self) -> None:
        self.value = 500.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class MediaRoomTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.clock = FakeClock()
        self.registry = PeerRegistry("246810", timeout_seconds=8.0, clock=self.clock)
        joined = self.registry.join(
            {
                "pairing_code": "246810",
                "client_id": "media-client-0001",
                "name": "Media-Laptop",
                "position": {"u": 0, "v": 0, "w": 0},
                "position_seq": 1,
            }
        )
        self.registry.heartbeat(
            {
                "peer_id": joined["peer_id"],
                "session_token": joined["session_token"],
                "position": {"u": 0, "v": 0, "w": 0},
                "position_seq": 2,
            }
        )
        self.peer = self.registry.authorize_session(joined)
        self.room = MediaRoom(
            Path(self.temporary_directory.name),
            max_media_bytes=1024,
            clock=self.clock,
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def upload(self, payload: bytes = b"blue-share-audio") -> dict[str, object]:
        return self.room.store_upload(
            peer=self.peer,
            filename_value="track.mp3",
            content_type_value="audio/mpeg",
            duration_value="120.0",
            content_length=len(payload),
            source=BytesIO(payload),
        )

    def test_upload_creates_capability_protected_audio_stream(self) -> None:
        payload = b"blue-share-audio"
        media = self.upload(payload)
        self.assertEqual(media["status"], "READY")
        self.assertEqual(media["filename"], "track.mp3")
        self.assertEqual(media["size_bytes"], len(payload))

        stream_url = str(media["stream_url"])
        media_id = stream_url.split("/stream/", 1)[1].split("?", 1)[0]
        stream_key = stream_url.split("key=", 1)[1]
        track = self.room.authorized_stream(media_id, stream_key)
        self.assertEqual(track.path.read_bytes(), payload)

        with self.assertRaises(ProtocolError) as context:
            self.room.authorized_stream(media_id, "wrong-key")
        self.assertEqual(context.exception.code, "media_not_found")

    def test_transport_clock_play_pause_seek_and_stop(self) -> None:
        self.upload()
        playing = self.room.control(self.peer, {"action": "play", "position_seconds": 5.0})
        self.assertEqual(playing["status"], "PLAYING")
        self.clock.advance(2.25)
        self.assertEqual(self.room.snapshot()["position_seconds"], 7.25)

        paused = self.room.control(self.peer, {"action": "pause"})
        self.assertEqual(paused["status"], "PAUSED")
        self.assertEqual(paused["position_seconds"], 7.25)
        self.clock.advance(3.0)
        self.assertEqual(self.room.snapshot()["position_seconds"], 7.25)

        sought = self.room.control(self.peer, {"action": "seek", "position_seconds": 30.0})
        self.assertEqual(sought["position_seconds"], 30.0)
        self.room.control(self.peer, {"action": "play"})
        self.clock.advance(3.0)
        self.assertEqual(self.room.snapshot()["position_seconds"], 33.0)

        self.room.control(self.peer, {"action": "seek", "position_seconds": 119.0})
        self.clock.advance(2.0)
        ended = self.room.snapshot()
        self.assertEqual(ended["status"], "PAUSED")
        self.assertEqual(ended["position_seconds"], 120.0)

        stopped = self.room.control(self.peer, {"action": "stop"})
        self.assertEqual(stopped["status"], "READY")
        self.assertEqual(stopped["position_seconds"], 0.0)

    def test_rejects_non_audio_and_oversized_uploads(self) -> None:
        with self.assertRaises(ProtocolError) as context:
            self.room.store_upload(
                self.peer,
                "notes.txt",
                "text/plain",
                None,
                4,
                BytesIO(b"text"),
            )
        self.assertEqual(context.exception.code, "invalid_media_type")

        with self.assertRaises(ProtocolError) as context:
            self.room.store_upload(
                self.peer,
                "large.mp3",
                "audio/mpeg",
                None,
                2048,
                BytesIO(b"x" * 2048),
            )
        self.assertEqual(context.exception.code, "media_too_large")


if __name__ == "__main__":
    unittest.main()
