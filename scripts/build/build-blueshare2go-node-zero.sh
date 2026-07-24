#!/usr/bin/env bash
# Build and smoke-test the two self-contained legacy BlueShare2Go C demos.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/native/blueshare-core/src"
BUILD_DIR="${REPO_ROOT}/build/blueshare2go"
LOG_DIR="${BUILD_DIR}/logs"

if ! command -v gcc >/dev/null 2>&1; then
    echo "gcc is required" >&2
    exit 1
fi

if ! command -v pkg-config >/dev/null 2>&1 || ! pkg-config --exists openssl; then
    echo "OpenSSL development headers and pkg-config are required" >&2
    exit 1
fi

mkdir -p "${BUILD_DIR}" "${LOG_DIR}"

gcc -o "${BUILD_DIR}/blueshare_demo" \
    "${SOURCE_DIR}/blueshare.c" -lm -O2 -Wall
gcc -o "${BUILD_DIR}/blueshare_node_zero_demo" \
    "${SOURCE_DIR}/zero.c" -lssl -lcrypto -O2 -Wall

"${BUILD_DIR}/blueshare_demo" >"${LOG_DIR}/blueshare-demo.log" 2>&1
(
    cd "${BUILD_DIR}"
    ./blueshare_node_zero_demo >"${LOG_DIR}/node-zero-demo.log" 2>&1
)

grep -q "BlueShare session completed successfully" \
    "${LOG_DIR}/blueshare-demo.log"
grep -q "Zero-knowledge: Identities never revealed" \
    "${LOG_DIR}/node-zero-demo.log"

echo "Legacy BlueShare2Go demonstrations passed"
echo "Logs: ${LOG_DIR}"
