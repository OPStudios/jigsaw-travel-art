"""Offline conformance gate for authored, play-once completion GIFs.

This game-owned validator does not publish content or change the still-image
policy. A bounded structural/LZW reader checks the runtime's supported subset;
Pillow independently decodes every composited frame for an exact pixel check.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, UnidentifiedImageError

POLICY = "completion-gif-v1"
MAX_BYTES = 5_000_000
MAX_AXIS = 2048
MAX_PIXELS = 2_097_152
MAX_INDEX_BYTES = 64 * 1024 * 1024
MAX_COMPRESSED_FRAME_BYTES = 1024 * 1024
MAX_DICTIONARY_BYTES = 1024 * 1024
FRAME_COUNT = 75
FRAME_DELAY_MS = 40
DURATION_MS = 3000


def budget_bytes(width: int, height: int, encoded_bytes: int) -> int:
    """Shared runtime peak: indexed snapshots/canvas/GPU, palettes and scratch."""
    return 79 * width * height + 1536 + encoded_bytes + 2_359_296 + 75 * 96


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class _Reader:
    def __init__(self, raw: bytes):
        self.raw, self.position = raw, 0

    def take(self, size: int) -> bytes:
        if size < 0 or size > len(self.raw) - self.position:
            raise ValueError("Truncated GIF structure")
        start = self.position
        self.position += size
        return self.raw[start:self.position]

    def byte(self) -> int:
        return self.take(1)[0]

    def word(self) -> int:
        return int.from_bytes(self.take(2), "little")

    def blocks(self, limit: int | None = None, discard: bool = False) -> bytes:
        result = bytearray()
        total = 0
        while (size := self.byte()) != 0:
            total += size
            if limit is not None and total > limit:
                raise ValueError("GIF compressed frame exceeds budget")
            chunk = self.take(size)
            if not discard:
                result.extend(chunk)
        return bytes(result)


def _indices(raw: bytes, minimum: int, expected: int) -> bytes:
    """Decode only one bounded index rectangle; require clear/end/pixel count."""
    if not 2 <= minimum <= 8:
        raise ValueError("Unsupported GIF LZW minimum code size")
    clear, end = 1 << minimum, (1 << minimum) + 1
    table: list[bytes | None] = []
    width, position, previous = minimum + 1, 0, None
    output = bytearray()
    dictionary_bytes = 0
    first = True
    while True:
        if position + width > len(raw) * 8:
            raise ValueError("Truncated GIF LZW stream or missing end code")
        at, shift = divmod(position, 8)
        code = (int.from_bytes(raw[at:at + 3], "little") >> shift) & ((1 << width) - 1)
        position += width
        if first and code != clear:
            raise ValueError("GIF LZW stream must start with a clear code")
        first = False
        if code == clear:
            table = [bytes((n,)) for n in range(clear)] + [None, None]
            dictionary_bytes = clear
            width, previous = minimum + 1, None
            continue
        if code == end:
            if len(output) != expected:
                raise ValueError("GIF LZW decoded pixel count mismatch")
            remaining = len(raw) * 8 - position
            if remaining > 7 or (remaining and (raw[-1] >> (8 - remaining)) != 0):
                raise ValueError("GIF LZW has nonzero padding or extra compressed bytes")
            return bytes(output)
        if code < len(table) and table[code] is not None:
            entry = table[code]
        elif code == len(table) and previous is not None and len(table) < 4096:
            entry = previous + previous[:1]
        else:
            raise ValueError("Invalid GIF LZW dictionary reference")
        if len(entry) > expected - len(output):
            raise ValueError("GIF LZW decoded pixel count exceeds rectangle")
        output.extend(entry)
        if previous is not None and len(table) < 4096:
            dictionary_bytes += len(previous) + 1
            if dictionary_bytes > MAX_DICTIONARY_BYTES:
                raise ValueError("GIF LZW dictionary payload exceeds budget")
            table.append(previous + entry[:1])
            if len(table) == (1 << width) and width < 12:
                width += 1
        previous = entry


def _structure(raw: bytes) -> dict:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("GIF must contain 1 to 5,000,000 bytes")
    reader = _Reader(raw)
    if reader.take(6) != b"GIF89a":
        raise ValueError("Completion requires GIF89a")
    width, height = reader.word(), reader.word()
    if not 1 <= width <= MAX_AXIS or not 1 <= height <= MAX_AXIS or width * height > MAX_PIXELS:
        raise ValueError("GIF canvas exceeds dimension budget")
    if width * height * FRAME_COUNT > MAX_INDEX_BYTES:
        raise ValueError("GIF indexed snapshot budget exceeded")
    flags, background, aspect = reader.byte(), reader.byte(), reader.byte()
    if not flags & 0x80:
        raise ValueError("GIF global palette is required")
    entries = 1 << ((flags & 7) + 1)
    if background >= entries or aspect != 0:
        raise ValueError("Invalid GIF background index or pixel aspect")
    palette = reader.take(entries * 3)
    frames, control, delta_bytes = [], None, 0
    while True:
        marker = reader.byte()
        if marker == 0x3B:
            if reader.position != len(raw) or control is not None:
                raise ValueError("GIF trailing data or unconsumed frame control")
            break
        if marker == 0x21:
            extension = reader.byte()
            if extension == 0xFE:
                reader.blocks(discard=True)  # Comments are inert; application/loop blocks are not.
                continue
            if extension != 0xF9:
                raise ValueError("GIF application, loop, plain-text or unknown extension is unsupported")
            if control is not None or reader.byte() != 4:
                raise ValueError("Invalid or duplicate GIF frame control")
            packed, delay, transparent = reader.byte(), reader.word(), reader.byte()
            if reader.byte() != 0 or packed & 0xE2 or ((packed >> 2) & 7) != 1:
                raise ValueError("GIF requires disposal 1 and no user input or reserved control bits")
            if delay * 10 != FRAME_DELAY_MS:
                raise ValueError("Completion frame delay must be 40ms")
            control = (delay * 10, transparent if packed & 1 else None)
            continue
        if marker != 0x2C or control is None:
            raise ValueError("GIF image must have exactly one frame control")
        x, y, frame_width, frame_height = (reader.word() for _ in range(4))
        if (not frame_width or not frame_height or x + frame_width > width or y + frame_height > height):
            raise ValueError("GIF frame rectangle escapes the canvas")
        if reader.byte() != 0:
            raise ValueError("GIF local palettes, interlace and reserved image flags are unsupported")
        if not frames and (x or y or frame_width != width or frame_height != height or control[1] is not None):
            raise ValueError("GIF first frame must be opaque and cover the canvas")
        minimum, encoded = reader.byte(), reader.blocks(limit=MAX_COMPRESSED_FRAME_BYTES)
        if not 2 <= minimum <= 8:
            raise ValueError("Unsupported GIF LZW minimum code size")
        if control[1] is not None and control[1] >= (1 << minimum):
            raise ValueError("GIF transparent sentinel is not an LZW literal")
        delta_bytes += frame_width * frame_height
        if delta_bytes > MAX_INDEX_BYTES:
            raise ValueError("GIF decoded delta budget exceeded")
        frames.append(dict(rect=(x, y, frame_width, frame_height), delay=control[0],
                           transparent=control[1], minimum=minimum, encoded=encoded))
        control = None
        if len(frames) > FRAME_COUNT:
            raise ValueError("Completion must contain exactly 75 frames")
    if len(frames) != FRAME_COUNT or sum(frame["delay"] for frame in frames) != DURATION_MS:
        raise ValueError("Completion must contain exactly 75 frames and last 3000ms")
    return dict(width=width, height=height, palette=palette, entries=entries,
                frames=frames, delta_bytes=delta_bytes)


def validate(raw: bytes) -> dict:
    """Return a content-addressed descriptor and independently verified metrics."""
    parsed = _structure(raw)
    width, height = parsed["width"], parsed["height"]
    canvas = bytearray(width * height * 4)
    indexed = bytearray(width * height)
    colours = [parsed["palette"][n * 3:n * 3 + 3] + b"\xff" for n in range(parsed["entries"])]
    records = []
    try:
        with Image.open(io.BytesIO(raw)) as decoded:
            if decoded.format != "GIF" or decoded.size != (width, height) or decoded.n_frames != FRAME_COUNT or "loop" in decoded.info:
                raise ValueError("Independent GIF metadata disagrees")
            for index, frame in enumerate(parsed["frames"]):
                x, y, frame_width, frame_height = frame["rect"]
                pixels = _indices(frame["encoded"], frame["minimum"], frame_width * frame_height)
                for offset, colour in enumerate(pixels):
                    if colour == frame["transparent"]:
                        continue  # Sentinel can be outside the global palette, never rendered.
                    if colour >= len(colours):
                        raise ValueError("GIF visible palette index is out of range")
                    at = ((y + offset // frame_width) * width + x + offset % frame_width) * 4
                    canvas[at:at + 4] = colours[colour]
                    indexed[at // 4] = colour
                decoded.seek(index)
                independent = decoded.convert("RGBA")
                if decoded.info.get("duration") != FRAME_DELAY_MS or independent.tobytes() != canvas:
                    raise ValueError("Independent GIF frame decoding disagrees at frame %d" % index)
                records.append(dict(index=index, rect=list(frame["rect"]), delayMs=frame["delay"],
                                    transparentIndex=frame["transparent"], rgbaSha256=digest(canvas),
                                    indexedSha256=digest(indexed)))
    except (UnidentifiedImageError, OSError, EOFError, SyntaxError, IndexError) as error:
        raise ValueError("Independent GIF decoder rejected the file") from error
    sha = digest(raw)
    return dict(policy=POLICY, descriptor=dict(path="objects/" + sha + ".gif", sha256=sha,
                bytes=len(raw), mediaType="image/gif", width=width, height=height),
                metrics=dict(frameCount=FRAME_COUNT, frameDelayMs=FRAME_DELAY_MS,
                durationMs=DURATION_MS, playCount=1, paletteEntries=parsed["entries"],
                decodedDeltaIndexBytes=parsed["delta_bytes"],
                indexedSnapshotBytes=width * height * FRAME_COUNT, rgbaFrameBytes=width * height * 4,
                uniqueFrameCount=len({row["rgbaSha256"] for row in records}),
                peakMemoryBytes=budget_bytes(width, height, len(raw))),
                paletteSha256=digest(parsed["palette"]),
                indexedFrameHashes=[row["indexedSha256"] for row in records], frames=records)


def validate_file(path: Path | str) -> dict:
    # Bound the read even if a file grows between stat and read.
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return validate(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gif", type=Path)
    args = parser.parse_args()
    try:
        result = validate_file(args.gif)
    except (ValueError, OSError) as error:
        parser.exit(1, "Completion GIF rejected: " + str(error) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
