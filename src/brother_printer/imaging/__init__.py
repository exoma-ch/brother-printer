"""Image-to-raster pipeline tuned for QR sharpness at 360 dpi.

See issue #6.
"""

from brother_printer.imaging.errors import ImageScalingError, ImagingError
from brother_printer.imaging.raster import (
    apply_margin,
    apply_rotation,
    image_to_raster,
    pack_raster_lines,
    resize_to_tape_width,
    to_monochrome,
)

__all__ = [
    "ImageScalingError",
    "ImagingError",
    "apply_margin",
    "apply_rotation",
    "image_to_raster",
    "pack_raster_lines",
    "resize_to_tape_width",
    "to_monochrome",
]
