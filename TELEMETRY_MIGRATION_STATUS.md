# TELEMETRY MIGRATION STATUS

## Canonical Runtime Telemetry
ACTIVE:
- runtime/logs/
- runtime/telemetry/append_only/

## Legacy Compatibility Surfaces
COMPATIBILITY ONLY:
- telemetry/
- authority/telemetry/
- evidence/telemetry/
- automation/telemetry/

## Runtime Components Already Migrated
- runtime/enforcement/telemetry.py
- runtime/enforcement/replay.py
- runtime/event_bus/governance_event_bus.py
- runtime/api/governance_runtime_api.py

## Legacy Components Pending Migration
- governance/*.sh
- telemetry/*.sh
- .github/workflows/*.yml
- tools/governance_gate.sh

## Governance Rule
No new runtime telemetry writers should target:
- telemetry/
- authority/telemetry/
- evidence/telemetry/
- automation/telemetry/

## Migration Strategy
Migration must preserve:
- replay continuity
- checksum continuity
- CI survivability
- export compatibility
- append-only evidence integrity
