# BlueShare desktop application

## Current state

No desktop frontend, NW.js runtime, HTML entry point, or desktop manifest exists
in the cleaned repository.

The former `blueshare/manifest.json` was inspected and is a pruning-control
research manifest. It is retained at `research/pruning/manifest.json` and must
not be used as an NW.js application manifest.

## Planned state

The project vision calls for a desktop-first BlueShare service and local web
interface. That work is intentionally paused until repository cleanup is
complete and a service protocol is approved.

Nothing in this directory currently pairs Bluetooth devices, shares an Internet
connection, starts a background service, or produces an Android package.
