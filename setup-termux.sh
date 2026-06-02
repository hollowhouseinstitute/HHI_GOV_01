#!/bin/bash
# Termux setup and PR creation for HHI Governance Runtime
# Run this in Termux to set up environment and create PR

set -e

echo "HHI Governance Runtime - Termux Setup & PR Creation"
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "runtime" ]; then
    echo "Error: Must run from HHI_GOV_01 repository root"
    exit 1
fi

echo "✓ Repository verified"

# Ensure git is configured
if ! git config --global user.email > /dev/null; then
    echo "Configuring git..."
    git config --global user.email "amypbui@github.com"
    git config --global user.name "Amy Bui"
    echo "✓ Git configured"
fi

# Check out the branch
echo ""
echo "Checking out runtime-product-phase1 branch..."
git checkout runtime-product-phase1
git pull origin runtime-product-phase1
echo "✓ Branch ready"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -q -r requirements.txt 2>/dev/null || pip3 install -q -r requirements.txt 2>/dev/null
echo "✓ Dependencies installed"

# Verify runtime works
echo ""
echo "Verifying governance runtime..."
python3 -c "from runtime.event_store import EventStore; print('✓ Runtime imports OK')"

# Show branch status
echo ""
echo "Git Status:"
git status

echo ""
echo "════════════════════════════════════════════════════"
echo "Ready to create PR"
echo "════════════════════════════════════════════════════"
echo ""
echo "To create PR via GitHub CLI:"
echo ""
echo "  gh pr create \\"
echo "    --base main \\"
echo "    --head runtime-product-phase1 \\"
echo "    --title 'Governance Runtime Product: From Static Standard to Executable Implementation' \\"
echo "    --body-file PR_BODY.md"
echo ""
echo "Or visit:"
echo "  https://github.com/Hollow-house-institute/HHI_GOV_01/compare/main...runtime-product-phase1"
echo ""
