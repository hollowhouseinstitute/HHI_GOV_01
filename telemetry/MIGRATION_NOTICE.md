# TELEMETRY MIGRATION NOTICE

This telemetry surface is retained for:
- legacy governance tooling
- CI compatibility
- replay continuity
- export compatibility

Canonical runtime telemetry ownership has migrated to:
- runtime/logs/
- runtime/telemetry/append_only/

Future runtime enforcement development should target:
- runtime/telemetry/
- runtime/logs/

This location should gradually transition into:
- compatibility exports
- replay mirrors
- legacy ingestion surfaces
