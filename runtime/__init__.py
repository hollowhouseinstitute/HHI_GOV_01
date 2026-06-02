"""HHI Governance Runtime Package

Provides event store, state reduction, and agent orchestration
for execution-time governance enforcement.
"""

from runtime.event_store import EventStore, GovernanceEvent
from runtime.reducer import reduce_events, compute_drift_indicators

__version__ = "0.1.0"
__all__ = [
    "EventStore",
    "GovernanceEvent",
    "reduce_events",
    "compute_drift_indicators",
]
