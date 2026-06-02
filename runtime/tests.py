"""Integration tests for governance runtime.

Tests event store, reducer, agents, and proof generation.
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from runtime.event_store import EventStore, GovernanceEvent, EventType
from runtime.reducer import reduce_events, compute_drift_indicators
from runtime.agents import BuilderAgent, ValidatorAgent, AdversaryAgent
from runtime.proof_generator import ProofGenerator


class TestEventStore(unittest.TestCase):
    """Test event store functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "test.jsonl"
        self.store = EventStore(str(self.log_file))
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_append_event(self):
        """Test appending event to store."""
        event = GovernanceEvent(
            event_type=EventType.ARTIFACT_CREATED,
            artifact_id="TEST_001",
            authority="builder",
            timestamp=0.0,
            evidence={"test": True},
        )
        
        event_id = self.store.append(event)
        self.assertIsNotNone(event_id)
        self.assertEqual(len(event_id), 64)  # SHA256 hex
    
    def test_load_events(self):
        """Test loading events from store."""
        event = GovernanceEvent(
            event_type=EventType.ARTIFACT_CREATED,
            artifact_id="TEST_001",
            authority="builder",
            timestamp=0.0,
            evidence={},
        )
        
        self.store.append(event)
        loaded = self.store.load_all()
        
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].artifact_id, "TEST_001")
    
    def test_integrity_verification(self):
        """Test event hash integrity."""
        event = GovernanceEvent(
            event_type=EventType.ARTIFACT_CREATED,
            artifact_id="TEST_001",
            authority="builder",
            timestamp=0.0,
            evidence={},
        )
        
        self.store.append(event)
        self.assertTrue(self.store.verify_integrity())


class TestReducer(unittest.TestCase):
    """Test state reduction."""
    
    def test_reduce_single_event(self):
        """Test reducing single event."""
        event = GovernanceEvent(
            event_type=EventType.ARTIFACT_CREATED,
            artifact_id="TEST_001",
            authority="builder",
            timestamp=0.0,
            evidence={"hash": "sha256:abc123"},
        )
        
        state = reduce_events([event])
        
        self.assertEqual(state.total_events, 1)
        self.assertIn("TEST_001", state.artifacts)
        self.assertEqual(state.artifacts["TEST_001"]["created_by"], "builder")
    
    def test_compute_drift_indicators(self):
        """Test drift indicator computation."""
        state = {
            "artifacts": {"A": {}, "B": {}},
            "validations": {"A": True, "B": True},
            "violations": [],
            "authority_actions": {"builder": 5, "validator": 5},
            "total_events": 10,
        }
        
        drift = compute_drift_indicators(state)
        
        self.assertIn("validation_pass_rate", drift)
        self.assertIn("violation_density", drift)
        self.assertEqual(drift["validation_pass_rate"], 1.0)


class TestAgents(unittest.TestCase):
    """Test governance agents."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "test.jsonl"
        self.store = EventStore(str(self.log_file))
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_builder_agent(self):
        """Test builder agent creates artifacts."""
        builder = BuilderAgent(self.store)
        result = builder.create_artifact("TEST_001", authority="builder")
        
        self.assertEqual(result["artifact_id"], "TEST_001")
        self.assertIsNotNone(result["hash"])
        self.assertIsNotNone(result["event_id"])
    
    def test_validator_agent(self):
        """Test validator agent validates artifacts."""
        builder = BuilderAgent(self.store)
        builder.create_artifact("TEST_001")
        
        validator = ValidatorAgent(self.store)
        results = validator.validate_artifacts()
        
        self.assertIn("TEST_001", results["validations"])
    
    def test_adversary_agent(self):
        """Test adversary agent detects mutations."""
        builder = BuilderAgent(self.store)
        builder.create_artifact("TEST_001")
        
        adversary = AdversaryAgent(self.store)
        result = adversary.test_artifact("TEST_001", mutation_rate=0.1)
        
        self.assertEqual(result["artifact_id"], "TEST_001")
        self.assertTrue(result["detected"])  # Should detect mutation


class TestProofGenerator(unittest.TestCase):
    """Test proof generation."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "test.jsonl"
        self.store = EventStore(str(self.log_file))
        self.gen = ProofGenerator(self.store)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_generate_proof(self):
        """Test generating proof for artifact."""
        builder = BuilderAgent(self.store)
        builder.create_artifact("TEST_001")
        
        proof = self.gen.generate_proof("TEST_001")
        
        self.assertEqual(proof.artifact_id, "TEST_001")
        self.assertIsNotNone(proof.hash)
        self.assertIsNotNone(proof.event_chain_hash)
    
    def test_save_and_load_proof(self):
        """Test saving and loading proofs."""
        builder = BuilderAgent(self.store)
        builder.create_artifact("TEST_001")
        
        # Save proof
        result = self.gen.generate_and_save_proof("TEST_001")
        self.assertIn("file", result)
        
        # Load proof
        loaded = self.gen.load_proof("TEST_001")
        self.assertEqual(loaded.artifact_id, "TEST_001")


if __name__ == '__main__':
    unittest.main()
