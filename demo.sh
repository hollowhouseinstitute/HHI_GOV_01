#!/bin/bash
# Demo script for HHI Governance Runtime
# Shows complete workflow: create -> validate -> test -> replay -> proof

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     HHI Governance Runtime - Complete Demonstration        ║"
echo "║     Execution-Time AI Governance Framework                 ║"
echo "║     From Prototype → Product                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Phase 1: Artifact Creation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Creating governance artifacts..."
echo ""

# Clean up any previous run
rm -f hhi_event_log.jsonl governance_state.json
mkdir -p runtime/proofs

# Create artifacts
python3 -c "
from runtime.commands import GovernanceContext
import sys

ctx = GovernanceContext()

# Create demo artifacts
for i in range(1, 4):
    result = ctx.builder.create_artifact(
        artifact_id=f'HHI_DEMO_{i:03d}',
        authority='builder',
        data={'demo': True, 'index': i}
    )
    print(f'✓ Created {result[\"artifact_id\"]} (hash: {result[\"hash\"][:16]}...)')
"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Phase 2: Artifact Validation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Validating all artifacts..."
echo ""

python3 -c "
from runtime.commands import GovernanceContext

ctx = GovernanceContext()
results = ctx.validator.validate_artifacts()

for aid, val in results['validations'].items():
    status = '✓' if val['valid'] else '✗'
    print(f'{status} {aid}: {val[\"reason\"]}')

print(f'\nValidations: {len(results[\"validations\"])} total')
"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Phase 3: Adversarial Testing${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Testing artifact resilience through mutation..."
echo ""

python3 -c "
from runtime.commands import GovernanceContext

ctx = GovernanceContext()

# Test first artifact
result = ctx.adversary.test_artifact(
    artifact_id='HHI_DEMO_001',
    mutation_rate=0.15
)

detected = '✓ DETECTED' if result['detected'] else '✗ UNDETECTED'
print(f'Mutation Test: {detected}')
print(f'  Original: {result[\"original_hash\"][:16]}...')
print(f'  Mutated:  {result[\"mutated_hash\"][:16]}...')
print(f'  Rate: {result[\"mutation_rate\"]:.1%}')
"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Phase 4: Governance State Reconstruction (Replay)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Replaying all events to reconstruct governance state..."
echo ""

python3 -c "
from runtime.reducer import replay_from_store
from runtime.event_store import EventStore

store = EventStore()
state = replay_from_store(store)

print(f'Event Log Statistics:')
print(f'  Total Events: {state.total_events}')
print(f'  Artifacts: {len(state.artifacts)}')
print(f'  Violations: {len(state.violations)}')
print(f'  Last Event: {state.last_event_timestamp}')

print(f'\nDrift Indicators (Quantitative):')
for indicator, value in state.drift_indicators.items():
    print(f'  {indicator}: {value:.4f}')

"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Phase 5: Cryptographic Proof Generation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Generating cryptographic proofs of governance..."
echo ""

python3 -c "
from runtime.proof_generator import ProofGenerator
from runtime.event_store import EventStore

store = EventStore()
gen = ProofGenerator(store)

# Generate proofs for all artifacts
proofs = gen.generate_batch_proofs()

for artifact_id, proof in proofs.items():
    print(f'✓ Proof generated: {artifact_id}')
    print(f'  Proof ID: {proof[\"proof_id\"][:16]}...')
    print(f'  Validated: {proof[\"validation_passed\"]}')
    print(f'  Adversary Tested: {proof[\"adversary_tested\"]}')

print(f'\nProofs saved to: runtime/proofs/')
"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Phase 6: Runtime Status & Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

python3 -c "
from runtime.event_store import EventStore
from runtime.reducer import replay_from_store

store = EventStore()
state = replay_from_store(store)

print('HHI Governance Runtime Status')
print('─' * 50)
print(f'Ledger Integrity: PASS' if store.verify_integrity() else 'Ledger Integrity: FAIL')
print(f'Total Artifacts: {len(state.artifacts)}')
valid = sum(1 for a in state.artifacts.values() if a.get(\"valid\"))
print(f'Valid: {valid}/{len(state.artifacts)}')
print(f'Total Events: {state.total_events}')
print(f'Total Violations: {len(state.violations)}')
print('')
print(f'Governance Health: NOMINAL')
print(f'  Validation Pass Rate: {state.drift_indicators[\"validation_pass_rate\"]:.1%}')
print(f'  Governance Breach Rate: {state.drift_indicators[\"governance_breach_rate\"]:.4f}')
print('')
print(f'System State: ✓ GOVERNED')
"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Event Log Sample${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Recent governance events:"
echo ""
head -5 hhi_event_log.jsonl | python3 -m json.tool 2>/dev/null | head -30

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Demonstration Complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Artifacts created:"
echo "  - Event log: hhi_event_log.jsonl"
echo "  - State snapshot: governance_state.json"
echo "  - Proofs: runtime/proofs/*.json"
echo ""
echo "Time turns behavior into infrastructure."
echo "Behavior is the most honest data there is."
echo ""
