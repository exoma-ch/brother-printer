"""Imaging-layer exceptions."""


class ImagingError(Exception):
    """Base exception for imaging failures."""


class ImageScalingError(ImagingError):
    """Image cannot be scaled to tape width without distorting QR modules."""
