#!/bin/bash
# BlueShare Network Creation Script

set -euo pipefail

# Default parameters
TOPOLOGY="star"
DURATION=3600
COST_PER_MB=100  # microsatoshis

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --topology)
            TOPOLOGY="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --cost-per-mb)
            COST_PER_MB="$2"
            shift 2
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

echo "🔵 Creating BlueShare network..."
echo "   Topology: ${TOPOLOGY}"
echo "   Duration: ${DURATION} seconds"
echo "   Cost per MB: ${COST_PER_MB} microsatoshis"

# Validate topology
case ${TOPOLOGY} in
    "star"|"bus"|"mesh"|"hybrid")
        echo "✅ Valid topology: ${TOPOLOGY}"
        ;;
    *)
        echo "❌ Invalid topology: ${TOPOLOGY}"
        echo "Valid options: star, bus, mesh, hybrid"
        exit 1
        ;;
esac

# Create network using BlueShare API
./build/blueshare_cli create-network \
    --topology=${TOPOLOGY} \
    --duration=${DURATION} \
    --cost-per-mb=${COST_PER_MB}

echo "✅ BlueShare network created successfully"
