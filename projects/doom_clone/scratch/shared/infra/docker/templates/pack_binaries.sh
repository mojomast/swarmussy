#!/usr/bin/env bash
set -euo pipefail
TARGET="$1"
ARTIFACTS_DIR="$2"
mkdir -p "$ARTIFACTS_DIR"

# Copy each workspace crate's binaries for the target into the artifacts dir
for member in $(jq -r '.workspace_members[]' < Cargo.toml); do
  crate_dir="${WORKSPACE_ROOT:-$(pwd)}/$member/target/${TARGET}"
  if [ -d "$crate_dir" ]; then
    for f in "$crate_dir"/*; do
      if [ -f "$f" ]; then
        cp "$f" "$ARTIFACTS_DIR"
      fi
    done
  fi
done
