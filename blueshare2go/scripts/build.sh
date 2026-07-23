#!/bin/bash
# BlueShare Build Script with Constitutional Compliance

set -euo pipefail

# Build configuration
BUILD_TYPE=${1:-debug}
TARGET_PLATFORM=${2:-linux}

echo "🔵 Building BlueShare for ${TARGET_PLATFORM} (${BUILD_TYPE})"

# Create build directory
mkdir -p build

# Configure build based on platform
configure_build() {
    case ${TARGET_PLATFORM} in
        "android")
            echo "Configuring for Android build..."
            export CC=arm-linux-androideabi-gcc
            export CFLAGS="-DPLATFORM_ANDROID=1"
            ;;
        "ios")
            echo "Configuring for iOS build..."
            export CC=clang
            export CFLAGS="-DPLATFORM_IOS=1 -arch arm64"
            ;;
        "linux"|*)
            echo "Configuring for Linux build..."
            export CC=gcc
            export CFLAGS="-DPLATFORM_LINUX=1"
            ;;
    esac
}

# Build core library
build_core() {
    echo "Building BlueShare core library..."
    
    cd build
    cmake .. \
        -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
        -DTARGET_PLATFORM=${TARGET_PLATFORM} \
        -DCONSTITUTIONAL_COMPLIANCE=ON
    
    make -j$(nproc)
    cd ..
}

# Run constitutional compliance validation
validate_constitutional_compliance() {
    echo "🏛️ Validating constitutional compliance..."
    
    ./tests/constitutional/test_constitutional_compliance.sh
    
    if [ $? -eq 0 ]; then
        echo "✅ Constitutional compliance validated"
    else
        echo "❌ Constitutional compliance validation FAILED"
        exit 1
    fi
}

# Main build process
main() {
    configure_build
    build_core
    validate_constitutional_compliance
    
    echo "🎉 BlueShare build complete for ${TARGET_PLATFORM}"
}

main "$@"
