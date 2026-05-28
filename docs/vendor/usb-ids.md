# USB identifiers — PT-E920BT

Canonical USB facts for the PT-E920BT. Resolve the product ID on live hardware in
issue [#4](https://github.com/exoma-ch/brother-printer/issues/4).

## Identifiers

| Field | Value | Source |
| --- | --- | --- |
| Vendor ID (USB) | `0x04F9` (Brother Industries, Ltd.) | Raster Command Reference, Appendix A — USB Specifications ([ptouch-raster-command-reference.md](ptouch-raster-command-reference.md), family doc) |
| Product ID (USB) | **TBD** — not published for PT-E920BT | Resolve via `lsusb` on connected hardware ([#4](https://github.com/exoma-ch/brother-printer/issues/4)) |
| USB version | USB 2.0 Full Speed | User's Guide, Appendix > Specifications > Interface ([pt-e920bt-user-guide.md](pt-e920bt-user-guide.md)) |
| Connector | USB Type-C | User's Guide, Appendix > Specifications > Interface |
| Device class | Printer (USB printer class) | Raster Command Reference, Appendix A (family PT-P900/P910BT; PT-E920BT assumed same class) |

### Reference PIDs (PT-P900 family — not PT-E920BT)

The published raster manual lists these **family** product IDs only:

| Model | Product ID |
| --- | --- |
| PT-P900 | `0x2083` |
| PT-P900W | `0x2085` |
| PT-P950NW | `0x2086` |
| PT-P910BT | `0x20C7` |

Do **not** assume the PT-E920BT shares any of these values.

## Interface descriptors (family reference)

From Raster Command Reference, Appendix A — USB Specifications (PT-P900/P910BT family).
Expected to match other Brother label printers; confirm on hardware in #4.

| Item | Value |
| --- | --- |
| USB spec | 1.1 |
| Device speed | Full speed |
| Interfaces | 1 (no alternate settings) |
| Class | Printer |
| Power | Self-powered (bus-power bit also set) |
| Manufacturer string | `"Brother"` (descriptor `0x01`, lang `0x0409`) |
| Serial string | `"000"` + last nine digits of printer serial (descriptor `0x03`, lang `0x0409`) |
| Endpoint 1 | **IN** bulk — printer → host status (max packet 64 bytes) |
| Endpoint 2 | **OUT** bulk — host → printer commands/data (max packet 64 bytes) |

## Discovery notes

```bash
# Example — replace xxxx with observed PID
lsusb -d 04f9:xxxx
```

Brother VID `04f9` is shared across the product line; always match on PID **and** product
string (`PT-E920BT`).
