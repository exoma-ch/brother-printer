# PT-E920BT vendor documentation

Official Brother documentation for the PT-E920BT, stored as grep-friendly text dumps.
Raw PDFs are **not** committed; fetch them on demand into `cache/`.

## Quick start

```bash
./docs/vendor/fetch.sh
apt-get install -y poppler-utils   # one-time; not in devcontainer image
./docs/vendor/convert.sh
```

See [INDEX.md](INDEX.md) for provenance (source URLs, versions, SHA256, license notes).

## Canonical fact files

Downstream code and ADRs should link to these instead of re-deriving values:

- [usb-ids.md](usb-ids.md) — USB vendor/product IDs and descriptors
- [tze-tape-widths.md](tze-tape-widths.md) — TZe tape widths and printable pixel widths at 360 dpi

## Redistribution policy

This repo commits **text dumps only** (derivative extracts via `pdftotext`), not the
original PDFs. See the *License / redistribution* column in [INDEX.md](INDEX.md).
