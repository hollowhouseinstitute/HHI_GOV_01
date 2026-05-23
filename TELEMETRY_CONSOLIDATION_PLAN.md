# TELEMETRY CONSOLIDATION PLAN

## Objective
Reduce active runtime telemetry duplication while preserving replay continuity.

## Canonical Live Telemetry
- runtime/logs/
- runtime/telemetry/append_only/

## Legacy / Historical Surfaces
- authority/telemetry/
- artifacts/telemetry/
- snapshot telemetry mirrors

## Rules
- preserve immutable evidence
- preserve replay continuity
- preserve snapshot lineage
- preserve export compatibility

## Prohibited Actions
- deleting replay evidence
- deleting snapshots without verification
- recursive telemetry rewrites
- global mutation scripts

## Future Direction
All active runtime governance telemetry should converge toward:
- runtime/logs/
- runtime/telemetry/append_only/
