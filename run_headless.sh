#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
chmod +x ./run.sh 2>/dev/null
./run.sh --no-display --output-video output/annotated_traffic.mp4 "$@"
