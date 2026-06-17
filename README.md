# brother-printer

Open-source Python library and CLI for the Brother **PT-E920BT** label printer.
Print image labels (PNG and other images, such as QR codes or barcodes you
generate) and text labels over USB from the command line or from your own
Python code.

## Features

- **USB discovery and live status** — find connected PT-E920BT printers and read
  loaded tape width, media type, and error state
- **Image printing** — print PNG or other image files with tape-width safety checks,
  auto-cut, threshold control, and optional scaling
- **Text labels** — multi-line text with auto-fit font size, alignment, rotation,
  margins, and PNG preview without printing
- **Self-laminating tape** — auto-detected from printer status; printing is confined
  to the narrow white band (~9.8 mm) and centred there, keeping content off the clear
  laminate flap (text, PNG, and strips)
- **Multi-label strips** — chain multiple images into one strip with auto-cut or
  half-cut (laminated tape only)
- **CSV batch printing** — print a list of images from a CSV file as one strip
- **Tape reference** — list supported TZe widths and printable pixel dimensions

## Supported hardware

| Item | Details |
| --- | --- |
| Printer | Brother **PT-E920BT** (USB vendor `04f9`, product `224b`) |
| Tape | TZe / HGe / FLe cassettes, 3.5–36 mm |
| Platform | Linux with USB access (see [Linux USB setup](docs/install/linux-usb.md)) |

Other Brother models are not supported. Printable widths and pin counts are
documented in [docs/vendor/tze-tape-widths.md](docs/vendor/tze-tape-widths.md).

## Installation

### Prerequisites

The PT-E920BT is driven over USB. On Linux you need the system `libusb` library
plus a `udev` rule for non-root access. The [`setup-usb.sh`](packaging/scripts/setup-usb.sh)
script installs `libusb`, the `udev` rule, and adds you to the `plugdev` group — run
it directly from GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/exoma-ch/brother-printer/main/packaging/scripts/setup-usb.sh | bash
```

Unplug and replug the printer afterwards. For an explanation of what the script
does, devcontainer/rootless Podman setup, alternative rules, manual steps, and
troubleshooting, see [docs/install/linux-usb.md](docs/install/linux-usb.md).

### Install

Clone the repository and create a virtual environment with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/exoma-ch/brother-printer.git
cd brother-printer
uv sync --all-packages
```

This installs both workspace packages and their dependencies (`pyusb`, `Pillow`,
`click`) into `.venv`. Python 3.12+ is required.

Activate the venv to use the CLI directly:

```bash
source .venv/bin/activate
brother-ptouch-driver --help
brother-ptouch-label --help
```

Or run commands without activating:

```bash
uv run brother-ptouch-driver --help
uv run brother-ptouch-label --help
```

Or, if you have [just](https://just.systems) installed, use the bundled
recipes (each has a short alias):

```bash
just discover          # alias: just d    — list connected printers
just printer-status    # alias: just ps   — show live printer status
just tapes             # alias: just t    — list supported tape widths
just print qr.png --tape 12mm    # alias: just p    — print an image label
just label "Hello" --tape 12mm   # alias: just l    — print a text label
```

Run `just help` for the full list of recipes (testing, linting, and more).

With USB set up (see [Prerequisites](#prerequisites)) and the printer connected,
verify it is detected:

```bash
brother-ptouch-driver discover
```

## Quick start

Connect the PT-E920BT over USB, then (with the venv activated, or prefix
commands with `uv run`):

```bash
# Find connected printers
brother-ptouch-driver discover

# Show live status (loaded tape width, errors)
brother-ptouch-driver status

# List supported tape widths and pixel dimensions
brother-ptouch-driver info tapes

# Print a PNG on 12 mm tape (auto-cut by default)
brother-ptouch-driver print qr.png --tape 12mm

# Print without cutting
brother-ptouch-driver print qr.png --tape 12mm --no-cut

# Chain multiple images into one strip
brother-ptouch-driver print a.png b.png --tape 12mm --strip

# Batch-print images from a CSV file as one strip
brother-ptouch-driver print --csv labels.csv --tape 12mm

# Half-cut peelable labels (laminated tape only)
brother-ptouch-driver print qr.png --tape 12mm --half-cut

# Print a text label (tape auto-detected from printer status)
brother-ptouch-label "Hello, world!"

# Multi-line text with rotation across the tape
brother-ptouch-label "Line 1\nLine 2" --rotate --tape 24mm

# Self-laminating tape is auto-detected: text is confined to the white band
brother-ptouch-label "Cable-01"

# Render a label to PNG without printing
brother-ptouch-label "Preview" -o label.png --tape 12mm
```

Image height must match the loaded tape print area (see `brother-ptouch-driver
info tapes`) unless you pass `--scale`. Text layout, rotation, and margins are
handled by `brother-ptouch-label`.

## Library usage

```python
from PIL import Image

from brother_ptouch_driver import (
    TapeWidth,
    discover_printers,
    print_image,
    query_status,
)

printers = discover_printers()
printer = printers[0]
status = query_status(printer)
print(f"Loaded tape: {status.media_width.mm:g} mm")

with Image.open("qr.png") as image:
    print_image(image, TapeWidth.MM_12, auto_cut=True)
```

Text rendering and printing are available from `brother_ptouch_label`:

```python
from brother_ptouch_label import render_text, print_text
from brother_ptouch_driver import TapeWidth

image = render_text("Hello", TapeWidth.MM_12)
print_text("Hello", TapeWidth.MM_12)
```

## Packages

| Package | CLI | Role |
| --- | --- | --- |
| `brother-ptouch-driver` | `brother-ptouch-driver` | USB transport, raster protocol, image printing |
| `brother-ptouch-label` | `brother-ptouch-label` | Text-to-label rendering and printing |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and
contribution guidelines.

## License

[MIT](LICENSE)
