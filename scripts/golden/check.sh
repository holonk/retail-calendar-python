#!/usr/bin/env bash
# Checks that tests/data/golden is exactly what the pinned JS package generates.
#
# Compressed files are compared by their decompressed content: gzip headers record the OS that wrote them, and
# zlib versions may compress the same data differently, so the .gz bytes differ between macOS and Linux.
#
#   cd scripts/golden && npm ci && ./check.sh
set -euo pipefail

cd "$(dirname "$0")"
expected="../../tests/data/golden"
actual="$(mktemp -d)"
trap 'rm -rf "$actual"' EXIT

TZ=UTC node generate.mjs "$actual" > /dev/null

if ! diff <(ls "$expected") <(ls "$actual"); then
  echo "Generated files differ from the files in tests/data/golden" >&2
  exit 1
fi

status=0
for path in "$expected"/*; do
  name="$(basename "$path")"
  if [[ "$name" == *.gz ]]; then
    cmp -s <(gzip -dc "$path") <(gzip -dc "$actual/$name") || { echo "$name is out of date" >&2; status=1; }
  else
    cmp -s "$path" "$actual/$name" || { echo "$name is out of date" >&2; status=1; }
  fi
done

if [[ $status -ne 0 ]]; then
  echo "Regenerate with: cd scripts/golden && npm run generate" >&2
else
  echo "Golden data is up to date"
fi
exit $status
