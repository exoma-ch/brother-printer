# brother-printer

Python library and CLI for the Brother PT-E920BT label printer.

## Workspace layout

```
pyproject.toml                    # uv workspace root (dev deps, pytest config)
packages/
  brother_printer/                # core driver + brother-printer CLI
  brother_printer_text/           # text rendering + brother-label-text CLI
```

## Packages

| Package | CLI | Role |
| --- | --- | --- |
| `brother_printer` | `brother-printer` | USB driver, raster protocol, image printing (`print_image`, `print_png`) |
| `brother_printer_text` | `brother-label-text` | Text-to-label rendering (`render_text`, `print_text`) |

Install everything from the repo root:

```bash
uv sync --all-packages
```

Image height must match the loaded tape width (see `brother-printer info tapes`) unless you
pass `--scale` on print or `scale=True` in the library. Text labels use the separate
`brother-label-text` tool.

Architecture: [docs/adr/0003-driver-text-decoupling.md](docs/adr/0003-driver-text-decoupling.md).

## Testing

See [TESTING.md](TESTING.md) for how to run unit and hardware tests, the hardware print
matrix, and tape prerequisites.
