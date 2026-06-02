"""Proof generator for governance runtime.

Generates cryptographic proofs that artifacts are governed according to HHI-GOV-01.

Proof structure:
- Artifact metadata (ID, hash, creation timestamp)
- Governance evidence (events, validation status)
- Cryptographic bindings (SHA256 chains)
- Authority declaration
- Adversarial testing results
"""

import json
import hashlib
import time
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from runtime.event_store import EventStore, EventType
from runtime.reducer import replay_from_store


@dataclass
class GovernanceProof:
    """Cryptographic proof of governance."""
    
    artifact_id: str
    hash: str
    created_by: str
    created_at: float
    validated_by: Optional[str]
    validated_at: Optional[float]
    validation_passed: bool
    event_chain_hash: str
    event_count: int
    adversary_tested: bool
    drift_indicators: Dict[str, float]
    proof_id: Optional[str] = None
    
    def compute_proof_id(self) -> str:
        """Compute deterministic proof ID.
        
        Returns:
            SHA256 hash of proof data.
        """
        proof_data = {
            "artifact_id": self.artifact_id,
            "hash": self.hash,
            "created_at": self.created_at,
            "validated_at": self.validated_at,
            "event_chain_hash": self.event_chain_hash,
        }
        proof_json = json.dumps(proof_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(proof_json.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert proof to dictionary."""
        if not self.proof_id:
            self.proof_id = self.compute_proof_id()
        
        return {
            "proof_id": self.proof_id,
            "artifact_id": self.artifact_id,
            "hash": self.hash,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "validated_by": self.validated_by,
            "validated_at": self.validated_at,
            "validation_passed": self.validation_passed,
            "event_chain_hash": self.event_chain_hash,
            "event_count": self.event_count,
            "adversary_tested": self.adversary_tested,
            "drift_indicators": self.drift_indicators,
        }


class ProofGenerator:
    """Generates governance proofs from event store and state."""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.proofs_dir = Path("runtime/proofs")
        self.proofs_dir.mkdir(parents=True, exist_ok=True)
    
    def compute_event_chain_hash(self, artifact_id: str) -> str:
        """Compute SHA256 hash of event chain for artifact.
        
        Args:
            artifact_id: Artifact identifier.
            
        Returns:
            SHA256 hash of event chain.
        """
        events = self.event_store.get_events_by_artifact(artifact_id)
        
        # Build chain by hashing events in sequence
        chain_data = []
        for event in events:
            chain_data.append(event.event_id)
        
        chain_json = json.dumps(chain_data, separators=(',', ':'))
        return hashlib.sha256(chain_json.encode()).hexdigest()
    
    def generate_proof(self, artifact_id: str) -> GovernanceProof:
        """Generate proof for artifact.
        
        Args:
            artifact_id: Artifact to prove.
            
        Returns:
            GovernanceProof instance.
            
        Raises:
            ValueError: If artifact not found.
        """
        # Get creation event
        created_events = self.event_store.get_events_by_artifact(artifact_id)
        if not created_events:
            raise ValueError(f"Artifact {artifact_id} not found")
        
        creation_event = created_events[0]
        artifact_hash = creation_event.evidence.get('hash', '').replace('sha256:', '')
        
        # Get validation status
        validation_events = [
            e for e in created_events
            if e.event_type in [EventType.VALIDATION_PASSED, EventType.VALIDATION_FAILED]
        ]
        
        validation_passed = False
        validated_by = None
        validated_at = None
        
        if validation_events:
            latest_validation = validation_events[-1]
            validation_passed = latest_validation.event_type == EventType.VALIDATION_PASSED
            validated_by = latest_validation.authority
            validated_at = latest_validation.timestamp
        
        # Check if adversary tested
        adversary_events = [
            e for e in created_events
            if e.event_type == EventType.ADVERSARY_DETECTED
        ]
        adversary_tested = bool(adversary_events)
        
        # Get current state for drift indicators
        state = replay_from_store(self.event_store)
        drift_indicators = state.drift_indicators
        
        # Compute event chain hash
        event_chain_hash = self.compute_event_chain_hash(artifact_id)
        
        proof = GovernanceProof(
            artifact_id=artifact_id,
            hash=artifact_hash,
            created_by=creation_event.authority,
            created_at=creation_event.timestamp,
            validated_by=validated_by,
            validated_at=validated_at,
            validation_passed=validation_passed,
            event_chain_hash=event_chain_hash,
            event_count=len(created_events),
            adversary_tested=adversary_tested,
            drift_indicators=drift_indicators,
        )
        
        return proof
    
    def save_proof(self, proof: GovernanceProof) -> Path:
        """Save proof to file.
        
        Args:
            proof: GovernanceProof to save.
            
        Returns:
            Path to proof file.
        """
        if not proof.proof_id:
            proof.proof_id = proof.compute_proof_id()
        
        proof_file = self.proofs_dir / f"{proof.artifact_id}.json"
        
        with open(proof_file, 'w') as f:
            json.dump(proof.to_dict(), f, indent=2)
        
        return proof_file
    
    def generate_and_save_proof(self, artifact_id: str) -> Dict[str, Any]:
        """Generate and save proof for artifact.
        
        Args:
            artifact_id: Artifact to prove.
            
        Returns:
            Dictionary with proof data and file path.
        """
        proof = self.generate_proof(artifact_id)
        proof_file = self.save_proof(proof)
        
        return {
            "artifact_id": artifact_id,
            "proof": proof.to_dict(),
            "file": str(proof_file),
        }
    
    def generate_batch_proofs(self) -> Dict[str, Any]:
        """Generate proofs for all artifacts.
        
        Returns:
            Dictionary with all proofs.
        """
        state = replay_from_store(self.event_store)
        
        proofs = {}
        for artifact_id in state.artifacts.keys():
            try:
                result = self.generate_and_save_proof(artifact_id)
                proofs[artifact_id] = result["proof"]
            except ValueError:
                pass
        
        return proofs
    
    def load_proof(self, artifact_id: str) -> GovernanceProof:
        """Load proof from file.
        
        Args:
            artifact_id: Artifact ID.
            
        Returns:
            GovernanceProof instance.
            
        Raises:
            FileNotFoundError: If proof not found.
        """
        proof_file = self.proofs_dir / f"{artifact_id}.json"
        
        if not proof_file.exists():
            raise FileNotFoundError(f"Proof not found: {proof_file}")
        
        with open(proof_file, 'r') as f:
            data = json.load(f)
        
        return GovernanceProof(
            artifact_id=data["artifact_id"],
            hash=data["hash"],
            created_by=data["created_by"],
            created_at=data["created_at"],
            validated_by=data["validated_by"],
            validated_at=data["validated_at"],
            validation_passed=data["validation_passed"],
            event_chain_hash=data["event_chain_hash"],
            event_count=data["event_count"],
            adversary_tested=data["adversary_tested"],
            drift_indicators=data["drift_indicators"],
            proof_id=data["proof_id"],
        )
