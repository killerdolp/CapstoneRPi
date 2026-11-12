"""Minimal Code 128 (subset B) encoder.

Used to print each session ID as a scannable barcode, so a printed or
photographed label can be matched back to its record with a hand scanner.
"""

from __future__ import annotations

from typing import List

# Bar/space module widths for symbol values 0..106 (106 = stop).
_PATTERNS = (
    "212222 222122 222221 121223 121322 131222 122213 122312 132212 221213 "
    "221312 231212 112232 122132 122231 113222 123122 123221 223211 221132 "
    "221231 213212 223112 312131 311222 321122 321221 312212 322112 322211 "
    "212123 212321 232121 111323 131123 131321 112313 132113 132311 211313 "
    "231113 231311 112133 112331 132131 113123 113321 133121 313121 211331 "
    "231131 213113 213311 213131 311123 311321 331121 312113 312311 332111 "
    "314111 221411 431111 111224 111422 121124 121421 141122 141221 112214 "
    "112412 122114 122411 142112 142211 241211 221114 413111 241112 134111 "
    "111242 121142 121241 114212 124112 124211 411212 421112 421211 212141 "
    "214121 412121 111143 111341 131141 114113 114311 411113 411311 113141 "
    "114131 311141 411131 211412 211214 211232 2331112"
).split()

START_B = 104
STOP = 106
QUIET = 10  # modules of quiet zone on each side


def encode(text: str) -> List[int]:
    """Return alternating bar/space module widths (starting with a bar),
    including start, checksum and stop symbols. Quiet zones are not included."""
    values = []
    for ch in text:
        code = ord(ch)
        if not 32 <= code <= 126:
            raise ValueError(f"Code 128B cannot encode {ch!r}")
        values.append(code - 32)
    checksum = (START_B + sum((i + 1) * v for i, v in enumerate(values))) % 103
    symbols = [START_B, *values, checksum, STOP]
    widths: List[int] = []
    for sym in symbols:
        widths.extend(int(c) for c in _PATTERNS[sym])
    return widths


def total_modules(text: str) -> int:
    return sum(encode(text)) + 2 * QUIET
