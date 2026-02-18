#!/bin/bash
# Batch process all PDFs in bookshelf directory

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/process_$TIMESTAMP.log"

echo "=== Avicenna Batch Processing ==="
echo "Started: $(date)"
echo "HF_ENDPOINT: $HF_ENDPOINT"
echo "Log file: $LOG_FILE"
echo ""

avicenna process "$@" 2>&1 | tee "$LOG_FILE"

echo ""
echo "=== Completed: $(date) ==="
