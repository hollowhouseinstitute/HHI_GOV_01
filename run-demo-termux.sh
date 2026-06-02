#!/bin/bash
# Run governance runtime demo in Termux
# Demonstrates: create -> validate -> test -> replay -> proof

set -e

echo "Installing dependencies..."
pip install -q -r requirements.txt 2>/dev/null || pip3 install -q -r requirements.txt 2>/dev/null

echo "Running demo..."
echo ""

bash demo.sh

echo ""
echo "Demo complete. Evidence files:"
echo "  - hhi_event_log.jsonl (event ledger)"
echo "  - governance_state.json (state snapshot)"
echo "  - runtime/proofs/ (cryptographic proofs)"
echo ""
echo "Run tests:"
echo "  python3 -m pytest runtime/tests.py -v"
echo ""
