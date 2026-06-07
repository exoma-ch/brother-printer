# TZe tape widths — PT-E920BT @ 360 dpi

Canonical tape-width facts for raster encoding. Printable pixel widths are from the
360 dpi PT-P900-family Raster Command Reference (proxy for PT-E920BT; see
[INDEX.md](INDEX.md)).

## Supported tape widths (PT-E920BT)

From User's Guide, Appendix > Specifications > Media Specification
([pt-e920bt-user-guide.md](pt-e920bt-user-guide.md)):

| Tape width (mm) | Cassette types |
| --- | --- |
| 3.5 | TZe, HGe, FLe |
| 6 | TZe, HGe, FLe |
| 9 | TZe, HGe, FLe |
| 12 | TZe, HGe, FLe |
| 18 | TZe, HGe, FLe |
| 24 | TZe, HGe, FLe |
| 36 | TZe, HGe, FLe |

PT-E720BT (same User's Guide) omits 36 mm and FLe labels.

## Print head and resolution

| Parameter | PT-E920BT value | Source |
| --- | --- | --- |
| Print resolution | 560 dots / **360 dpi** | User's Guide, Appendix > Specifications > Printing |
| Total print-head pins | **560** | Raster Command Reference §2.3.5 (360 dpi models) |
| Maximum print height | 32 mm | User's Guide, Appendix > Specifications > Printing |
| Raster line payload | **70 bytes** uncompressed (560 pins ÷ 8) | Raster Command Reference §2.3.5 |

## Printable area widths at 360 dpi (TZe tape)

From Raster Command Reference §2.3.5 — *Number of print area pins* column
([ptouch-raster-command-reference.md](ptouch-raster-command-reference.md), PT-P900/P910BT
family, 360 dpi TZe table):

| Tape width (mm) | Left margin (pins) | **Print area (pins)** | Right margin (pins) | Bytes per raster line |
| --- | ---: | ---: | ---: | ---: |
| 3.5 | 248 | **48** | 264 | 70 |
| 6 | 240 | **64** | 256 | 70 |
| 9 | 219 | **106** | 235 | 70 |
| 12 | 197 | **150** | 213 | 70 |
| 18 | 155 | **234** | 171 | 70 |
| 24 | 112 | **320** | 128 | 70 |
| 36 | 45 | **454** | 61 | 70 |

**Printable pixel width** = *Print area (pins)* column. At 360 dpi, 1 pin = 1/360 inch
vertically and horizontally (360 dpi × 360 dpi mode).

## ESC/P media-width codes (reference only)

Raster Command Reference §4, table (3) — TZe *Media Width* byte values (hex):

| Tape width | Media width byte |
| --- | --- |
| 3.5 mm | `0x04` |
| 6 mm | `0x06` |
| 9 mm | `0x09` |
| 12 mm | `0x0C` |
| 18 mm | `0x12` |
| 24 mm | `0x18` |
| 36 mm | `0x24` |

Media length byte for TZe tape is fixed at `0x00` (continuous roll).

## Half-cut tape support

The PT-E920BT has a dual auto-cutter (full and half-cut). Half-cut perforates the
label layer while leaving the backing attached, which is used for multi-label strips.

| Requirement | Detail |
| --- | --- |
| Supported widths | All PT-E920BT widths (3.5–36 mm) when other conditions are met |
| Required media | **Laminated** TZe or HGe tape (`MediaType.LAMINATED`, status byte `0x01`) |
| Not supported | Non-laminated TZe (e.g. TZe-N series), fabric, heat-shrink, file tape, and other non-laminated types |

Brother documents that when non-laminated TZe is loaded and half-cut is requested,
the printer disables half-cut and uses auto-cut (full cut) instead:

- [Label feeding and cutting options (FAQ)](https://support.brother.com/g/b/faqend.aspx?c=hk&faqid=faqp00100033_000)
- [PT-E920BT specifications (media widths)](https://support.brother.com/g/s/es/htmldoc/ptouch/e720bt/uken/html/GUID-3EA582BC-2E97-4C09-BDB7-C03AA57ED33B_1.html)

This library raises `HalfCutNotSupportedError` when `half_cut=True` and the status
reply reports a non-laminated media type, rather than silently falling back to full cuts.

## Applicability note

Brother has not published a PT-E920BT-specific Raster Command Reference. The tables
above are taken from the PT-P900/P910BT manual because both families share the 560-pin /
360 dpi print head per the PT-E920BT User's Guide. The right-margin print-area pin
offset used by `pack_raster_lines()` has been verified on PT-E920BT hardware.
