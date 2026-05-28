#!/usr/bin/env bash
# Fetch official Brother PDFs into docs/vendor/cache/ (gitignored).
# See INDEX.md for provenance. Run from repo root or this directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${SCRIPT_DIR}/cache"
mkdir -p "${CACHE_DIR}"

declare -A DOCS=(
  ["pt-e920bt-user-guide.pdf"]="https://support.brother.com/g/s/es/htmldoc/ptouch/e720bt/uken/PDF/PDF.pdf"
  ["ptouch-raster-command-reference.pdf"]="https://download.brother.com/welcome/docp100407/cv_ptp900_eng_raster_102.pdf"
  ["ptouch-template-command-reference.pdf"]="https://download.brother.com/welcome/docp100187/cv_ptp900_eng_ptemp_103.pdf"
  ["escp-command-reference.pdf"]="https://download.brother.com/welcome/docp100186/cv_ptp900_eng_escp_103.pdf"
)

declare -A SHA256=(
  ["pt-e920bt-user-guide.pdf"]="3c6b584298e466dc17bcb4f92d9f2f5aec287aea8cfedd1c50614d318ffbb33e"
  ["ptouch-raster-command-reference.pdf"]="7e3ed949ae56a7771f20bd420a8eb39ce107da46eb17b5f773ec6c100411a6a1"
  ["ptouch-template-command-reference.pdf"]="85d233df84668d6cf578f1833cb27069c76d35cc45230fd6f00d34989f29dd1e"
  ["escp-command-reference.pdf"]="642043216f236a87b376008cfec0e2ebe04088fe86160fe2cdc452a497a067b6"
)

download() {
  local name="$1"
  local url="$2"
  local dest="${CACHE_DIR}/${name}"

  echo "==> ${name}"
  curl -fsSL -o "${dest}.tmp" "${url}"
  mv "${dest}.tmp" "${dest}"

  local hash
  hash="$(sha256sum "${dest}" | awk '{print $1}')"
  echo "    sha256: ${hash}"
  echo "    size:   $(wc -c < "${dest}") bytes"

  local expected="${SHA256[${name}]:-}"
  if [[ -n "${expected}" && "${hash}" != "${expected}" ]]; then
    echo "ERROR: SHA256 mismatch for ${name}" >&2
    echo "  expected: ${expected}" >&2
    echo "  got:      ${hash}" >&2
    exit 1
  fi
}

for name in "${!DOCS[@]}"; do
  download "${name}" "${DOCS[${name}]}"
done

echo
echo "Done. PDFs saved under ${CACHE_DIR}/"
echo "Next: install poppler-utils and run ./docs/vendor/convert.sh"
