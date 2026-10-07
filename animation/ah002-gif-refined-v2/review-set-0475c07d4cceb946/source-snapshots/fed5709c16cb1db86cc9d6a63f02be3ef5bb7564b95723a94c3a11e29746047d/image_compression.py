"""Measured delivery encodings; source artwork and gameplay are never rewritten.

The quality gates are regression limits, not a claim of perceptual equivalence.
Alpha/cutouts remain exact. Large opaque art may use WebP after independent decode
checks. Keep this policy version immutable when validating retained catalogues.
"""
import io
import math

import numpy as np
from PIL import Image, ImageFilter

POLICY = "composed-v1"
QUALITIES = (90, 94, 97)
MIN_LOSSY_PIXELS = 256 * 256
MIN_PSNR = 36.0
MIN_SSIM = 0.985
MIN_SSIM_P05 = 0.95
MIN_TILE_PSNR = 25.0
MAX_P99_ERROR = 24.0
MAX_PUZZLE_BYTES = 4 * 1024 * 1024
MAX_READY_BYTES = 8 * 1024 * 1024  # Includes a city's shared presentation artwork.
MAX_AVERAGE_BYTES = 2 * 1024 * 1024


def decode(raw):
    with Image.open(io.BytesIO(raw)) as image:
        if image.format not in ("PNG", "WEBP") or image.n_frames != 1:
            raise ValueError("Unsupported delivery image format")
        if not all(0 < n <= 4096 for n in image.size):
            raise ValueError("Image dimensions outside decode budget")
        image.load()
        return image.convert("RGBA")


def psnr(mse):
    return 100.0 if mse == 0 else float(10 * math.log10(255 ** 2 / mse))


