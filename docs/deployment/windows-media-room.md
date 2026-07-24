# BlueShare Windows media-room guide

This guide runs BlueShare on Windows and sends one shared audio track to
multiple joined Windows devices. Each device plays through the sound output
selected on that device, including a locally paired Bluetooth headset.

## Architecture and boundary

```text
Windows host + BlueShare service
        |
        +-- LAN browser peer A --> Windows output A --> Bluetooth headset A
        +-- LAN browser peer B --> Windows output B --> Bluetooth headset B
        +-- LAN browser peer C --> Windows output C --> Bluetooth headset C
```

BlueShare carries the audio file and synchronized room commands across the LAN.
Windows carries decoded audio from each browser to that device's selected sound
output. Version 0.2 does not pair Bluetooth devices and does not send one
Windows Bluetooth radio directly to several headsets.

## 1. Prepare each Windows device

On every listening device:

1. Open **Settings > Bluetooth & devices**.
2. Turn Bluetooth on and select **Add device > Bluetooth**.
3. Pair one headset or speaker.
4. Open **Settings > System > Sound** and choose that headset as the output.
5. Connect every Windows device to the same trusted Wi-Fi network.

Do this before enabling the BlueShare browser speaker. The Windows volume mixer
can route the browser to a different output if the system default is not the
headset you want.

## 2. Start the host service

Open Windows PowerShell on the host laptop:

```powershell
Set-Location C:\Users\OBINexus\Projects\blueshare\blueshare

python packages\python\blueshare\peer_service.py `
  --bind 192.168.1.117 `
  --port 8765 `
  --pairing-code 246810 `
  --max-media-mb 256
```

Keep this PowerShell window open. Replace `192.168.1.117` if `ipconfig` shows a
different Wi-Fi IPv4 address. Binding to `127.0.0.1` permits only the host
laptop and prevents other devices from joining.

If Windows Defender Firewall prompts, allow Python only on the trusted network
profile being used.

## 3. Join all peers

On the host and every other Windows device, open:

```text
http://192.168.1.117:8765/
```

Enter a different device name, the shared pairing code, and the manual
`(U,V,W)` position for each device. Select **Join network**. Wait until every
peer shows `VERIFIED`.

## 4. Enable the Bluetooth output

On every joined device:

1. Confirm the intended headset is connected in Windows.
2. Select **Enable this speaker** in BlueShare.
3. Set **Volume on this device only** to a safe initial level.

Browsers require a local user action before remote playback can produce sound.
The enable button provides that action. It does not change the Windows output
device.

## 5. Share and control music

Any verified peer may:

1. Select an audio file that it has permission to share.
2. Select **Upload to room**.
3. Wait for the track name and `READY` state to appear on every peer.
4. Select **Play room**.

Play, pause, seek, and stop are shared commands. Volume is local and is never
broadcast. The client polls the room clock every 750 ms and corrects playback
drift above 650 ms.

The current track is stored under the ignored `build/peer-media/` directory on
the host. Uploading another track replaces it. The default maximum upload is
256 MiB.

## 6. Verify multiple-device operation

Use a short test track and confirm:

- every peer reports the same track and transport state;
- play and pause from either laptop affect the full room;
- seeking on one peer moves all other peers;
- local volume changes only one headset;
- disconnecting one peer does not stop the others; and
- reconnecting and rejoining restores the current room state.

Small timing differences are expected from browser buffering, Bluetooth codec
latency, and Windows audio pipelines. Version 0.2 is synchronized LAN playback,
not sample-accurate professional audio distribution.

## Stop the service

Return to the host PowerShell window and press `Ctrl+C`.

The transport uses unencrypted HTTP and an in-memory session registry. Run it
only on a trusted LAN and use a new pairing code for each session.
