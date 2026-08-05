#!/usr/bin/env bash
# Runs every thing's test suite in its own subprocess (each has its own
# pyproject.toml / pythonpath config, and several projects share test file
# basenames like test_render.py -- running them all under one pytest
# invocation from the repo root causes import collisions, since none of
# these are meant to be one big package. Isolation is the point.
set -u

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
failures=()

for dir in "$repo_root"/things/*/; do
    name="$(basename "$dir")"
    if [ ! -f "$dir/pyproject.toml" ]; then
        continue
    fi
    echo "=== $name ==="
    (cd "$dir" && python3 -m pytest -q) || failures+=("$name")
    echo
done

if [ ${#failures[@]} -eq 0 ]; then
    echo "All things passed."
    exit 0
else
    echo "FAILED: ${failures[*]}"
    exit 1
fi