def quality(original, decoded):
    """Full resolution RGB error + non-overlapping 8x8 luma SSIM (population).

    Edge padding includes every pixel, including partial blocks. Worst 32x32 RGB
    error catches localized damage which a whole-image average could conceal.
    """
    a, b = original.convert("RGBA"), decoded.convert("RGBA")
    if a.size != b.size:
        raise ValueError("Image geometry changed")
    if a.getchannel("A").tobytes() != b.getchannel("A").tobytes():
        raise ValueError("Image alpha changed")
    if a.tobytes() == b.tobytes():
        return dict(exact=True, psnr=100.0, ssim=1.0, ssim_p05=1.0,
                    tile_psnr=100.0, p99_error=0.0)
    x, y = np.asarray(a, dtype=np.float32)[:, :, :3], np.asarray(b, dtype=np.float32)[:, :, :3]
    error = x - y
    squared = np.mean(error * error, axis=2)
    h, w = squared.shape
    padded = np.pad(squared, ((0, -h % 32), (0, -w % 32)), mode="edge")
    tiles = padded.reshape(padded.shape[0] // 32, 32, padded.shape[1] // 32, 32).mean(axis=(1, 3))
    def blocks(rgb):
        luma = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        luma = np.pad(luma, ((0, -h % 8), (0, -w % 8)), mode="edge")
        return luma.reshape(luma.shape[0] // 8, 8, luma.shape[1] // 8, 8).transpose(0, 2, 1, 3).reshape(-1, 64)
    u, v = blocks(x), blocks(y)
    mu, mv = u.mean(1), v.mean(1)
    du, dv = u - mu[:, None], v - mv[:, None]
    vu, vv, covariance = (du * du).mean(1), (dv * dv).mean(1), (du * dv).mean(1)
    scores = ((2 * mu * mv + 6.5025) * (2 * covariance + 58.5225) /
              ((mu * mu + mv * mv + 6.5025) * (vu + vv + 58.5225)))
    return dict(exact=False, psnr=psnr(float(squared.mean())), ssim=float(scores.mean()),
                ssim_p05=float(np.percentile(scores, 5)), tile_psnr=psnr(float(tiles.max())),
                p99_error=float(np.percentile(np.max(np.abs(error), axis=2), 99)))


def acceptable(metrics):
    return (metrics["psnr"] >= MIN_PSNR and metrics["ssim"] >= MIN_SSIM
            and metrics["ssim_p05"] >= MIN_SSIM_P05
            and metrics["tile_psnr"] >= MIN_TILE_PSNR and metrics["p99_error"] <= MAX_P99_ERROR)


def encode(original, *, lossless, quality_value=100):
    output = io.BytesIO()
    original.save(output, format="WEBP", lossless=lossless, quality=quality_value, method=6, exact=True)
    return output.getvalue()


def compress(raw, *, protected=False):
    original = decode(raw)
    opaque = original.getchannel("A").getextrema() == (255, 255)
    if not protected and opaque and original.width * original.height >= MIN_LOSSY_PIXELS:
        for value in QUALITIES:
            candidate = encode(original, lossless=False, quality_value=value)
            metrics = quality(original, decode(candidate))
            if len(candidate) < len(raw) and acceptable(metrics):
                return candidate, "webp", dict(mode="lossy", quality=value, **metrics)
    candidate = encode(original, lossless=True)
    metrics = quality(original, decode(candidate))
    if not metrics["exact"]:
        raise ValueError("Lossless encoding changed pixels")
    # The source PNG is preferable when WebP would enlarge a small asset.
    if len(candidate) >= len(raw):
        return raw, "png", dict(mode="original", quality=100, **metrics)
    return candidate, "webp", dict(mode="lossless", quality=100, **metrics)


def validate_image(original, delivered, *, protected=False):
    original, delivered = original.convert("RGBA"), delivered.convert("RGBA")
    metrics = quality(original, delivered)
    opaque = original.getchannel("A").getextrema() == (255, 255)
    if protected or not opaque or original.width * original.height < MIN_LOSSY_PIXELS:
        if not metrics["exact"]:
            raise ValueError("Protected artwork changed pixels")
    elif not acceptable(metrics):
        raise ValueError("Image compression quality below policy limits")
    return metrics


def composite(level, images, phase=0):
    animation = level["paintedAnimation"]
    result = images[animation["background"]].copy()
    width, height = result.size
    for part in animation["parts"]:
        x, y = part["rect"][:2]
        dx = part["axis"][0] * part["amplitude"] * width / 343.0 * phase
        dy = part["axis"][1] * part["amplitude"] * height / 428.75 * phase
        result.alpha_composite(images[part["source"]], (round(x * width + dx), round(y * height + dy)))
    return result


def validate_animation(level, originals, delivered):
    """Compare the rest transition, layer seams and both motion extrema.

    Cutout RGBA stays exact. The original authored geometry is used for all
    comparisons; no placement or motion is changed by this publication step.
    """
    animation = level["paintedAnimation"]
    source = originals[level["image"]]
    width, height = source.size
    rest = composite(level, delivered, 0)
    if composite(level, originals, 0).tobytes() != source.tobytes():
        raise ValueError("Authored animation does not reproduce the puzzle")
    result = {}
    for name, a, b in [("rest", source, rest), ("transition", delivered[level["image"]], rest),
                       ("motion_negative", composite(level, originals, -1), composite(level, delivered, -1)),
                       ("motion_positive", composite(level, originals, 1), composite(level, delivered, 1))]:
        metrics = quality(a, b)
        if not acceptable(metrics):
            raise ValueError("Animation compression quality failed: " + name)
        result[name] = metrics
    # Thin visible cutout boundaries must not hide poor local quality in the
    # full-frame average. Include antialiased alpha and a 2px neighborhood.
    for index, part in enumerate(animation["parts"]):
        cutout = originals[part["source"]]
        alpha = cutout.getchannel("A")
        border = np.asarray(alpha.filter(ImageFilter.MaxFilter(5)), dtype=np.int16) - np.asarray(alpha.filter(ImageFilter.MinFilter(5)), dtype=np.int16)
        mask = border > 0
        if not mask.any():
            continue
        x, y = round(part["rect"][0] * width), round(part["rect"][1] * height)
        box = (x, y, x + cutout.width, y + cutout.height)
        for label, reference in [("source", source), ("transition", delivered[level["image"]])]:
            delta = np.asarray(reference.crop(box), dtype=np.float32)[:, :, :3] - np.asarray(rest.crop(box), dtype=np.float32)[:, :, :3]
            score = psnr(float(np.mean(delta[mask] ** 2)))
            if score < MIN_PSNR:
                raise ValueError("Animation edge quality below policy limits")
            result[f"edge_{index}_{label}"] = score
    return result
