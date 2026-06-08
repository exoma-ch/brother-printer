#!/usr/bin/env bash
# Convert cached PDFs to text dumps under docs/vendor/.
# Requires poppler-utils (pdftotext). Install ad-hoc: apt-get install -y poppler-utils

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${SCRIPT_DIR}/cache"

if ! command -v pdftotext >/dev/null 2>&1; then
  echo "ERROR: pdftotext not found. Install poppler-utils first." >&2
  exit 1
fi

# Only convert docs with committed text dumps. See INDEX.md for stubs (template, ESC/P).
declare -A MAP=(
  ["pt-e920bt-user-guide.pdf"]="pt-e920bt-user-guide.md"
  ["ptouch-raster-command-reference.pdf"]="ptouch-raster-command-reference.md"
)

for pdf in "${!MAP[@]}"; do
  src="${CACHE_DIR}/${pdf}"
  dst="${SCRIPT_DIR}/${MAP[${pdf}]}"
  if [[ ! -f "${src}" ]]; then
    echo "ERROR: missing ${src} — run fetch.sh first" >&2
    exit 1
  fi
  echo "==> ${pdf} -> ${MAP[${pdf}]}"
  {
    echo "<!-- Converted from ${pdf}. Provenance: see INDEX.md -->"
    echo
    pdftotext -layout "${src}" -
  } > "${dst}"
done

echo "Done."
