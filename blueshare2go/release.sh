#!/bin/bash
# BlueShare2Go Automated Release Script
# OBINexus Computing - Computing from the Heart

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "============================================================="
echo "BlueShare2Go Release Automation"
echo "OBINexus Computing - Computing from the Heart"
echo "============================================================="
echo -e "${NC}"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: package.json not found${NC}"
    echo "Please run this script from the BlueShare2Go root directory"
    exit 1
fi

# Parse arguments
RELEASE_TYPE=${1:-alpha}
DRY_RUN=${2:-false}

if [ "$DRY_RUN" == "--dry-run" ]; then
    echo -e "${YELLOW}🔍 DRY RUN MODE - No changes will be made${NC}"
    echo ""
fi

# Get current version
CURRENT_VERSION=$(node -p "require('./package.json').version")
echo -e "${BLUE}Current version: ${CURRENT_VERSION}${NC}"
echo ""

# Determine new version
case $RELEASE_TYPE in
    alpha)
        NEW_VERSION=$(npm version prerelease --preid=alpha --no-git-tag-version --dry-run 2>&1 | grep -oP 'v\K[0-9]+\.[0-9]+\.[0-9]+-alpha\.[0-9]+')
        NPM_TAG="alpha"
        ;;
    beta)
        NEW_VERSION=$(npm version prerelease --preid=beta --no-git-tag-version --dry-run 2>&1 | grep -oP 'v\K[0-9]+\.[0-9]+\.[0-9]+-beta\.[0-9]+')
        NPM_TAG="beta"
        ;;
    rc)
        NEW_VERSION=$(npm version prerelease --preid=rc --no-git-tag-version --dry-run 2>&1 | grep -oP 'v\K[0-9]+\.[0-9]+\.[0-9]+-rc\.[0-9]+')
        NPM_TAG="next"
        ;;
    patch)
        NEW_VERSION=$(npm version patch --no-git-tag-version --dry-run 2>&1 | grep -oP 'v\K[0-9]+\.[0-9]+\.[0-9]+')
        NPM_TAG="latest"
        ;;
    minor)
        NEW_VERSION=$(npm version minor --no-git-tag-version --dry-run 2>&1 | grep -oP 'v\K[0-9]+\.[0-9]+\.[0-9]+')
        NPM_TAG="latest"
        ;;
    major)
        NEW_VERSION=$(npm version major --no-git-tag-version --dry-run 2>&1 | grep -oP 'v\K[0-9]+\.[0-9]+\.[0-9]+')
        NPM_TAG="latest"
        ;;
    *)
        echo -e "${RED}Invalid release type: $RELEASE_TYPE${NC}"
        echo "Usage: ./release.sh [alpha|beta|rc|patch|minor|major] [--dry-run]"
        exit 1
        ;;
esac

echo -e "${GREEN}New version: ${NEW_VERSION}${NC}"
echo -e "${GREEN}NPM tag: ${NPM_TAG}${NC}"
echo ""

# Confirm
if [ "$DRY_RUN" != "--dry-run" ]; then
    read -p "$(echo -e ${YELLOW}Continue with release? [y/N]:${NC} )" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Release cancelled${NC}"
        exit 1
    fi
fi

# Step 1: Run tests
echo -e "${BLUE}[1/8] Running tests...${NC}"
if [ "$DRY_RUN" != "--dry-run" ]; then
    chmod +x build.sh
    ./build.sh || {
        echo -e "${RED}❌ Tests failed. Fix issues before releasing.${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ Tests passed${NC}"
else
    echo -e "${YELLOW}⊘ Skipped (dry run)${NC}"
fi
echo ""

# Step 2: Update version
echo -e "${BLUE}[2/8] Updating version...${NC}"
if [ "$DRY_RUN" != "--dry-run" ]; then
    case $RELEASE_TYPE in
        alpha|beta|rc)
            npm version prerelease --preid=$RELEASE_TYPE --no-git-tag-version
            ;;
        *)
            npm version $RELEASE_TYPE --no-git-tag-version
            ;;
    esac
    echo -e "${GREEN}✅ Version updated to ${NEW_VERSION}${NC}"
else
    echo -e "${YELLOW}⊘ Would update to ${NEW_VERSION}${NC}"
fi
echo ""

# Step 3: Update CHANGELOG
echo -e "${BLUE}[3/8] Updating CHANGELOG...${NC}"
if [ "$DRY_RUN" != "--dry-run" ]; then
    DATE=$(date +%Y-%m-%d)
    
    # Create changelog entry
    CHANGELOG_ENTRY="## [${NEW_VERSION}] - ${DATE}

### Added
- List new features here

### Changed
- List changes here

### Fixed
- List bug fixes here

---
"
    
    # Prepend to existing CHANGELOG
    if [ -f CHANGELOG.md ]; then
        # Backup
        cp CHANGELOG.md CHANGELOG.md.bak
        
        # Insert new entry after first header
        awk -v entry="$CHANGELOG_ENTRY" '
            NR==1 {print; print ""; print entry; next}
            {print}
        ' CHANGELOG.md.bak > CHANGELOG.md
        
        rm CHANGELOG.md.bak
        
        echo -e "${YELLOW}⚠ Please edit CHANGELOG.md to add release notes${NC}"
    fi
    echo -e "${GREEN}✅ CHANGELOG updated${NC}"
