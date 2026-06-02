#!/usr/bin/env python3
"""HHI Governance Runtime CLI Entry Point

Usage:
    hhi create <artifact-id>
    hhi validate
    hhi replay
    hhi adversary <artifact-id>
    hhi status
    hhi logs
"""

from runtime.commands import cli


if __name__ == '__main__':
    cli(obj={})
