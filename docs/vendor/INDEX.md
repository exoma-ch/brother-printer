# PT-E920BT vendor documentation index

Provenance for all documents under `docs/vendor/`. This file is the single source of
truth for URLs, versions, retrieval dates, and SHA256 checksums.

Retrieval date for all entries: **2026-05-28**.

| Document | Text dump | Applicability | Source URL | Version | SHA256 (PDF) | License / redistribution |
| --- | --- | --- | --- | --- | --- | --- |
| User's Guide (PT-E720BT / PT-E920BT) | [pt-e920bt-user-guide.md](pt-e920bt-user-guide.md) | **Direct** — covers PT-E920BT | https://support.brother.com/g/s/es/htmldoc/ptouch/e720bt/uken/PDF/PDF.pdf | PDF dated 2025-09-29 (`Last-Modified` header); EU manual portal lists 2025-05-08(01) | `3c6b584298e466dc17bcb4f92d9f2f5aec287aea8cfedd1c50614d318ffbb33e` | End-user guide; text dump committed (no PDF). © Brother Industries, Ltd. |
| Raster Command Reference (PT-P900/P900W/P950NW/P910BT) | [ptouch-raster-command-reference.md](ptouch-raster-command-reference.md) | **Proxy** — no PT-E920BT-specific manual published; same 360 dpi / 560-pin head as PT-P900 family per User's Guide specs | https://download.brother.com/welcome/docp100407/cv_ptp900_eng_raster_102.pdf | 1.02 (© 2020) | `7e3ed949ae56a7771f20bd420a8eb39ce107da46eb17b5f773ec6c100411a6a1` | Developer manual; text dump committed (no PDF). © Brother Industries, Ltd. |
| P-touch Template Command Reference (PT-P900 family — not applicable) | [ptouch-template-command-reference.md](ptouch-template-command-reference.md) (stub) | **Not applicable** — PT-E920BT not on command-reference page or SDK P-touch Template matrix | https://download.brother.com/welcome/docp100187/cv_ptp900_eng_ptemp_103.pdf | 1.03 (© 2016) | `85d233df84668d6cf578f1833cb27069c76d35cc45230fd6f00d34989f29dd1e` | Fetchable via `fetch.sh`; text dump not committed (stub + link only). |
| ESC/P Command Reference (PT-P900 family — not applicable) | [escp-command-reference.md](escp-command-reference.md) (stub) | **Not applicable** — PT-E920BT advertises Raster + Mobile SDK only | https://download.brother.com/welcome/docp100186/cv_ptp900_eng_escp_103.pdf | 1.03 (© 2016) | `642043216f236a87b376008cfec0e2ebe04088fe86160fe2cdc452a497a067b6` | Fetchable via `fetch.sh`; text dump not committed (stub + link only). |

## Extracted fact files

| Topic | File | Primary source |
| --- | --- | --- |
| USB IDs and endpoints | [usb-ids.md](usb-ids.md) | User's Guide + Raster Command Reference Appendix A (family) |
| TZe tape widths @ 360 dpi | [tze-tape-widths.md](tze-tape-widths.md) | User's Guide specs + Raster Command Reference §2.3.5 |

## Fetch and regenerate

```bash
./docs/vendor/fetch.sh          # downloads PDFs to cache/ (gitignored), verifies SHA256
apt-get install -y poppler-utils
./docs/vendor/convert.sh        # regenerates committed text dumps from cache/
```

## PT-E920BT vs other P-touch models

| Topic | PT-E920BT | PT-E720BT | PT-P900 / P910BT family (proxy docs) |
| --- | --- | --- | --- |
| Print resolution | 560 dots / **360 dpi** | 64 dots / 180 dpi | 560 pins / **360 dpi** |
| Max print height | 32 mm | 18 mm | 32 mm (P910BT) |
| Max tape width | 36 mm (+ FLe labels) | 24 mm | 36 mm |
| USB connector | USB Type-C | USB Micro-B | varies |
| Published raster manual | **None** (use P900-family proxy) | None | Yes (cv_ptp900_eng_raster_102.pdf) |
| Command reference page | **Not listed** | Not listed | Listed (PT-P950NW download portal) |
| Advertised host languages | Raster, Mobile SDK | Raster, Mobile SDK (per EDGE product line) | Raster, P-touch Template, ESC/P |

## Related Brother portals

- [PT-E920BT manuals (US)](https://support.brother.com/g/b/manualtop.aspx?c=us&lang=en&prod=e920bteus)
- [Brother Developer Center](https://support.brother.com/g/s/es/dev/en/index.html)
- [Command reference model list](https://support.brother.com/g/s/es/dev/en/command/reference/index.html)
