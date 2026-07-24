# BlueShare detailed build and run guide

This guide explains how to compile, test, and run every executable component
that currently exists in the BlueShare repository.

## 1. Current scope

BlueShare now has a working same-LAN browser peer service, but it is not yet a
packaged desktop or production network service. The repository currently
provides:

- a deterministic Python spatial-acceptance model measured in metres;
- a standalone C BlueShare mixed-consent demonstration;
- a Linux C NSIGII demonstration;
- an optional OpenSSL Node-Zero demonstration;
- a standard-library Python join/heartbeat service and dependency-free web
  client;
- two standalone Python demonstrations; and
- an experimental NumPy pruning module.

There is currently no `blueshare --desktop` command, Bluetooth pairing daemon,
Android package, Java/JAR layer, Rust FFI bridge, TLS deployment, or installed
operating-system service. The HTML application under `apps/desktop/` is served
by the Python LAN prototype.

The tomography model

```text
T_G: N -> R^3
T_G(n) = (U_n, V_n, W_n)
```

is currently represented by deterministic Cartesian node coordinates. It is not
yet backed by physical stereo, Bluetooth, UWB, GPS, or radio tomography.

## 2. Repository root

Run all commands from the repository root:

```text
C:\Users\OBINexus\Projects\blueshare\blueshare
```

In PowerShell:

```powershell
Set-Location C:\Users\OBINexus\Projects\blueshare\blueshare
```

In WSL:

```bash
cd /mnt/c/Users/OBINexus/Projects/blueshare/blueshare
```

Running commands from another directory can break Python imports and make build
outputs difficult to locate.

## 3. Prerequisites

### Common requirements

- Git for source control.
- CMake 3.16 or newer.
- Python 3.10 or newer. The acceptance suite uses only the standard library.

Check the installed tools:

```powershell
git --version
cmake --version
python --version
```

### Windows native build

Install a C toolchain supported by CMake. The tested configuration uses Visual
Studio Build Tools with the **Desktop development with C++** workload.

OpenSSL is optional. When CMake cannot find OpenSSL, it skips
`blueshare_node_zero_demo` and continues building the other supported targets.

### WSL or Linux native build

On Debian or Ubuntu, the typical packages are:

```bash
sudo apt update
sudo apt install build-essential cmake pkg-config python3 python3-pip
```

Install the optional Node-Zero dependency with:

```bash
sudo apt install libssl-dev
```

The Linux NSIGII target requires the Linux `sys/random.h` interface.

### Optional pruning dependency

Only the research pruning module requires NumPy:

```powershell
python -m pip install numpy
```

## 4. Fastest verification path

On Windows PowerShell, run the Python acceptance suite and native build:

```powershell
python -m unittest discover -s acceptance\tests -v
python acceptance\run_spatial_acceptance.py --output-dir build\acceptance-reports

cmake -S . -B build
cmake --build build --config Debug
ctest --test-dir build -C Debug --output-on-failure
```

On WSL/Linux:

```bash
python3 -m unittest discover -s acceptance/tests -v
python3 acceptance/run_spatial_acceptance.py --output-dir build/acceptance-reports
bash scripts/build/build-blueshare-core.sh Release
```

A successful spatial run reports `PASS`, 13 distance samples, and the paths of
its JSON and CSV reports. A successful native test run reports all available
CTest cases as passed.

## 5. Run the metre-based spatial MVP

The spatial MVP verifies:

- 1, 2, 5, and 10 metre A/B checkpoints;
- `A -> B` and `B -> A` distance symmetry;
- continuous movement away from A;
- nearest-neighbour switching when C joins;
- MMUKO disconnect and reconnect state recovery; and
- rejection of stale coordinates.

Run its unit tests:

```powershell
python -m unittest discover -s acceptance\tests -v
```

Run the acceptance scenario without adding new files to the versioned evidence
directory:

