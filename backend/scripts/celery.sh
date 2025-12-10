#!/bin/bash
# Simple wrapper script for Celery CLI
# Usage: ./scripts/celery.sh [worker|beat|both|flower|status]

cd "$(dirname "$0")/.." || exit 1

python scripts/celery_cli.py "$@"
