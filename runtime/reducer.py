"""State reducer for governance runtime.

Reconstructs governance state from append-only event log.
Implements deterministic replay of governance history.

Complies with HHI-GOV-01 Section 2.5: Drift Detection
Computes quantitative drift indicators without narrative explanation.
"""

import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from runtime.event_store import EventStore, GovernanceEvent, EventType


@dataclass
class GovernanceState:
    """Reconstructed governance state from event log."""
    
    artifacts: Dict[str, Dict[str, Any]]  # artifact_id -> metadata
    authority_actions: Dict[str, int]     # authority -> action count
    validations: Dict[str, bool]          # artifact_id -> is_valid
    violations: List[Dict[str, Any]]      # governance breaches
    last_event_timestamp: float           # most recent event
    total_events: int                     # total event count
    drift_indicators: Dict[str, float]    # drift metrics


def reduce_events(events: List[GovernanceEvent]) -> GovernanceState:
    """Reconstruct governance state from events.
    
    Implements deterministic replay: same events always produce same state.
    
    Args:
        events: List of events in chronological order.
        
    Returns:
        GovernanceState reflecting full governance history.
    """
    state = {
        "artifacts": {},
        "authority_actions": {},
        "validations": {},
        "violations": [],
        "last_event_timestamp": 0.0,
        "total_events": 0,
    }
    
    for event in events:
        # Track timestamp
        state["last_event_timestamp"] = event.timestamp
        state["total_events"] += 1
        
        # Track authority actions
        if event.authority not in state["authority_actions"]:
            state["authority_actions"][event.authority] = 0
        state["authority_actions"][event.authority] += 1
        
        # Process by event type
        if event.event_type == EventType.ARTIFACT_CREATED:
            state["artifacts"][event.artifact_id] = {
                "created_at": event.timestamp,
                "created_by": event.authority,
                "hash": event.evidence.get("hash"),
                "valid": False,
            }
        
        elif event.event_type == EventType.VALIDATION_PASSED:
            if event.artifact_id not in state["artifacts"]:
                state["artifacts"][event.artifact_id] = {}
            state["artifacts"][event.artifact_id]["valid"] = True
            state["artifacts"][event.artifact_id]["validated_at"] = event.timestamp
            state["validations"][event.artifact_id] = True
        
        elif event.event_type == EventType.VALIDATION_FAILED:
            if event.artifact_id not in state["artifacts"]:
                state["artifacts"][event.artifact_id] = {}
            state["artifacts"][event.artifact_id]["valid"] = False
            state["validations"][event.artifact_id] = False
            state["violations"].append({
                "type": "VALIDATION_FAILED",
                "artifact_id": event.artifact_id,
                "timestamp": event.timestamp,
                "reason": event.evidence.get("reason"),
            })
        
        elif event.event_type == EventType.ADVERSARY_DETECTED:
            state["violations"].append({
                "type": "ADVERSARY_DETECTED",
                "artifact_id": event.artifact_id,
                "timestamp": event.timestamp,
                "mutation_rate": event.evidence.get("mutation_rate"),
                "detected": event.evidence.get("detected"),
            })
        
        elif event.event_type == EventType.GOVERNANCE_BREACH:
            state["violations"].append({
                "type": "GOVERNANCE_BREACH",
                "artifact_id": event.artifact_id,
                "timestamp": event.timestamp,
                "reason": event.evidence.get("reason"),
            })
        
        elif event.event_type == EventType.DRIFT_DETECTED:
            state["violations"].append({
                "type": "DRIFT_DETECTED",
                "artifact_id": event.artifact_id,
                "timestamp": event.timestamp,
                "indicator": event.evidence.get("indicator"),
                "value": event.evidence.get("value"),
            })
    
    # Compute drift indicators
    drift = compute_drift_indicators(state)
    
    return GovernanceState(
        artifacts=state["artifacts"],
        authority_actions=state["authority_actions"],
        validations=state["validations"],
        violations=state["violations"],
        last_event_timestamp=state["last_event_timestamp"],
        total_events=state["total_events"],
        drift_indicators=drift,
    )


def compute_drift_indicators(state: Dict[str, Any]) -> Dict[str, float]:
    """Compute quantitative drift indicators.
    
    Complies with HHI-GOV-01 Section 2.5: Drift Detection
    Drift detection MUST NOT depend on narrative explanation.
    
    Examples include:
    - acceptance versus override ratios
    - escalation frequency decay
    - review time compression
    - repetition velocity without review
    
    Args:
        state: Governance state dictionary.
        
    Returns:
        Dictionary of drift metrics and their values.
    """
    indicators = {}
    
    # 1. Validation success rate
    if state["validations"]:
        total_validations = len(state["validations"])
        passed = sum(1 for v in state["validations"].values() if v)
        indicators["validation_pass_rate"] = passed / total_validations if total_validations > 0 else 0.0
    else:
        indicators["validation_pass_rate"] = 0.0
    
    # 2. Violation frequency
    total_artifacts = len(state["artifacts"])
    total_violations = len(state["violations"])
    indicators["violation_density"] = total_violations / total_artifacts if total_artifacts > 0 else 0.0
    
    # 3. Authority concentration
    if state["authority_actions"]:
        total_actions = sum(state["authority_actions"].values())
        max_authority_actions = max(state["authority_actions"].values())
        indicators["authority_concentration"] = max_authority_actions / total_actions if total_actions > 0 else 0.0
    else:
        indicators["authority_concentration"] = 0.0
    
    # 4. Adversary detection rate
    adversary_events = [v for v in state["violations"] if v["type"] == "ADVERSARY_DETECTED"]
    indicators["adversary_detection_rate"] = len(adversary_events) / max(1, total_artifacts)
    
    # 5. Governance breach rate
    breach_events = [v for v in state["violations"] if v["type"] == "GOVERNANCE_BREACH"]
    indicators["governance_breach_rate"] = len(breach_events) / max(1, state["total_events"])
    
    return indicators


def replay_from_store(event_store: EventStore) -> GovernanceState:
    """Replay governance state from event store.
    
    Args:
        event_store: EventStore instance.
        
    Returns:
        Reconstructed GovernanceState.
    """
    events = event_store.load_all()
    return reduce_events(events)


def export_state_to_json(state: GovernanceState, output_file: str = "governance_state.json"):
    """Export governance state to JSON file.
    
    Args:
        state: GovernanceState to export.
        output_file: Output file path.
    """
    state_dict = {
        "artifacts": state.artifacts,
        "authority_actions": state.authority_actions,
        "validations": state.validations,
        "violations": state.violations,
        "last_event_timestamp": state.last_event_timestamp,
        "total_events": state.total_events,
        "drift_indicators": state.drift_indicators,
    }
    
    with open(output_file, "w") as f:
        json.dump(state_dict, f, indent=2)
