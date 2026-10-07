# Reproduce the reviewed completion GIF samples

**Historical experiment:** the user subsequently raised the GIF cap to 5,000,000 bytes and requested more meaningful physical scene animation. These original 1 MB A/B samples and this reproduction recipe remain evidence only; they are not the current production quality target.

`encode_sample.py` is an isolated offline recipe for one level at a time. It does not write game assets, modify a CDN catalogue, publish files, or integrate playback. The review is in `docs/qa/gif-size-review-2026-10-04/index.html`. No 120-level batch is approved by this recipe.

Both profiles bake the five existing painted parts and 100–105% zoom into an actual GIF. They retain 75 frames at 40 ms each, exactly three seconds, no loop extension, and the final 105% frame. Authored part axes are preserved with a maximum amplitude of 4pt; the image returns the parts to their home positions at the end. Full-size authoring happens at 1128×1350 before the explicit resolution reduction.

| Profile | Review file | Canvas | Global palette | Gifsicle optimization | Measured level-1 bytes |
| --- | --- | --- | --- | --- | ---: |
| A | `more-colors.gif` | 208×249 | 255 colors | `-O3 --lossy=40` | 980,210 |
| B | `more-detail.gif` | 256×306 | 64 colors | `-O3` | 962,355 |

A retains richer gradients but loses fine detail and adds some grain. B retains more spatial detail but shows color banding, especially in the sky and honey. Gifsicle's lossless optimization for B means no *additional* pixel changes after palette reduction; it does not mean lossless reproduction of the full-color source. Neither profile retains the original PM resolution. These GIF samples are a separate visual review choice; the existing PNG/WebP compression policy remains unchanged.

## Requirements

The reviewed run used Python 3.14, Pillow 12.3.0 with libwebp 1.6.0, and Gifsicle 1.93. The existing repository compression module imported for immutable source verification also requires NumPy. No executable is downloaded or installed by this script. Pass an explicit Gifsicle executable path; any version other than 1.93 is rejected. A different Pillow/libwebp build may produce different bytes, so `--compare-with` is required when verifying an exact reproduction.

The reviewed Windows optimizer was supplied by npm `gifsicle@7.0.1`, upstream `imagemin/gifsicle-bin` tag `v7.0.1`. Binary SHA256: `839226b95887c0911e3b8ed562a9971d8ae5c0bea2515e266d8fa5a4d0754186`. The encoder records the actual binary hash and library versions. That platform-specific binary hash is evidence, not an automatic downloader or a cross-platform binary requirement.

## Run from the repository root

Supply your installed optimizer path in place of `<path-to-gifsicle>`. The catalogue's filename must equal its SHA256, and its referenced local object files must already be present. All level/background/cutout byte counts and hashes are verified before use.

```text
python tools/prototypes/completion_gif/encode_sample.py --catalogue builds/cdn/releases/abd71aee7d39fa611a2ca0f27178b8fd24301b4df871d510e3cbd2db1af846f5.json --level-id 1 --gifsicle <path-to-gifsicle> --profile A --output reports/completion-gif-reproduction/profile-a.gif --compare-with docs/qa/gif-size-review-2026-10-04/more-colors.gif
```

For B, change `--profile A` to `--profile B`, use a new output filename, and compare with `docs/qa/gif-size-review-2026-10-04/more-detail.gif`. Existing files are never overwritten. Without `--compare-with`, the script still enforces conformance but makes no byte-for-byte reproduction claim.

The script trains a median-cut palette using source frames 0, 19, 37, 56 and 74, quantizes all 75 resized frames without dithering, and writes transparent deltas with disposal 1. Gifsicle then applies `--no-interlace --no-loopcount` plus the profile's optimization settings.

Before writing the final output, `tools/completion_gif.py` independently validates the strict GIF subset and checks every composited frame against Pillow. Files over **1,000,000 bytes** are rejected; so are incorrect frame counts, frame delays, loops, invalid palette references, or decoder mismatches. If `--compare-with` is supplied, both the exact file bytes and all 75 decoded-frame records must match the reviewed file.

The adjacent `.gif.json` records every source object's hash and byte count, authoring parameters, encoder versions/options, output identity, frame timing, decoded frame hashes, and comparison result. Every future level must pass its own cap and format checks; these two presets do not guarantee that all 120 levels will fit.

## Current 5 MB natural-action preview

