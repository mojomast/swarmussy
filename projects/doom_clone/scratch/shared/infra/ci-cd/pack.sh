#!/usr/bin/env bash
set -euo pipefail
TARGET="$1"
ARTIFACTS_DIR=artifacts
mkdir -p "$ARTIFACTS_DIR"
# Package workspace crates as tarballs per target
PACKAGE_DIR="${ARTIFACTS_DIR}/${TARGET}"
mkdir -p "$PACKAGE_DIR"

# Discover workspace members from Cargo.toml without external JSON tools
if [ ! -f Cargo.toml ]; then
  echo "Cargo.toml not found in $(pwd)." >&2
  exit 1
fi
python3 scratch/shared/infra/ci-cd/list_ws_members.py | while read -r member; do
  if [ -z "$member" ]; then
    continue
  fi
  crate_cargo="$member/Cargo.toml"
  if [ ! -f "$crate_cargo" ]; then
    echo "Cargo.toml not found for member $member, skipping." >&2
    continue
  fi
  crate_name=$(grep -m1 '^name\s*=\s*"' "$crate_cargo" | sed -E 's/.*name\s*=\s*"([^"]+)".*/\1/')
  if [ -z "$crate_name" ]; then
    # Fallback: use directory name
    crate_name=$(basename "$member")
  fi
  echo "Packaging crate '$crate_name' (path: $member) for target '$TARGET'"
  # Build the specific crate for the target
  cargo build --release --manifest-path "$crate_cargo" --target "$TARGET" -p "$crate_name" >/dev/null 2>&1 || true
  binary_path="$member/target/${TARGET}/release/${crate_name}"
  if [ -f "$binary_path" ]; then
    tar -czf "$PACKAGE_DIR/${crate_name}-${TARGET}.tar.gz" -C "$member/target/${TARGET}/release" "$crate_name"
  else
    # Some crates may output a binary with a different extension on Windows (.exe)
    if [ -f "$binary_path.exe" ]; then
      tar -czf "$PACKAGE_DIR/${crate_name}-${TARGET}.tar.gz" -C "$member/target/${TARGET}/release" "$crate_name.exe"
    else
      echo "No binary found for crate '$crate_name' at expected location: $binary_path" >&2
    fi
  fi
done

echo "Artifacts prepared in $PACKAGE_DIR
