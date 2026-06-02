# Phase 2: CLI Commands & Agent System

## Files Added

### `runtime/commands.py`
CLI command implementations using Click framework.

**Commands:**
- `hhi create <artifact-id>` — Create new artifact and emit event
- `hhi validate` — Validate artifacts against registry
- `hhi replay` — Reconstruct state from events
- `hhi adversary <artifact-id>` — Test mutation resilience
- `hhi status` — Show governance runtime status
- `hhi logs` — Display recent events

### `runtime/agents.py`
Multi-agent governance enforcement system.

**Agents:**

1. **BuilderAgent**
   - Creates artifacts
   - Computes SHA256 hashes
   - Emits ARTIFACT_CREATED events
   - Non-bypassable event emission

2. **ValidatorAgent**
   - Validates against canonical registry
   - Checks hash integrity
   - Emits VALIDATION_PASSED/FAILED events

3. **AdversaryAgent**
   - Injects mutations
   - Tests resilience
   - Emits ADVERSARY_DETECTED events

4. **GovernorAgent**
   - Monitors drift indicators
   - Enforces thresholds
   - Emits GOVERNANCE_BREACH events

### `hhi_cli.py`
CLI entry point for installation as executable.

## Installation

```bash
# Create symlink or install as command
chmod +x hhi_cli.py
ln -s hhi_cli.py /usr/local/bin/hhi
```

## Usage Examples

```bash
# Create artifact
hhi create HHI_A001

# Validate all
hhi validate

# Validate specific
hhi validate --artifact-id HHI_A001

# Replay state
hhi replay --output state.json

# Test resilience
hhi adversary HHI_A001 --mutation-rate 0.1

# Check status
hhi status

# Show logs
hhi logs
```

## Architecture

```
CLI Commands (hhi create, validate, replay, adversary)
        ↓
    GovernanceContext
        ↓
    Agents (Builder, Validator, Adversary, Governor)
        ↓
    Event Store (append-only ledger)
        ↓
    Reducer (state reconstruction)
        ↓
    Output (JSON, terminal, files)
```

## Next: Phase 3

- Proof generator
- Demo script
- Integration tests