```powershell
python acceptance\run_spatial_acceptance.py `
  --output-dir build\acceptance-reports `
  --tolerance-m 0.01
```

WSL/Linux equivalent:

```bash
python3 acceptance/run_spatial_acceptance.py \
  --output-dir build/acceptance-reports \
  --tolerance-m 0.01
```

The exit code is 0 for `PASS` and 1 for `FAIL`. Reports contain timestamps,
movement events, ground truth, reported distances, absolute errors, symmetry
deltas, nearest-neighbour state, and MMUKO state.

To intentionally write reviewable evidence into the repository, omit
`--output-dir`. The default is `acceptance/reports/`.

## 6. Compile the native demonstrations on Windows

Configure a Debug build:

```powershell
cmake -S . -B build
```

Compile:

```powershell
cmake --build build --config Debug --parallel
```

Run the registered tests:

```powershell
ctest --test-dir build -C Debug --output-on-failure
```

Visual Studio is a multi-configuration generator, so `-C Debug` is required by
CTest. Replace `Debug` with `Release` consistently for a release build:

```powershell
cmake --build build --config Release --parallel
ctest --test-dir build -C Release --output-on-failure
```

Typical executable locations are:

```text
build\native\blueshare-core\Debug\blueshare_demo.exe
build\native\blueshare-core\Debug\blueshare_node_zero_demo.exe
```

The second executable exists only when OpenSSL is detected. The Linux NSIGII C
target is intentionally unavailable on Windows.

### Run the BlueShare C demonstration

```powershell
& .\build\native\blueshare-core\Debug\blueshare_demo.exe
```

The retained sample contains two `YES`, one `NO`, and one `MAYBE` response. It
therefore prints `REJECTED`, aborts the session, and exits with code 1. This is
the designed constitutional result, not a compiler failure. CTest marks this
nonzero outcome as expected.

Inspect the exit code with:

```powershell
$LASTEXITCODE
```

### Run Node-Zero safely

Node-Zero writes demonstration key files in its current working directory. Run
it inside the ignored `build/` tree:

```powershell
$repo = (Get-Location).Path
New-Item -ItemType Directory -Force .\build\node-zero-run | Out-Null
Push-Location .\build\node-zero-run
& "$repo\build\native\blueshare-core\Debug\blueshare_node_zero_demo.exe"
Pop-Location
```

Do not treat the generated demo keys as production identities or credentials.

## 7. Compile the native demonstrations on WSL/Linux

The canonical wrapper configures, builds, and runs CTest:

```bash
bash scripts/build/build-blueshare-core.sh Release
```

Its build directory is:

```text
build/wsl/
```

Depending on available libraries, executables include:

```text
build/wsl/native/blueshare-core/blueshare_demo
build/wsl/native/blueshare-core/blueshare_nsigii_demo
build/wsl/native/blueshare-core/blueshare_node_zero_demo
```

Run the Linux NSIGII demonstration:

```bash
./build/wsl/native/blueshare-core/blueshare_nsigii_demo
```

Run the mixed-consent BlueShare demonstration:

```bash
./build/wsl/native/blueshare-core/blueshare_demo
echo "exit code: $?"
```

An exit code of 1 is expected for its deliberately rejected consent set.

If the optional Node-Zero target exists, run it in an ignored directory:

```bash
mkdir -p build/node-zero-run
cd build/node-zero-run
../wsl/native/blueshare-core/blueshare_node_zero_demo
cd ../..
```

If configuration prints `OpenSSL not found`, install the OpenSSL development
package, delete or reconfigure `build/wsl`, and build again.

## 8. Compile directly with GCC

CMake is the recommended build interface. For diagnostic use on Linux, the
standalone sources can also be compiled directly because each has its own
`main()` function.

