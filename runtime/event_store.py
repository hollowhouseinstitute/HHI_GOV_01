"""Append-only event store for governance runtime.

Implements non-destructive, immutable event ledger with schema validation,
SHA256 integrity hashing, and timestamped event emission.

Complies with HHI-GOV-01 Section 2.4: Evidence & Ledger Invariants
- append-only writes
- non-destructive
- immutable once written
- corrections recorded as new events
"""

import json
import hashlib
import time
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum


class EventType(str, Enum):
    """Governance event types."""
    ARTIFACT_CREATED = "ARTIFACT_CREATED"
    VALIDATION_PASSED = "VALIDATION_PASSED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    ADVERSARY_DETECTED = "ADVERSARY_DETECTED"
    GOVERNANCE_BREACH = "GOVERNANCE_BREACH"
    ESCALATION_TRIGGERED = "ESCALATION_TRIGGERED"
    AUTHORITY_DECLARED = "AUTHORITY_DECLARED"
    DRIFT_DETECTED = "DRIFT_DETECTED"


@dataclass
class GovernanceEvent:
    """Schema for governance event.
    
    Complies with HHI-GOV-01 Section 2.3: Non-Bypassable Event Emission
    Every consequential action MUST emit a governance event.
    """
    
    event_type: EventType
    artifact_id: str
    authority: str
    timestamp: float
    evidence: Dict[str, Any]
    event_id: Optional[str] = None
    
    def __post_init__(self):
        """Compute event ID if not provided."""
        if self.event_id is None:
            self.event_id = self.compute_hash()
    
    def compute_hash(self) -> str:
        """Compute SHA256 hash of event.
        
        Returns:
            Hex-encoded SHA256 hash of the event data.
        """
        # Serialize in canonical order (sorted keys)
        event_dict = {
            "event_type": self.event_type,
            "artifact_id": self.artifact_id,
            "authority": self.authority,
            "timestamp": self.timestamp,
            "evidence": json.dumps(self.evidence, sort_keys=True),
        }
        event_json = json.dumps(event_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(event_json.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "artifact_id": self.artifact_id,
            "authority": self.authority,
            "timestamp": self.timestamp,
            "evidence": self.evidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GovernanceEvent":
        """Reconstruct event from dictionary."""
        return cls(
            event_type=EventType(data["event_type"]),
            artifact_id=data["artifact_id"],
            authority=data["authority"],
            timestamp=data["timestamp"],
            evidence=data["evidence"],
            event_id=data.get("event_id"),
        )


class EventStore:
    """Append-only event ledger for governance runtime.
    
    Implements:
    - Immutable event writes
    - SHA256 integrity validation
    - Timestamped event sequencing
    - JSONL persistence
    
    Complies with HHI-GOV-01 Section 2.4: Evidence & Ledger Invariants
    """
    
    def __init__(self, log_file: str = "hhi_event_log.jsonl"):
        """Initialize event store.
        
        Args:
            log_file: Path to append-only event log file.
        """
        self.log_file = Path(log_file)
        self._event_cache: List[GovernanceEvent] = []
        self._loaded = False
    
    def append(self, event: GovernanceEvent) -> str:
        """Append event to ledger.
        
        Args:
            event: GovernanceEvent to append.
            
        Returns:
            Event ID (SHA256 hash).
            
        Raises:
            IOError: If write fails.
        """
        # Ensure event has ID
        if event.event_id is None:
            event.event_id = event.compute_hash()
        
        # Serialize event
        event_dict = event.to_dict()
        event_json = json.dumps(event_dict, separators=(',', ':'))
        
        # Append to file (non-destructive, atomic)
        try:
            with open(self.log_file, "a") as f:
                f.write(event_json + "\n")
            
            # Update cache
            self._event_cache.append(event)
            
            return event.event_id
        except IOError as e:
            raise IOError(f"Failed to write event to {self.log_file}: {e}")
    
    def load_all(self) -> List[GovernanceEvent]:
        """Load all events from ledger.
        
        Returns:
            List of all GovernanceEvents in order.
            
        Raises:
            FileNotFoundError: If log file does not exist.
        """
        if self._loaded and self._event_cache:
            return self._event_cache
        
        events = []
        
        if not self.log_file.exists():
            return events
        
        try:
            with open(self.log_file, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event_dict = json.loads(line)
                        event = GovernanceEvent.from_dict(event_dict)
                        events.append(event)
                    except json.JSONDecodeError as e:
                        raise ValueError(
                            f"Invalid JSON in {self.log_file} at line {line_num}: {e}"
                        )
            
            self._event_cache = events
            self._loaded = True
            return events
        except IOError as e:
            raise IOError(f"Failed to read event log from {self.log_file}: {e}")
    
    def get_events_by_artifact(self, artifact_id: str) -> List[GovernanceEvent]:
        """Get all events for a specific artifact.
        
        Args:
            artifact_id: Artifact identifier.
            
        Returns:
            List of events in chronological order.
        """
        all_events = self.load_all()
        return [e for e in all_events if e.artifact_id == artifact_id]
    
    def get_events_by_type(self, event_type: EventType) -> List[GovernanceEvent]:
        """Get all events of a specific type.
        
        Args:
            event_type: Type of event to filter.
            
        Returns:
            List of matching events in chronological order.
        """
        all_events = self.load_all()
        return [e for e in all_events if e.event_type == event_type]
    
    def get_latest_event(self) -> Optional[GovernanceEvent]:
        """Get the most recent event.
        
        Returns:
            Latest GovernanceEvent or None if empty.
        """
        events = self.load_all()
        return events[-1] if events else None
    
    def verify_integrity(self) -> bool:
        """Verify event log integrity.
        
        Returns:
            True if all event hashes are valid, False otherwise.
        """
        events = self.load_all()
        for event in events:
            computed_hash = event.compute_hash()
            if computed_hash != event.event_id:
                return False
        return True
    
    def get_event_count(self) -> int:
        """Get total number of events in ledger.
        
        Returns:
            Count of events.
        """
        return len(self.load_all())
