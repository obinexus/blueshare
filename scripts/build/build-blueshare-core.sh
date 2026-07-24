#!/usr/bin/env bash
# Build the C demonstrations from either WSL or a Unix-like shell.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_TYPE="${1:-Debug}"
BUILD_DIR="${REPO_ROOT}/build/wsl"

echo "Building BlueShare native demonstrations (${BUILD_TYPE})"
cmake -S "${REPO_ROOT}" -B "${BUILD_DIR}" \
    -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"
cmake --build "${BUILD_DIR}" --config "${BUILD_TYPE}" --parallel
ctest --test-dir "${BUILD_DIR}" -C "${BUILD_TYPE}" --output-on-failure

echo "Native demonstration build complete: ${BUILD_DIR}"
