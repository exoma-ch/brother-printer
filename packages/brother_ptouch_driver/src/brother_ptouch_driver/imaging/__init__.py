"""Image-to-raster pipeline tuned for QR sharpness at 360 dpi.

See issue #6.
"""

from brother_ptouch_driver.imaging.errors import ImageScalingError, ImagingError
from brother_ptouch_driver.imaging.raster import (
    image_to_raster,
    pack_raster_lines,
    resize_to_tape_width,
    to_monochrome,
)

__all__ = [
    "ImageScalingError",
    "ImagingError",
    "image_to_raster",
    "pack_raster_lines",
    "resize_to_tape_width",
    "to_monochrome",
]
