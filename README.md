# brother-printer

Python library and CLI for the Brother PT-E920BT label printer.

## Workspace layout

```
pyproject.toml                    # uv workspace root (dev deps, pytest config)
packages/
  brother_ptouch_driver/          # P-touch driver + brother-ptouch-driver CLI
  brother_ptouch_label/           # text rendering + brother-ptouch-label CLI
```

## Packages

| Package | CLI | Role |
| --- | --- | --- |
| `brother-ptouch-driver` | `brother-ptouch-driver` | USB driver, raster protocol, image printing (`print_image`, `print_png`) |
| `brother-ptouch-label` | `brother-ptouch-label` | Text-to-label rendering (`render_text`, `print_text`) |

Install everything from the repo root:

```bash
uv sync --all-packages
```

Image height must match the loaded tape width (see `brother-ptouch-driver info tapes`) unless you
pass `--scale` on print or `scale=True` in the library. Text labels use the separate
`brother-ptouch-label` tool:

```bash
brother-ptouch-label "Hello" --tape 24mm          # print
brother-ptouch-label "Hi\nThere" -o label.png     # render PNG (--tape optional)
brother-ptouch-label "Label" --rotate --width 400 # 90° across tape, fixed width
```

Architecture: [docs/adr/0003-driver-text-decoupling.md](docs/adr/0003-driver-text-decoupling.md).

## Testing

See [TESTING.md](TESTING.md) for how to run unit and hardware tests, the hardware print
matrix, and tape prerequisites.