else
    echo -e "${YELLOW}⊘ Would update CHANGELOG${NC}"
fi
echo ""

# Step 4: Commit changes
echo -e "${BLUE}[4/8] Committing changes...${NC}"
if [ "$DRY_RUN" != "--dry-run" ]; then
    git add package.json CHANGELOG.md
    git commit -m "chore(release): ${NEW_VERSION}" || {
        echo -e "${YELLOW}⚠ No changes to commit${NC}"
    }
    echo -e "${GREEN}✅ Changes committed${NC}"
else
    echo -e "${YELLOW}⊘ Would commit: package.json, CHANGELOG.md${NC}"
fi
echo ""

# Step 5: Create Git tag
echo -e "${BLUE}[5/8] Creating Git tag...${NC}"
if [ "$DRY_RUN" != "--dry-run" ]; then
    git tag -a "v${NEW_VERSION}" -m "BlueShare2Go v${NEW_VERSION}

Release type: ${RELEASE_TYPE}
NPM tag: ${NPM_TAG}

See CHANGELOG.md for details."
    
    echo -e "${GREEN}✅ Tag v${NEW_VERSION} created${NC}"
else
    echo -e "${YELLOW}⊘ Would create tag: v${NEW_VERSION}${NC}"
fi
echo ""

# Step 6: Push to GitHub
echo -e "${BLUE}[6/8] Pushing to GitHub...${NC}"
if [ "$DRY_RUN" != "--dry-run" ]; then
    read -p "$(echo -e ${YELLOW}Push to GitHub? [y/N]:${NC} )" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push origin main
        git push origin "v${NEW_VERSION}"
        echo -e "${GREEN}✅ Pushed to GitHub${NC}"
    else
        echo -e "${YELLOW}⊘ Skipped push${NC}"
    fi
else
    echo -e "${YELLOW}⊘ Would push: main, v${NEW_VERSION}${NC}"
fi
echo ""

# Step 7: Build for NPM
echo -e "${BLUE}[7/8] Building for NPM...${NC}"
if [ "$DRY_RUN" != "--dry-run" ]; then
    npm pack
    echo -e "${GREEN}✅ Package built${NC}"
else
    echo -e "${YELLOW}⊘ Would run: npm pack${NC}"
fi
echo ""

# Step 8: Publish to NPM
echo -e "${BLUE}[8/8] Publishing to NPM...${NC}"
if [ "$DRY_RUN" != "--dry-run" ]; then
    read -p "$(echo -e ${YELLOW}Publish to NPM with tag \"${NPM_TAG}\"? [y/N]:${NC} )" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Check NPM authentication
        if ! npm whoami &> /dev/null; then
            echo -e "${RED}❌ Not logged in to NPM${NC}"
            echo "Run: npm login"
            exit 1
        fi
        
        # Publish
        npm publish --tag $NPM_TAG --access public
        
        echo -e "${GREEN}✅ Published to NPM${NC}"
        echo ""
        echo -e "${GREEN}Package: @obinexus/blueshare2go@${NEW_VERSION}${NC}"
        echo -e "${GREEN}Install: npm install @obinexus/blueshare2go@${NPM_TAG}${NC}"
    else
        echo -e "${YELLOW}⊘ Skipped NPM publish${NC}"
        echo "To publish later, run:"
        echo "  npm publish --tag $NPM_TAG --access public"
    fi
else
    echo -e "${YELLOW}⊘ Would publish with tag: ${NPM_TAG}${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}"
echo "============================================================="
echo "Release Summary"
echo "============================================================="
echo -e "${NC}"
echo -e "Version: ${GREEN}${CURRENT_VERSION}${NC} → ${GREEN}${NEW_VERSION}${NC}"
echo -e "Type: ${BLUE}${RELEASE_TYPE}${NC}"
echo -e "NPM Tag: ${BLUE}${NPM_TAG}${NC}"
echo ""

if [ "$DRY_RUN" != "--dry-run" ]; then
    echo -e "${GREEN}✅ Release completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Create GitHub release at:"
    echo "     https://github.com/obinexus/blueshare2go/releases/new?tag=v${NEW_VERSION}"
    echo ""
    echo "  2. Verify NPM package:"
    echo "     https://www.npmjs.com/package/@obinexus/blueshare2go"
    echo ""
    echo "  3. Test installation:"
    echo "     npm install @obinexus/blueshare2go@${NPM_TAG}"
else
    echo -e "${YELLOW}This was a dry run. No changes were made.${NC}"
    echo "Run without --dry-run to actually release:"
    echo "  ./release.sh ${RELEASE_TYPE}"
fi

echo ""
echo -e "${BLUE}Computing from the Heart. Building with Purpose.${NC}"