```bash
mkdir -p build/manual

gcc native/blueshare-core/src/blueshare.c \
  -o build/manual/blueshare_demo \
  -std=gnu11 -O2 -Wall -Wextra -lm

gcc native/blueshare-core/src/nsiggi.c \
  -o build/manual/blueshare_nsigii_demo \
  -std=gnu11 -O2 -Wall -Wextra -lm

gcc native/blueshare-core/src/zero.c \
  -o build/manual/blueshare_node_zero_demo \
  -std=gnu11 -O2 -Wall -Wextra \
  $(pkg-config --cflags --libs openssl)
```

Run them with:

```bash
./build/manual/blueshare_demo
./build/manual/blueshare_nsigii_demo
(cd build/manual && ./blueshare_node_zero_demo)
```

Do not combine the three C files into one executable: all three define their
own `main()` function.

## 9. Run the Python LAN service and demonstrations

The Python scripts use only the standard library and require no compilation.

### Connect multiple Windows devices on the same trusted LAN

Find the host laptop's Wi-Fi IPv4 address, choose a temporary pairing code, and
run from the repository root. For the currently verified host address:

```powershell
python packages\python\blueshare\peer_service.py `
  --bind 192.168.1.117 `
  --port 8765 `
  --pairing-code 246810 `
  --max-media-mb 256
```

On both laptops, open `http://192.168.1.117:8765/` in a modern browser. Enter a
different device name on each laptop, use the same pairing code, and enter each
device's manual `(U,V,W)` position in metres. The topology view then reports
peer lifecycle state and symmetric Euclidean distance. Press `Ctrl+C` in the
host terminal to stop the service.

For shared music, pair a Bluetooth headset or speaker to each Windows peer and
select it in **Settings > System > Sound** on that device. In every joined
BlueShare browser, select **Enable this speaker**. A verified peer may then
select an audio file, upload it to the room, and use play, pause, seek, or stop.
Transport commands affect the room; volume affects only the current device.

Run the peer registry tests with:

```powershell
py -3.14 -m unittest packages.python.tests.test_peer_service packages.python.tests.test_media_room -v
```

Protocol version 0.2 uses unencrypted HTTP and in-memory state. Use it only on a
trusted LAN. It provides actual LAN audio streaming and shared media controls,
but not physical ranging, Bluetooth discovery/pairing, Windows output-device
routing, or Internet Connection Sharing. See the detailed
[`Windows media-room guide`](docs/deployment/windows-media-room.md).

### Standalone demonstrations

NSIGII echo demonstration:

```powershell
python packages\python\blueshare\nsiggi.py
```

BlueShare cost-sharing demonstration:

```powershell
python packages\python\blueshare\blueshare.py
```

WSL/Linux equivalents:

```bash
python3 packages/python/blueshare/nsiggi.py
python3 packages/python/blueshare/blueshare.py
```

These two demonstration scripts model in-memory behavior. Unlike
`peer_service.py`, they do not connect browser peers. None of the Python code
scans headsets, shares an Internet connection, or processes real payments.

## 10. Exercise the pruning research module

After installing NumPy, run a small invariant check from the repository root:

```powershell
python -c "import numpy as np; from research.pruning.pruning_operator import node_pruning, compute_fod_score; t=np.ones((1,1,4,4)); w=np.array([0.1,0.9,0.2,0.05]); p,h=node_pruning(t,w,0.25); f=compute_fod_score(p,h); assert 0 <= f <= 6; print(f'FoD={f:.2f}, H={h:.2f}')"
```

This is a mathematical research check, not a runtime network-topology service.

## 11. Native targets and expected behavior

| Target | Platform | Dependency | Expected behavior |
| --- | --- | --- | --- |
| `blueshare_demo` | Windows/Linux | C compiler and math library | Prints a mixed-consent session, rejects it, exits 1. |
| `blueshare_nsigii_demo` | Linux only | `sys/random.h` | Runs an NSIGII sampling/verification demonstration, exits 0. |
| `blueshare_node_zero_demo` | Windows/Linux | OpenSSL Crypto | Generates demonstration identities/keys and exits 0. |
| `blueshare_core_api` | All | None | Header-only CMake interface; it is not a binary library. |