The subsequent `encode_scene.py` recipe is authored specifically for the inspected level-1 scene. It uses the same verified CDN background and cutouts, plus their semantic authoring record. It does not invent shapes or repaint the scene. Offline deformation of the existing painted pixels creates five distinct actions:

- Tea steam curls upward and dissipates as a fresh wisp forms at the cup rim.
- Thyme leaves flex with a fixed stem base.
- The daisy nods on its flexible stem with a fixed vase attachment.
- Butterfly wings fold around the body as it hovers along a short curved path and returns.
- Mint tips flex separately around their fixed central join.

The 75 × 40 ms timing and 100–105% camera remain. The five painted parts return to their original pose at the end. These are baked GIF pixels; the runtime does not need to animate cutouts.

Use the same explicit Gifsicle 1.93 executable and an existing `authoring.portable.json` from the art archive. The script checks its level and subjects, verifies all five original cutout hashes, and checks they match the selected immutable CDN source identities. It rejects an unrelated scene rather than reusing these actions blindly.

```text
python tools/prototypes/completion_gif/encode_scene.py --catalogue builds/cdn/releases/abd71aee7d39fa611a2ca0f27178b8fd24301b4df871d510e3cbd2db1af846f5.json --authoring <art-archive>/scenes/ah001-v1-verified/ah001-001-food-drink/authoring.portable.json --gifsicle <path-to-gifsicle> --width 376 --output reports/gif-meaningful-motion/level-001-natural-376.gif
```

The reviewed natural-action candidate is **4,371,702 bytes**, **376×450**, with a 255-color global palette, no dithering and no additional lossy Gifsicle setting. Independent conformance verifies all 75 composited frames. Its sidecar records the five action descriptions, unique deformed poses, source identities, encoder settings and GIF validation. Still frames are exported for source/palette and seam inspection. The exact **5,000,000-byte** cap is enforced before writing a final GIF; the unchanged PNG/WebP policy is separate.

All 120 scenes have part subject labels and explicit anchors. Historical records use two keys, `anchor.kind` and `anchor.mode`; both must be read. Scene subjects vary substantially, so the batch uses semantic physical rigs, the original attachment coordinates and visually inspected overrides. The single-scene recipe deliberately does not generate all 120 levels; `encode_batch.py` requires an explicit level range and reviewed art-repository profiles.

## Final 120-scene batch

`author_profiles.py` creates explicit physical profiles for all 600 painted parts, retaining source placement metadata and the inspected `overrides.json`. Each subject is assigned an appropriate action; unknown subjects fail rather than receive a generic moving-sprite fallback. Source contact sheets and body-axis/attachment reviews inform the saved overrides.

`encode_batch.py` uses at most three CPU workers and verifies the immutable catalogue, level package, composition recipe, compressed source objects, original painted-part hashes and authoring metadata. It requires five bound parts, verifies non-static actions and their return to the home pose, and rejects visible clipping. The first candidate is 376×450 with 255 colors; bounded alternatives are 352×421 and 320×383, using Gifsicle loss levels 0, 10 or 20 at each size. There is no frame-count or timing reduction. Each accepted file independently passes the exact 5,000,000-byte cap and all 75 frame comparisons against the separate GIF decoder.

Example (explicit local paths are supplied by the caller):

```text
python tools/prototypes/completion_gif/encode_batch.py --catalogue <sha-named-contract2-catalogue.json> --art-root <art-repository> --profiles <art-repository>/animation/ah002-gif-v1/profiles.json --gifsicle <gifsicle-1.93> --output reports/gif-completion-final --levels 1-120 --workers 3
python tools/prototypes/completion_gif/review_batch.py --root reports/gif-completion-final
```

Every GIF has a JSON receipt with exact source/output hashes, physical profiles, encoding attempts, independent frame hashes and advisory palette metrics. Resume verifies the requested source level, catalogue, composition, motion profile and actual GIF identity; stale or partial outputs fail closed. The final `index.json` binds each GIF to its unchanged source composition for packaging, and `download-summary.json` records actual per-city and aggregate bytes. Independent QA receipts approve exact final GIF identities only.

The final directory is separate from exploratory first-pass encodings. All 120 GIFs must be available in the local review gallery before upload. **Publication is explicitly on hold until the user reviews that complete set and approves uploading it.** Local authoring and technical QA do not imply that approval.
