"""Offline level-1 natural-action GIF preview using its verified painted artwork."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, __version__ as PILLOW_VERSION, features

from encode_sample import SIZE, read_source, source_animation
from completion_gif import validate_file
from delivery_variants import composition_descriptor

MAX_BYTES = 5_000_000
EXPECTED_SUBJECTS = ["tea-steam", "lemon-thyme-branch", "daisy-stem", "garden-butterfly", "mint-garnish"]
MOTIONS = [
    {"subject": "tea-steam", "action": "curl upward and dissipate while a fresh wisp grows from the cup", "anchor": "cup rim", "maximumTravelPt": 4},
    {"subject": "lemon-thyme-branch", "action": "leaf-bearing branch flexes in a breeze, rooted stem stays fixed", "anchor": "bottom stem", "maximumTipBendPt": 3},
    {"subject": "daisy-stem", "action": "flower head nods on its flexible stem, vase attachment stays fixed", "anchor": "bottom stem", "maximumTipBendPt": 4},
    {"subject": "garden-butterfly", "action": "left and right wings fold about the body during a curved hover and return", "anchor": "body axis", "maximumTravelPt": 4},
    {"subject": "mint-garnish", "action": "three leaf tips flex with different phases around their shared fixed join", "anchor": "central leaf join", "maximumTipBendPt": 2.5},
]


def smooth(value: float) -> float:
    value = max(0., min(1., value))
    return value * value * (3 - 2 * value)


def fade(image: Image.Image, alpha: float) -> Image.Image:
    result = image.copy()
    result.putalpha(result.getchannel("A").point(lambda v: round(v * max(0., min(1., alpha)))))
    return result


def deform(image: Image.Image, inverse, cell: int = 12) -> Image.Image:
    """Resample painted pixels through a fine mesh; never draw substitute art."""
    width, height = image.size
    mesh = []
    for top in range(0, height, cell):
        bottom = min(top + cell, height)
        for left in range(0, width, cell):
            right = min(left + cell, width)
            quad = []
            for x, y in ((left, top), (left, bottom), (right, bottom), (right, top)):
                quad.extend(inverse(x, y))
            mesh.append(((left, top, right, bottom), tuple(quad)))
    return image.transform(image.size, Image.Transform.MESH, mesh, Image.Resampling.BICUBIC)


def painted_action(cutout: Image.Image, index: int, phase: float) -> tuple[Image.Image, tuple[int, int]]:
    """Each action preserves source pixels/alpha and returns to the original pose."""
    pad = 28
    width, height = cutout.size
    image = Image.new("RGBA", (width + pad * 2, height + pad * 2))
    image.alpha_composite(cutout, (pad, pad))
    if phase <= 0 or phase >= 1:
        return image, (-pad, -pad)
    envelope = math.sin(math.pi * phase) ** 2
    if index == 0:
        # One painted wisp rises and thins; a new one forms at the rooted cup rim.
        first_progress = smooth(phase / .78)
        rise = 12 * first_progress
        def steam_warp(x, y):
            free = max(0., min(1., (pad + height - y) / height))
            curl = 7 * envelope * free * math.sin(2 * math.pi * (phase + free * .7))
            return x - curl, y + rise * free
        old = fade(deform(image, steam_warp), 1 - smooth((phase - .18) / .62))
        new_opacity = smooth((phase - .30) / .68)
        growth = .72 + .28 * smooth((phase - .25) / .75)
        base = pad + height
        fresh = image.transform(image.size, Image.Transform.AFFINE,
                                (1, 0, 0, 0, 1 / growth, base * (1 - 1 / growth)),
                                Image.Resampling.BICUBIC)
        old.alpha_composite(fade(fresh, new_opacity))
        return old, (-pad, -pad)
    if index in (1, 2):
        maximum = 9 if index == 1 else 12
        wave = math.sin(2 * math.pi * phase + (.35 if index == 1 else -.25))
        bend = maximum * envelope * wave
        def stem_warp(x, y):
            free = max(0., min(1., (pad + height - y) / height))
            # Quadratic flexibility concentrates motion in leaves/head and
            # produces zero displacement/zero slope at the fixed stem base.
            shift = bend * free * free
            droop = abs(bend) * .18 * free ** 3
            return x - shift, y - droop
        return deform(image, stem_warp), (-pad, -pad)
    if index == 3:
        joint = (pad + width * .49, pad + height * .65)
        ax, ay = .371390676, -.928476691
        px, py = -ay, ax
        flutter = (.5 - .5 * math.cos(16 * math.pi * phase)) * envelope
        left_scale, right_scale = 1 - .58 * flutter, 1 - .42 * flutter
        body_radius = width * .035
        def wings(x, y):
            dx, dy = x - joint[0], y - joint[1]
            along, across = dx * ax + dy * ay, dx * px + dy * py
            if abs(across) > body_radius:
                scale = left_scale if across < 0 else right_scale
                across = math.copysign(body_radius + (abs(across) - body_radius) / scale, across)
            return joint[0] + along * ax + across * px, joint[1] + along * ay + across * py
        flapping = deform(image, wings, cell=5)
        dx = round(7 * math.sin(2 * math.pi * phase) * math.sin(math.pi * phase))
        dy = round(-10 * envelope)
        return flapping, (-pad + dx, -pad + dy)
    # The mint's three tips flex separately; the central leaf join stays fixed.
    joint = (pad + width * .50, pad + height * .54)
    radius = max(width, height) * .52
    def mint_warp(x, y):
        dx, dy = x - joint[0], y - joint[1]
        distance = math.hypot(dx, dy)
        free = min(1., distance / radius) ** 2
        angle = math.atan2(dy, dx)
        bend = 7.5 * envelope * math.sin(4 * math.pi * phase + angle * 2) * free
        return x + math.sin(angle) * bend, y - math.cos(angle) * bend
    return deform(image, mint_warp, cell=8), (-pad, -pad)


def render(args):
    optimizer = args.gifsicle.resolve()
    version_text = subprocess.run([str(optimizer), "--version"], check=True,
                                  capture_output=True, text=True, timeout=15).stdout
    version = re.search(r"Gifsicle\s+(\d+\.\d+(?:\.\d+)?)", version_text)
    if not version or version.group(1) != "1.93":
        raise ValueError("This reproducible preview requires explicit Gifsicle 1.93")
    payload, root, records, catalogue_sha = source_animation(args.catalogue.resolve(), 1)
    spec_bytes = args.authoring.read_bytes()
    spec = json.loads(spec_bytes)
    if spec["levelId"] != 1 or [p["subject"] for p in spec["parts"]] != EXPECTED_SUBJECTS:
        raise ValueError("This natural-action preview is authored only for the inspected level-1 parts")
    animation = payload["levels"][0]["paintedAnimation"]
    source_image = payload["assets"][payload["levels"][0]["image"]]
    if source_image != composition_descriptor(payload["levels"][0], payload["assets"], source_image):
        raise ValueError("Source still composition identity mismatch")
    art_root = args.authoring.resolve().parent.parent
    authoring_sources = []
    for actual, authored in zip(animation["parts"], spec["parts"]):
        if authored["sha256"][:12] not in actual["source"] or actual["rect"] != authored["rect"]:
            raise ValueError("Semantic authoring metadata does not identify this painted source")
        art_path = (art_root / authored["source"]).resolve()
        if not art_path.is_relative_to(art_root) or hashlib.sha256(art_path.read_bytes()).hexdigest() != authored["sha256"]:
            raise ValueError("Semantic authoring source identity mismatch")
        authoring_sources.append({"source": authored["source"], "sha256": authored["sha256"]})
    with Image.open(read_source(root, payload["assets"][animation["background"]], records)) as source:
        background = source.convert("RGBA").resize(SIZE, Image.Resampling.LANCZOS)
    parts = []
    for part in animation["parts"]:
        with Image.open(read_source(root, payload["assets"][part["source"]], records)) as source:
            cutout = source.convert("RGBA").resize((round(part["rect"][2] * SIZE[0]),
                                                   round(part["rect"][3] * SIZE[1])), Image.Resampling.LANCZOS)
        parts.append((part, cutout))
    size = (args.width, round(args.width * SIZE[1] / SIZE[0]))
    frames = []
    motion_proof = [[] for _ in parts]
    for index in range(75):
        phase = index / 74
        zoom = 1 + .05 * smooth(phase)
        image = background.copy()
        for part_index, (part, cutout) in enumerate(parts):
            animated, offset = painted_action(cutout, part_index, phase)
            motion_proof[part_index].append(hashlib.sha256(animated.tobytes()).hexdigest())
            image.alpha_composite(animated, (round(part["rect"][0] * SIZE[0]) + offset[0],
                                            round(part["rect"][1] * SIZE[1]) + offset[1]))
        image = image.transform(SIZE, Image.Transform.AFFINE,
                                (1 / zoom, 0, 564 * (1 - 1 / zoom), 0, 1 / zoom, 675 * (1 - 1 / zoom)),
                                Image.Resampling.BICUBIC).convert("RGB")
        image.info.clear()
        frames.append(image.resize(size, Image.Resampling.LANCZOS))
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    for n, label in ((0, "start"), (19, "motion"), (37, "middle"), (56, "return"), (74, "end")):
        frames[n].save(output.with_name(output.stem + "-reference-" + label + ".png"))
    training = Image.new("RGB", (size[0] * 5, size[1]))
    for column, frame in enumerate((0, 19, 37, 56, 74)):
        training.paste(frames[frame], (column * size[0], 0))
    palette = training.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    quantized = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    for frame in quantized:
        frame.info.clear()
    with tempfile.TemporaryDirectory(prefix="natural-scene-", dir=output.parent) as temp:
        unoptimized, optimized = Path(temp) / "source.gif", Path(temp) / "optimized.gif"
        quantized[0].save(unoptimized, save_all=True, append_images=quantized[1:], duration=40,
                          disposal=1, optimize=True, interlace=False, palette=palette.getpalette())
        options = ["-O3", "--no-interlace", "--no-loopcount"]
        if args.lossy:
            options.append("--lossy=" + str(args.lossy))
        subprocess.run([str(optimizer), *options, str(unoptimized), "-o", str(optimized)], check=True, timeout=120)
        if optimized.stat().st_size > MAX_BYTES:
            raise ValueError(f"Candidate is {optimized.stat().st_size} bytes; cap is {MAX_BYTES}")
        result = validate_file(optimized)
        output.write_bytes(optimized.read_bytes())
    for i, motion in enumerate(MOTIONS):
        motion["uniqueDeformedPoses"] = len(set(motion_proof[i]))
        motion["finalPoseMatchesStart"] = motion_proof[i][0] == motion_proof[i][-1]
    report = dict(levelId=1, motionRecipe="level001-natural-v1", capBytes=MAX_BYTES, catalogueSha256=catalogue_sha,
                  semanticAuthoringSha256=hashlib.sha256(spec_bytes).hexdigest(),
                  verifiedSources=records, verifiedAuthoringSources=authoring_sources,
                  actions=MOTIONS, originalResolution=list(SIZE),
                  profile={"width": size[0], "height": size[1], "colors": 255,
                           "dither": "none", "lossy": args.lossy, "pillow": PILLOW_VERSION,
                           "libwebp": features.version("webp"), "gifsicle": version.group(1),
                           "gifsicleSha256": hashlib.sha256(optimizer.read_bytes()).hexdigest(),
                           "options": options},
                  conformance=result, published=False)
    output.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    receipt = {"schemaVersion": 1, "sourceCatalogueSha256": catalogue_sha,
               "levels": {"1": {"levelId": 1, "path": output.name,
                                   "gifSha256": result["descriptor"]["sha256"],
                                   "sourceImageSha256": source_image["sha256"]}}}
    output.with_suffix(".index.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"output": str(output), "bytes": output.stat().st_size,
                      "dimensions": size, "actions": MOTIONS, "frames": result["metrics"]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", required=True, type=Path)
    parser.add_argument("--authoring", required=True, type=Path)
    parser.add_argument("--gifsicle", required=True, type=Path)
    parser.add_argument("--width", type=int, choices=(376, 512), default=376)
    parser.add_argument("--lossy", type=int, default=0)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output path; existing GIFs are not overwritten")
    if not 0 <= args.lossy <= 1000:
        parser.error("Lossy comparison setting must be between 0 and 1000")
    render(args)


if __name__ == "__main__":
    main()
