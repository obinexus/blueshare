# BlueShare native demonstrations

This directory consolidates the legacy BlueShare2Go C material.

## What exists

- `src/blueshare.c`: standalone session and cost-sharing demonstration.
- `src/zero.c`: standalone Node-Zero/OpenSSL demonstration.
- `src/nsiggi.c`: standalone Linux `getrandom()` NSIGII demonstration.
- `include/blueshare_core.h`: proposed public library API.
- `include/platform_interface.h`: proposed platform API.
- `tests/constitutional/`: retained driver for a future test executable.

Each source file has its own `main()` function. None implements the functions
declared in `blueshare_core.h`, so CMake does not advertise a binary core
library. The headers are exposed through the `blueshare_core_api` interface
target until an implementation exists.

## Build

From the repository root:

```powershell
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

The self-contained BlueShare demo is cross-platform where the available C
compiler accepts the current source. The Node-Zero demo is conditional on
OpenSSL. The NSIGII C demo is Linux-only because it includes `sys/random.h`.

The constitutional shell driver currently exits with code 2 because the
expected `blueshare_test` program is not implemented.
