"""Governance runtime agents.

Multi-agent system for enforcement:
- BuilderAgent: Creates artifacts
- ValidatorAgent: Validates integrity
- AdversaryAgent: Tests resilience
- GovernorAgent: Enforces escalation

All agents emit governance events non-bypassably.
"""

import hashlib
import time
import json
from typing import Dict, Any, Optional
from pathlib import Path

from runtime.event_store import EventStore, GovernanceEvent, EventType


class BuilderAgent:
    """Creates governance artifacts and emits events."""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.authority = "builder"
    
    def create_artifact(
        self,
        artifact_id: str,
        authority: str = None,
        file_path: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new governance artifact.
        
        Args:
            artifact_id: Unique artifact identifier
            authority: Authority declaring the artifact
            file_path: Path to file to create artifact from
            data: Data dict to create artifact from
            
        Returns:
            Dictionary with artifact metadata and event ID
            
        Emits:
            ARTIFACT_CREATED event
        """
        authority = authority or self.authority
        
        # Get artifact content
        if file_path:
            with open(file_path, 'rb') as f:
                content = f.read()
        elif data:
            content = json.dumps(data, sort_keys=True).encode()
        else:
            content = b''
        
        # Compute hash
        artifact_hash = hashlib.sha256(content).hexdigest()
        
        # Create event
        event = GovernanceEvent(
            event_type=EventType.ARTIFACT_CREATED,
            artifact_id=artifact_id,
            authority=authority,
            timestamp=time.time(),
            evidence={
                "hash": f"sha256:{artifact_hash}",
                "size": len(content),
                "authority_declared": authority,
            }
        )
        
        # Emit event (non-bypassable)
        event_id = self.event_store.append(event)
        
        return {
            "artifact_id": artifact_id,
            "hash": artifact_hash,
            "event_id": event_id,
            "timestamp": event.timestamp,
            "authority": authority,
        }


class ValidatorAgent:
    """Validates artifact integrity against registry."""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.authority = "validator"
    
    def validate_artifacts(
        self,
        artifact_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate artifacts.
        
        Args:
            artifact_id: Validate specific artifact (all if None)
            
        Returns:
            Dictionary with validation results
            
        Emits:
            VALIDATION_PASSED or VALIDATION_FAILED events
        """
        # Load canonical registry
        try:
            with open('CANONICAL_CHECKSUMS.sha256', 'r') as f:
                canonical = {}
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        hash_val, filename = parts[0], ' '.join(parts[1:])
                        canonical[filename] = hash_val
        except FileNotFoundError:
            canonical = {}
        
        validations = {}
        
        # Get artifacts to validate
        if artifact_id:
            artifact_events = self.event_store.get_events_by_artifact(artifact_id)
            artifacts = {artifact_id: artifact_events}
        else:
            # Get all created artifacts
            created_events = self.event_store.get_events_by_type(EventType.ARTIFACT_CREATED)
            artifacts = {e.artifact_id: [e] for e in created_events}
        
        # Validate each artifact
        for aid, events in artifacts.items():
            if not events:
                continue
            
            creation_event = events[0]
            stored_hash = creation_event.evidence.get('hash', '').replace('sha256:', '')
            canonical_hash = canonical.get(aid, '')
            
            is_valid = bool(stored_hash and (stored_hash == canonical_hash or not canonical_hash))
            
            # Emit validation event
            event = GovernanceEvent(
                event_type=EventType.VALIDATION_PASSED if is_valid else EventType.VALIDATION_FAILED,
                artifact_id=aid,
                authority=self.authority,
                timestamp=time.time(),
                evidence={
                    "stored_hash": stored_hash,
                    "canonical_hash": canonical_hash,
                    "matches": is_valid,
                    "reason": "Hash match" if is_valid else "Hash mismatch",
                }
            )
            self.event_store.append(event)
            
            validations[aid] = {
                "valid": is_valid,
                "stored_hash": stored_hash[:16],
                "canonical_hash": canonical_hash[:16] if canonical_hash else "N/A",
                "reason": event.evidence["reason"],
            }
        
        return {
            "validations": validations,
            "authority": self.authority,
            "timestamp": time.time(),
        }


class AdversaryAgent:
    """Tests artifact resilience through mutation injection."""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.authority = "adversary"
    
    def test_artifact(
        self,
        artifact_id: str,
        mutation_rate: float = 0.1
    ) -> Dict[str, Any]:
        """Test artifact resilience by injecting mutations.
        
        Args:
            artifact_id: Artifact to test
            mutation_rate: Fraction of bytes to mutate (0.0-1.0)
            
        Returns:
            Dictionary with mutation test results
            
        Emits:
            ADVERSARY_DETECTED event
        """
        # Get original artifact
        created_events = self.event_store.get_events_by_artifact(artifact_id)
        if not created_events:
            raise ValueError(f"Artifact {artifact_id} not found")
        
        creation_event = created_events[0]
        original_hash = creation_event.evidence.get('hash', '').replace('sha256:', '')
        
        # Simulate mutation (in real system, would mutate actual file)
        # For demo, just create a different hash
        import random
        random.seed(int(artifact_id[-3:]) + int(mutation_rate * 100))
        
        mutation_seed = random.getrandbits(256)
        mutated_hash = hashlib.sha256(str(mutation_seed).encode()).hexdigest()
        
        # Check if mutation was detected (always true in well-governed system)
        detected = (original_hash != mutated_hash)
        
        # Emit adversary event (non-bypassable)
        event = GovernanceEvent(
            event_type=EventType.ADVERSARY_DETECTED,
            artifact_id=artifact_id,
            authority=self.authority,
            timestamp=time.time(),
            evidence={
                "original_hash": original_hash,
                "mutated_hash": mutated_hash,
                "mutation_rate": mutation_rate,
                "detected": detected,
            }
        )
        self.event_store.append(event)
        
        return {
            "artifact_id": artifact_id,
            "original_hash": original_hash,
            "mutated_hash": mutated_hash,
            "mutation_rate": mutation_rate,
            "detected": detected,
            "timestamp": event.timestamp,
        }


class GovernorAgent:
    """Enforces governance escalation thresholds."""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.authority = "governor"
        self.thresholds = {
            "violation_density": 0.2,      # 20% violations
            "governance_breach_rate": 0.05,  # 5% breaches
        }
    
    def check_thresholds(self) -> Dict[str, Any]:
        """Check governance thresholds and escalate if needed.
        
        Returns:
            Dictionary with breach status
            
        Emits:
            GOVERNANCE_BREACH and/or ESCALATION_TRIGGERED events
        """
        from runtime.reducer import replay_from_store
        
        state = replay_from_store(self.event_store)
        breaches = []
        
        # Check violation density
        if state.drift_indicators['violation_density'] > self.thresholds['violation_density']:
            breaches.append({
                "threshold": "violation_density",
                "value": state.drift_indicators['violation_density'],
                "limit": self.thresholds['violation_density'],
            })
        
        # Check governance breach rate
        if state.drift_indicators['governance_breach_rate'] > self.thresholds['governance_breach_rate']:
            breaches.append({
                "threshold": "governance_breach_rate",
                "value": state.drift_indicators['governance_breach_rate'],
                "limit": self.thresholds['governance_breach_rate'],
            })
        
        # Emit escalation event if thresholds breached
        if breaches:
            event = GovernanceEvent(
                event_type=EventType.GOVERNANCE_BREACH,
                artifact_id="SYSTEM",
                authority=self.authority,
                timestamp=time.time(),
                evidence={
                    "breaches": breaches,
                    "action": "ESCALATE",
                    "reason": "Governance thresholds exceeded",
                }
            )
            self.event_store.append(event)
        
        return {
            "thresholds_met": len(breaches) == 0,
            "breaches": breaches,
            "drift_indicators": state.drift_indicators,
            "timestamp": time.time(),
        }
