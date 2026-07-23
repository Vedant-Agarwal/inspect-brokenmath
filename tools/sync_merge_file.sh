#!/usr/bin/env bash
# MANAGED FILE - Updates pulled from template. See MANAGED_FILES.md
# Three-way merge for a single managed file.
#
# Usage: sync_merge_file.sh <base> <ours> <theirs> <output>
#
# Exit codes:
#   0 — clean merge (or only one side changed)
#   1 — conflict (output contains conflict markers)
#   2 — no base file; output is a copy of theirs (hard overwrite)
set -euo pipefail

base="$1"
ours="$2"
theirs="$3"
output="$4"

if [ ! -f "$base" ]; then
    cp "$theirs" "$output"
    exit 2
fi

# git merge-file works in-place on the first argument, so copy ours to output
cp "$ours" "$output"

if git merge-file "$output" "$base" "$theirs"; then
    exit 0
else
    # git merge-file returns >0 when there are conflicts
    exit 1
fi
