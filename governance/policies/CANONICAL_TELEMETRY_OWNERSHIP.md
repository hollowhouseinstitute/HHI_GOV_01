# CANONICAL TELEMETRY OWNERSHIP POLICY

## Canonical Runtime Telemetry Locations

ACTIVE RUNTIME TELEMETRY:
- runtime/logs/
- runtime/telemetry/append_only/

These locations are authoritative for:
- governance telemetry
- escalation telemetry
- immutable audit chains
- replay continuity
- drift monitoring
- governance events

## Non-Canonical Telemetry Locations

The following locations are retained only for:
- historical continuity
- exports
- snapshots
- replay evidence
- legacy compatibility

Examples:
- authority/telemetry/
- artifacts/telemetry/
- snapshot telemetry mirrors

## Governance Rule

Do not introduce new live telemetry writers outside:
- runtime/logs/
- runtime/telemetry/append_only/

Telemetry duplication increases:
- authority ambiguity
- replay inconsistency
- governance drift risk
