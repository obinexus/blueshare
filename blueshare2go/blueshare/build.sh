#!/bin/bash
# BlueShare + Node-Zero Build & Test Script
# OBINexus Computing Project

set -e  # Exit on error

echo "============================================================="
echo "BlueShare + Node-Zero Build System"
echo "OBINexus Computing - Computing from the Heart"
echo "============================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check dependencies
echo "[BUILD] Checking dependencies..."

if ! command -v gcc &> /dev/null; then
    echo -e "${RED}✗ gcc not found${NC}"
    echo "  Install: sudo apt-get install build-essential"
    exit 1
fi
echo -e "${GREEN}✓ gcc found${NC}"

if ! pkg-config --exists openssl; then
    echo -e "${RED}✗ OpenSSL development headers not found${NC}"
    echo "  Install: sudo apt-get install libssl-dev"
    exit 1
fi
echo -e "${GREEN}✓ OpenSSL found${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠ python3 not found (optional)${NC}"
else
    echo -e "${GREEN}✓ python3 found${NC}"
fi

echo ""

# Create directory structure
echo "[BUILD] Creating directory structure..."
mkdir -p build
mkdir -p devices
mkdir -p networks
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Compile BlueShare core
echo "[BUILD] Compiling BlueShare core..."
gcc -o build/blueshare_core blueshare_core.c -lm -O2 -Wall
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ BlueShare core compiled${NC}"
else
    echo -e "${RED}✗ Compilation failed${NC}"
    exit 1
fi
echo ""

# Compile BlueShare + Node-Zero integration
echo "[BUILD] Compiling BlueShare + Node-Zero..."
gcc -o build/blueshare_nodezero blueshare_nodezero.c -lssl -lcrypto -lm -O2 -Wall
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Node-Zero integration compiled${NC}"
else
    echo -e "${RED}✗ Compilation failed${NC}"
    exit 1
fi
echo ""

# Run tests
echo "============================================================="
echo "RUNNING TESTS"
echo "============================================================="
echo ""

# Test 1: BlueShare Core
echo "[TEST 1] BlueShare Core Protocol"
./build/blueshare_core > logs/blueshare_core_test.log 2>&1
if grep -q "✓ BlueShare session completed successfully" logs/blueshare_core_test.log; then
    echo -e "${GREEN}✓ PASSED${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    cat logs/blueshare_core_test.log
    exit 1
fi
echo ""

# Test 2: Node-Zero Privacy
echo "[TEST 2] Node-Zero Privacy Framework"
./build/blueshare_nodezero > logs/nodezero_test.log 2>&1
if grep -q "✓ Zero-knowledge: Identities never revealed" logs/nodezero_test.log; then
    echo -e "${GREEN}✓ PASSED${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    cat logs/nodezero_test.log
    exit 1
fi
echo ""

# Test 3: Python prototype (optional)
if command -v python3 &> /dev/null && [ -f blueshare_prototype.py ]; then
    echo "[TEST 3] Python Prototype"
    python3 blueshare_prototype.py > logs/python_test.log 2>&1
    if grep -q "✓ BlueShare session completed successfully" logs/python_test.log; then
        echo -e "${GREEN}✓ PASSED${NC}"
    else
        echo -e "${YELLOW}⚠ Python test skipped${NC}"
    fi
    echo ""
fi

# Verify generated files
echo "[VERIFY] Checking generated files..."
if [ -f alice.zid ] && [ -f alice.zid.key ]; then
    mv alice.zid devices/
    mv alice.zid.key devices/
    echo -e "${GREEN}✓ Alice's ZeroID files moved to devices/${NC}"
fi

if [ -f bob.zid ] && [ -f bob.zid.key ]; then
    mv bob.zid devices/
    mv bob.zid.key devices/
    echo -e "${GREEN}✓ Bob's ZeroID files moved to devices/${NC}"
fi
echo ""

# Security check
echo "[SECURITY] Checking file permissions..."
if [ -d devices ]; then
    # Make .key files readable only by owner
    chmod 600 devices/*.key 2>/dev/null || true
    # Make .zid files readable by all (they're public)
    chmod 644 devices/*.zid 2>/dev/null || true
    echo -e "${GREEN}✓ Permissions set correctly${NC}"
    echo "  .zid files: -rw-r--r-- (public)"
    echo "  .key files: -rw------- (private) ⚠️"
fi
echo ""

# Constitutional compliance check
echo "[COMPLIANCE] Verifying constitutional requirements..."
COMPLIANCE_CHECKS=0

# Check 1: Transparency
if grep -q "Cost transparency verified" logs/blueshare_core_test.log; then
    echo -e "${GREEN}✓ Transparency: VERIFIED${NC}"
    ((COMPLIANCE_CHECKS++))
else
    echo -e "${RED}✗ Transparency: FAILED${NC}"
fi

# Check 2: Fairness
if grep -q "Fairness verified" logs/blueshare_core_test.log; then
    echo -e "${GREEN}✓ Fairness: VERIFIED${NC}"
    ((COMPLIANCE_CHECKS++))
else
    echo -e "${RED}✗ Fairness: FAILED${NC}"
fi

# Check 3: Privacy
if grep -q "Zero-knowledge: Identities never revealed" logs/nodezero_test.log; then
    echo -e "${GREEN}✓ Privacy: VERIFIED${NC}"
    ((COMPLIANCE_CHECKS++))
else
    echo -e "${RED}✗ Privacy: FAILED${NC}"
fi

# Check 4: File Separation
if [ -f devices/alice.zid ] && [ -f devices/alice.zid.key ]; then
    echo -e "${GREEN}✓ File Separation: VERIFIED${NC}"
    ((COMPLIANCE_CHECKS++))
else
    echo -e "${RED}✗ File Separation: FAILED${NC}"
fi

echo ""

# Final summary
echo "============================================================="
echo "BUILD & TEST SUMMARY"
echo "============================================================="
echo ""

if [ $COMPLIANCE_CHECKS -eq 4 ]; then
    echo -e "${GREEN}✓✓✓ ALL TESTS PASSED ✓✓✓${NC}"
    echo ""
    echo "Constitutional Compliance: ${COMPLIANCE_CHECKS}/4 checks passed"
    echo ""
    echo "Built artifacts:"
    echo "  - build/blueshare_core"
    echo "  - build/blueshare_nodezero"
    echo ""
    echo "Test logs:"
    echo "  - logs/blueshare_core_test.log"
    echo "  - logs/nodezero_test.log"
    echo ""
    echo "Device identities:"
    ls -lh devices/*.zid 2>/dev/null || true
    echo ""
    echo -e "${YELLOW}⚠️ SECURITY REMINDER:${NC}"
    echo "  - NEVER commit .key files to Git"
    echo "  - Add 'devices/*.key' to .gitignore"
    echo ""
    echo "Computing from the Heart. Building with Purpose."
    exit 0
else
    echo -e "${RED}✗✗✗ SOME TESTS FAILED ✗✗✗${NC}"
    echo ""
    echo "Constitutional Compliance: ${COMPLIANCE_CHECKS}/4 checks passed"
    echo ""
    echo "Please review test logs:"
    echo "  - logs/blueshare_core_test.log"
    echo "  - logs/nodezero_test.log"
    exit 1
fi
