"""Reproduce one reviewed GIF sample offline; never publish or update game content."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, __version__ as PILLOW_VERSION, features

TOOLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TOOLS))
from completion_gif import validate_file  # noqa: E402
from measure_completion_gif import verified  # noqa: E402

SIZE = (1128, 1350)
FRAME_COUNT = 75
FRAME_MS = 40
HISTORICAL_SAMPLE_MAX_BYTES = 1_000_000
PROFILES = {
    "A": {"width": 208, "colors": 255, "lossy": 40},
    "B": {"width": 256, "colors": 64, "lossy": None},
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_source(root: Path, descriptor: dict, records: list[dict]) -> Path:
    path = (root / descriptor["path"]).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Source object is outside the CDN directory")
    # Reuse the same immutable-object byte count and SHA256 check as the
    # original full-resolution measurement; never trust a path alone.
    verified(root, descriptor)
    records.append({key: descriptor[key] for key in ("path", "bytes", "sha256")})
    return path


def source_animation(catalogue: Path, level_id: int) -> tuple[dict, Path, list[dict], str]:
    raw = catalogue.read_bytes()
    catalogue_sha = sha256(raw)
    if catalogue.stem != catalogue_sha:
        raise ValueError("Catalogue filename must be its exact SHA256")
    catalog = json.loads(raw)
    if catalog.get("deliveryContract") != 2 or catalog.get("imagePolicy") != "composed-v1":
        raise ValueError("This offline recipe expects delivery contract 2 / composed-v1")
    root = catalogue.parent.parent.resolve()
    records = [{"path": "releases/" + catalogue.name, "bytes": len(raw), "sha256": catalogue_sha}]
    matches = [city["delivery"]["levels"][str(level_id)] for city in catalog["destinations"]
               if str(level_id) in city.get("delivery", {}).get("levels", {})]
    if len(matches) != 1:
        raise ValueError("Expected exactly one immutable level package")
    payload = json.loads(read_source(root, matches[0], records).read_bytes())
    levels = payload["levels"]
    if len(levels) != 1 or levels[0]["levelId"] != level_id:
        raise ValueError("Level package identity mismatch")
    animation = levels[0]["paintedAnimation"]
    if animation.get("version") != 1 or len(animation["parts"]) != 5:
        raise ValueError("Expected five version-1 painted animation parts")
    for part in animation["parts"]:
        axis, amplitude = part["axis"], part["amplitude"]
        if len(axis) != 2 or len(part["rect"]) != 4:
            raise ValueError("Invalid painted part geometry")
        if not (math.isfinite(amplitude) and 0 <= amplitude <= 4):
            raise ValueError("Painted part amplitude exceeds the PM's 4pt bound")
        if any(not math.isfinite(v) for v in axis) or math.hypot(*axis) > 1.000001:
            raise ValueError("Painted part axis exceeds a unit vector")
    return payload, root, records, catalogue_sha


def author_frames(payload: dict, root: Path, records: list[dict], width: int) -> list[Image.Image]:
    animation = payload["levels"][0]["paintedAnimation"]
    background_path = read_source(root, payload["assets"][animation["background"]], records)
    with Image.open(background_path) as source:
        background = source.convert("RGBA").resize(SIZE, Image.Resampling.LANCZOS)
    parts = []
    for part in animation["parts"]:
        path = read_source(root, payload["assets"][part["source"]], records)
        with Image.open(path) as source:
            cutout = source.convert("RGBA").resize(
                (round(part["rect"][2] * SIZE[0]), round(part["rect"][3] * SIZE[1])),
                Image.Resampling.LANCZOS)
        parts.append((part, cutout))
    size = (width, round(width * SIZE[1] / SIZE[0]))
    frames = []
    for index in range(FRAME_COUNT):
        phase = index / (FRAME_COUNT - 1)
        zoom = 1 + .05 * phase * phase * (3 - 2 * phase)
        image = background.copy()
        for part, cutout in parts:
            # At the 376×450 board size, three source pixels equal one point.
            # Divide the part offset by zoom to preserve its authored amplitude.
            dx = part["axis"][0] * part["amplitude"] * 3 * math.sin(phase * math.tau) / zoom
            dy = part["axis"][1] * part["amplitude"] * 3 * math.sin(phase * math.tau) / zoom
            image.alpha_composite(cutout, (round(part["rect"][0] * SIZE[0] + dx),
                                         round(part["rect"][1] * SIZE[1] + dy)))
        image = image.transform(
            SIZE, Image.Transform.AFFINE,
            (1 / zoom, 0, 564 * (1 - 1 / zoom), 0, 1 / zoom, 675 * (1 - 1 / zoom)),
            Image.Resampling.BICUBIC).convert("RGB")
        image.info.clear()
        frames.append(image.resize(size, Image.Resampling.LANCZOS))
    return frames


def encode(args: argparse.Namespace) -> dict:
    catalogue, optimizer, output = args.catalogue.resolve(), args.gifsicle.resolve(), args.output.resolve()
    metadata = output.with_suffix(output.suffix + ".json")
    if output.suffix.lower() != ".gif" or output.exists() or metadata.exists():
        raise ValueError("Choose a new .gif output path; existing files are never overwritten")
    version_text = subprocess.run([str(optimizer), "--version"], check=True,
                                  capture_output=True, text=True, timeout=15).stdout
    version = re.search(r"Gifsicle\s+(\d+\.\d+(?:\.\d+)?)", version_text)
    if not version or version.group(1) != "1.93":
        raise ValueError("The reviewed recipe requires explicit Gifsicle version 1.93")
    profile = PROFILES[args.profile]
    payload, root, records, catalogue_sha = source_animation(catalogue, args.level_id)
    frames = author_frames(payload, root, records, profile["width"])
    width, height = frames[0].size
    training = Image.new("RGB", (width * 5, height))
    for column, index in enumerate((0, 19, 37, 56, 74)):
        training.paste(frames[index], (column * width, 0))
    palette = training.quantize(colors=profile["colors"], method=Image.Quantize.MEDIANCUT)
    quantized = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    for frame in quantized:
        frame.info.clear()  # Do not inherit looping metadata from the source WebP.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="completion-gif-", dir=output.parent) as temporary:
        first, final = Path(temporary) / "palette.gif", Path(temporary) / "optimized.gif"
        quantized[0].save(first, save_all=True, append_images=quantized[1:], duration=FRAME_MS,
                          optimize=True, disposal=1, interlace=False, palette=palette.getpalette())
        options = ["-O3", "--no-interlace", "--no-loopcount"]
        if profile["lossy"] is not None:
            options.append("--lossy=" + str(profile["lossy"]))
        subprocess.run([str(optimizer), *options, str(first), "-o", str(final)],
                       check=True, capture_output=True, text=True, timeout=120)
        if final.stat().st_size > HISTORICAL_SAMPLE_MAX_BYTES:
            raise ValueError("Historical A/B sample exceeds its original 1,000,000-byte cap")
        # This enforces the strict 1,000,000-byte cap, global-palette subset,
        # every 40ms frame, no loops, and exact independent 75-frame decoding.
        result = validate_file(final)
        raw = final.read_bytes()
        comparison = None
        if args.compare_with:
            expected = validate_file(args.compare_with)
            if raw != args.compare_with.read_bytes() or result["frames"] != expected["frames"]:
                raise ValueError("The reproduced sample differs in bytes or decoded frames")
            comparison = {"sha256": expected["descriptor"]["sha256"],
                          "bytesIdentical": True, "all75FramesIdentical": True}
        report = dict(profile=args.profile, settings=profile, levelId=args.level_id,
                      catalogueSha256=catalogue_sha, verifiedSources=records,
                      authoring={"sourceCanvas": list(SIZE), "frameCount": FRAME_COUNT,
                                 "frameDelayMs": FRAME_MS, "durationMs": FRAME_COUNT * FRAME_MS,
                                 "zoom": [1.0, 1.05], "paintedParts": 5},
                      encoder={"pillow": PILLOW_VERSION, "libwebp": features.version("webp"),
                               "gifsicle": version.group(1), "gifsicleSha256": sha256(optimizer.read_bytes()),
                               "options": options, "palette": "global median cut", "dither": "none"},
                      comparison=comparison, conformance=result, published=False)
        # Exclusive creation protects review or production files from overwrite.
        with output.open("xb") as destination:
            destination.write(raw)
        with metadata.open("x", encoding="utf-8") as destination:
            json.dump(report, destination, indent=2)
            destination.write("\n")
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", required=True, type=Path,
                        help="Immutable SHA256-named JSON beneath a local CDN root/releases directory")
    parser.add_argument("--level-id", required=True, type=int)
    parser.add_argument("--gifsicle", required=True, type=Path, help="Explicit Gifsicle 1.93 executable")
    parser.add_argument("--profile", required=True, choices=PROFILES)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--compare-with", type=Path, help="Require identical bytes and all 75 decoded frames")
    args = parser.parse_args()
    try:
        result = encode(args)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(1, "Offline GIF sample rejected: " + str(error) + "\n")
    print(json.dumps({"output": str(args.output), "profile": args.profile,
                      "descriptor": result["conformance"]["descriptor"],
                      "metrics": result["conformance"]["metrics"],
                      "comparison": result["comparison"], "published": False}, indent=2))


if __name__ == "__main__":
    main()
