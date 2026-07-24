# BlueShare scripts

All scripts use repository-relative paths. They are Bash scripts intended for
WSL or another Unix-like shell; they are not native PowerShell scripts.

| Script | Intended use | Current status |
| --- | --- | --- |
| `build/build-blueshare-core.sh` | Configure, build, and run CTest. | Expected to work from WSL when CMake and a C compiler are installed. |
| `build/build-blueshare2go-node-zero.sh` | Build the legacy BlueShare and Node-Zero demos. | Requires GCC, pkg-config, and OpenSSL development files. |
| `build/bootstrap-legacy-blueshare-service.sh` | Historical generator for a separate legacy service tree. | Retained for reference; not a normal build and not executed by cleanup. |
| `network/create-network.sh` | Legacy CLI compatibility entry point. | Exits with code 2 because `blueshare_cli` is not implemented. |
| `release/release-blueshare2go.sh` | Historical npm/Git release automation. | Not runnable: package metadata is absent. It can commit, tag, push, and publish; review before any future use. |

From Windows PowerShell, invoke compatible scripts through WSL, for example:

```powershell
wsl bash scripts/build/build-blueshare-core.sh
```

Build outputs belong under the repository root `build/` directory.
