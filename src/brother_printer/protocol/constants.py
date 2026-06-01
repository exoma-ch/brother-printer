"""P-touch raster protocol constants.

See docs/vendor/ptouch-raster-command-reference.md and docs/vendor/tze-tape-widths.md.
"""

# Command opcodes (fixed prefixes; parameters appended by encoder)
CMD_INITIALIZE = b"\x1b\x40"
CMD_STATUS_REQUEST = b"\x1b\x69\x53"
CMD_SWITCH_RASTER = b"\x1b\x69\x61\x01"
CMD_PRINT_INFO = b"\x1b\x69\x7a"
CMD_MODE = b"\x1b\x69\x4d"
CMD_ADVANCED_MODE = b"\x1b\x69\x4b"
CMD_MARGIN = b"\x1b\x69\x64"
CMD_COMPRESSION = b"\x4d"
CMD_RASTER = b"\x47"
CMD_ZERO_RASTER = b"\x5a"
CMD_PRINT = b"\x0c"
CMD_EJECT = b"\x1a"

CMD_INVALIDATE_COUNT = 200

# Print information valid flags
PI_KIND = 0x02
PI_WIDTH = 0x04

# Mode settings bit masks
MODE_AUTO_CUT = 0x40
MODE_MIRROR = 0x80

# Advanced mode bit masks
ADV_HALF_CUT = 0x04
ADV_NO_CHAIN = 0x08

# Raster line payload (560 pins / 8)
RASTER_LINE_BYTES = 70
HEAD_PINS = RASTER_LINE_BYTES * 8

# 32-byte status reply layout
STATUS_REPLY_SIZE = 32
# Bulk IN max packet size (docs/vendor/usb-ids.md); read this many bytes over USB
STATUS_USB_READ_SIZE = 64
STATUS_HEADER_MARK = 0x80
STATUS_SIZE_BYTE = 0x20
STATUS_OFFSET_ERROR1 = 8
STATUS_OFFSET_ERROR2 = 9
STATUS_OFFSET_MEDIA_WIDTH = 10
STATUS_OFFSET_MEDIA_TYPE = 11
STATUS_OFFSET_STATUS_TYPE = 18
STATUS_OFFSET_PHASE_TYPE = 19
STATUS_OFFSET_PHASE_HI = 20
STATUS_OFFSET_PHASE_LO = 21
STATUS_OFFSET_NOTIFICATION = 22
STATUS_OFFSET_TAPE_COLOR = 24