The public functions declared in `blueshare_core.h` do not yet have a matching
library implementation. Installing the project installs headers only.

## 12. Compatibility scripts that do not provide a service

The following paths are deliberately retained but are not normal run commands:

- `scripts/network/create-network.sh` exits 2 because `blueshare_cli` is not
  implemented.
- `native/blueshare-core/tests/constitutional/test_constitutional_compliance.sh`
  exits 2 because `blueshare_test` is not implemented.
- `scripts/release/release-blueshare2go.sh` cannot run without package metadata
  and contains commit, tag, push, and publish operations.
- `scripts/build/bootstrap-legacy-blueshare-service.sh` is a historical source
  generator, not the current build.
- `scripts/build/build-blueshare2go-node-zero.sh` retains an older smoke-test
  expectation that conflicts with the current mixed-consent demo's designed
  exit code. Use the CMake workflow above.

## 13. Troubleshooting

### `cmake` is not recognized

Install CMake and open a new terminal. Confirm with `cmake --version`.

### CMake cannot find a compiler

On Windows, run from a Visual Studio Developer PowerShell or install the C++
build workload. On WSL/Linux, install `build-essential`.

### CTest says it cannot find the Debug executable

Use the same configuration for build and test:

```powershell
cmake --build build --config Debug
ctest --test-dir build -C Debug --output-on-failure
```

### OpenSSL target is skipped

This is allowed. Install OpenSSL development headers and reconfigure if you
need Node-Zero. The other supported targets still build.

### Python cannot import `acceptance` or `spatial_mvp`

Return to the repository root and run the documented command exactly. Do not
launch the acceptance modules from inside their subdirectories.

### BlueShare prints `REJECTED`

That is expected from the retained mixed-consent sample. Use CTest to verify the
behavior. It does not mean a real peer connection was attempted.

### No headset or Bluetooth device appears

The current repository has no discovery or pairing adapter. Compiling the demos
will not add Bluetooth support to the operating system.

### The other laptop cannot open the BlueShare URL

Confirm both laptops are on the same trusted Wi-Fi, use the host's Wi-Fi IPv4
address rather than `127.0.0.1`, and keep the service terminal running. Windows
may ask to allow Python on private/public networks; allow only the trusted
network profile you are using. Test `http://HOST_IP:8765/api/health` in the
other laptop's browser.

### Join says the pairing code is invalid

Use the exact temporary code printed by the host service. Pairing codes are not
stored in the browser and can change every time the service starts.

## 14. Clean generated outputs

Ask CMake to clean compiled targets while retaining its configuration:

```powershell
cmake --build build --target clean --config Debug
```

For a completely fresh configure, remove only the repository's generated
`build/` directory, then rerun `cmake -S . -B build`. Do not remove the
repository root or any source directory.

Python caches, native build products, runtime logs, and `build/` are ignored by
Git. Timestamped files under `acceptance/reports/` are intentionally not ignored
because they are reviewable evidence.

## 15. Recommended development sequence

Before building a desktop or Android package:

1. Implement the native functions declared in `blueshare_core.h`.
2. Add a real `blueshare_test` executable and constitutional tests.
3. Define the node reconstruction contract `T_G(n)=(U_n,V_n,W_n)` and metre
   uncertainty semantics.
4. Harden the implemented protocol with TLS, persistent identity, and service
   installation.
5. Add automated multi-process and two-host integration tests.
6. Add physical discovery/ranging adapters without changing the acceptance
   contract.
7. Build the desktop and Android shells after the service boundary is stable.

For implementation status and verified results, also read
[`README.md`](README.md), [`docs/current-status.md`](docs/current-status.md), and
[`docs/repository-cleanup-report.md`](docs/repository-cleanup-report.md).
