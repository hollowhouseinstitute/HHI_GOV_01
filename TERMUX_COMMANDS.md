#!/bin/bash
# Quick commands for Termux terminal

# Copy this to Termux and run:

# 1. Install dependencies
pip install -q click

# 2. Create artifacts
python3 hhi_cli.py create HHI_A001
python3 hhi_cli.py create HHI_A002
python3 hhi_cli.py create HHI_A003

# 3. Validate
python3 hhi_cli.py validate

# 4. Test resilience
python3 hhi_cli.py adversary HHI_A001 --mutation-rate 0.15

# 5. Replay state
python3 hhi_cli.py replay

# 6. Check status
python3 hhi_cli.py status

# 7. View logs
python3 hhi_cli.py logs

# 8. Run tests
python3 -m pytest runtime/tests.py -v

# 9. View event ledger
echo "\nEvent Ledger Sample:"
head -2 hhi_event_log.jsonl | python3 -m json.tool

# 10. View proofs
echo "\nGenerated Proofs:"
ls -lh runtime/proofs/
cat runtime/proofs/HHI_A001.json | python3 -m json.tool 2>/dev/null || echo "Proofs will be generated during demo"
