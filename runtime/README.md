# HHI Governance Runtime

## Phase 1: Event Store & State Reducer

Foundation for execution-time governance enforcement.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Governance Runtime                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Agent Actions]                                             │
│       ↓                                                       │
│  [Event Emission] → [Event Store] → [hhi_event_log.jsonl]   │
│       ↑                                                       │
│  [Reduce Events] ← [State Reconstruction]                    │
│       ↓                                                       │
│  [GovernanceState] → [Drift Indicators] → [Proofs]          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### EventStore (`event_store.py`)

Append-only, immutable event ledger.

**Features:**
- SHA256 integrity hashing per event
- Canonical JSON serialization (sorted keys)
- Timestamped event sequencing
- JSONL persistence (one event per line)
- Integrity verification

**Events Types:**
- `ARTIFACT_CREATED` — governance artifact created
- `VALIDATION_PASSED` — artifact validated successfully
- `VALIDATION_FAILED` — validation failed
- `ADVERSARY_DETECTED` — mutation detected during testing
- `GOVERNANCE_BREACH` — governance threshold violated
- `ESCALATION_TRIGGERED` — escalation authority engaged
- `AUTHORITY_DECLARED` — authority explicitly declared
- `DRIFT_DETECTED` — behavioral drift detected

**Usage:**

```python
from runtime.event_store import EventStore, GovernanceEvent, EventType

store = EventStore()

event = GovernanceEvent(
    event_type=EventType.ARTIFACT_CREATED,
    artifact_id="HHI_A001",
    authority="builder",
    timestamp=time.time(),
    evidence={"hash": "sha256:...", "size": 1024}
)

event_id = store.append(event)
all_events = store.load_all()
```

#### Reducer (`reducer.py`)

Deterministic state reconstruction from events.

**Capabilities:**
- Replays full governance history
- Reconstructs artifact registry
- Tracks authority actions
- Detects violations and breaches
- Computes drift indicators

**Drift Indicators (quantitative, narrative-free):**
- `validation_pass_rate` — % of validations that passed
- `violation_density` — violations per artifact
- `authority_concentration` — action concentration by authority
- `adversary_detection_rate` — mutation detection frequency
- `governance_breach_rate` — breach events per total events

**Usage:**

```python
from runtime.reducer import replay_from_store
from runtime.event_store import EventStore

store = EventStore()
state = replay_from_store(store)

print(f"Total artifacts: {len(state.artifacts)}")
print(f"Total violations: {len(state.violations)}")
print(f"Drift indicators: {state.drift_indicators}")
```

### HHI-GOV-01 Compliance

✅ **Section 2.3: Non-Bypassable Event Emission**
- Every action emits a governance event
- No execution path bypasses event creation

✅ **Section 2.4: Evidence & Ledger Invariants**
- Append-only writes
- Non-destructive
- Immutable once written
- Corrections recorded as new events

✅ **Section 2.5: Drift Detection**
- Quantitative indicators computed automatically
- No narrative explanation required
- Metrics traceable to governance events

### Testing

```bash
# Verify event store integrity
python -c "from runtime.event_store import EventStore; s = EventStore(); print('Integrity:', s.verify_integrity())"

# Replay state from events
python -c "from runtime.reducer import replay_from_store; from runtime.event_store import EventStore; s = EventStore(); st = replay_from_store(s); print('State:', st)"
```

### Next: Phase 2

- CLI command scaffold
- Agent system (builder, validator, adversary, governor)
- Proof generation
