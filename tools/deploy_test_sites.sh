#!/bin/bash
# Deploy test fixtures to GitHub Pages
# See: docs/1105-test-site-infrastructure.md

set -e

FIXTURES_DIR="tests/fixtures/html"
BRANCH="gh-pages"
TEMP_DIR=$(mktemp -d)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Deploying test fixtures to GitHub Pages...${NC}"

# Check if fixtures directory exists
if [ ! -d "$FIXTURES_DIR" ]; then
    echo -e "${RED}Error: Fixtures directory not found: $FIXTURES_DIR${NC}"
    exit 1
fi

# Count fixtures
FILE_COUNT=$(find "$FIXTURES_DIR" -maxdepth 1 -name "*.html" 2>/dev/null | wc -l)
if [ "$FILE_COUNT" -eq 0 ]; then
    echo -e "${RED}Error: No HTML files found in $FIXTURES_DIR${NC}"
    exit 1
fi
echo -e "Found ${GREEN}$FILE_COUNT${NC} HTML files to deploy"

# Save current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

# Copy fixtures to temp directory
echo "Copying fixtures to temp directory..."
cp -r "$FIXTURES_DIR"/* "$TEMP_DIR/"

# Check if gh-pages branch exists
if git show-ref --quiet refs/heads/$BRANCH; then
    echo "Switching to existing $BRANCH branch..."
    git checkout $BRANCH
else
    echo "Creating orphan $BRANCH branch..."
    git checkout --orphan $BRANCH
    git rm -rf . 2>/dev/null || true
fi

# Clean the branch (except .git)
find . -maxdepth 1 ! -name '.git' ! -name '.' -exec rm -rf {} +

# Copy fixtures from temp directory
echo "Copying fixtures..."
cp -r "$TEMP_DIR"/* ./

# Create a simple .nojekyll file to disable Jekyll processing
touch .nojekyll

# Stage and commit
git add -A
if git diff --cached --quiet; then
    echo -e "${YELLOW}No changes to deploy${NC}"
else
    git commit -m "Deploy test fixtures $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "Pushing to origin/$BRANCH..."
    git push origin $BRANCH
    echo -e "${GREEN}Deployed successfully!${NC}"
fi

# Return to original branch
echo "Returning to $CURRENT_BRANCH..."
git checkout "$CURRENT_BRANCH"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}Done!${NC}"
echo -e "Test site will be available at:"
echo -e "  ${YELLOW}https://martymcenroe.github.io/Aletheia/${NC}"
echo ""
echo "Note: GitHub Pages may take a few minutes to update."
