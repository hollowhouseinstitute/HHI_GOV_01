# TELEMETRY RUNTIME VARIABLE STANDARD

Canonical runtime telemetry variables:

RUNTIME_TELEMETRY_DIR=runtime/telemetry/append_only
RUNTIME_LOG_DIR=runtime/logs

Legacy compatibility variables:
LEGACY_GOVERNANCE_LOG=telemetry/GOVERNANCE_LOG.jsonl

New runtime tooling should avoid introducing:
- hardcoded telemetry paths
- duplicate telemetry writers
- non-runtime telemetry ownership
