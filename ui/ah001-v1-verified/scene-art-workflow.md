# AH-001 painted scene production contract

This workflow is for AH-001-91, -92 and -96. A completed scene is one flattened puzzle image, its clean painted background, and exactly five painted transparent moving parts. Generic particles, arbitrary rectangular fragments of the flattened image, and a decorative overlay unrelated to the picture do not meet this contract.

## Authoring

1. Choose one of the ten permitted themes and one dominant colour different from the previous level. A destination landmark is prohibited in the puzzle image; it remains appropriate for postcards and Arrival only.
2. Write a scene-specific composition brief, with five named things that plausibly move up to4logical points. Examples include a leaf cluster, curtain edge, hanging pennant, steam wisp, or reflection. Avoid moving an entire rigid building or anatomy without coherent joints.
3. Paint a clean background plate, keeping composition, light direction, painterly style and palette consistent with the six approved Art Direction V2 boards. The areas behind the five moving elements must contain finished painting. A cloned smear, blurred rectangle, or transparent hole is not a clean plate.
4. Paint the five actual foreground parts on transparent alpha using the same scene brief and references. Each part must have no background matte. Generate each requested layer separately using the built-in image-generation workflow. Preserve original generations and exact prompts.
5. Assemble the five painted layers at recorded integer source-pixel rectangles on top of the clean plate. This composition becomes the flattened puzzle image. Thus at-rest reconstruction can be exact; no approximation is needed. Alternatively, a human illustrator can supply a single layered painting, exporting its original background and five layers.
6. Inspect the complete image and all five layers at full resolution, at a390ptwide screen, and on black/cream backgrounds. Verify that each visible part is actually part of the picture and that a4ptmotion exposes finished painting.
7. Export the background at the delivered puzzle-image dimensions, and crop each part tightly to its real alpha bounds. Preserve the integer rectangle of that cropped layer relative to the background. Do not multiply full-size textures for each tiny part.

## Runtime handoff

One level entry uses:

```json
{
  "paintedAnimation": {
    "version": 1,
    "background": "res://assets/art/themes/<scene>/background.png",
    "parts": [
      {"source": "res://assets/art/themes/<scene>/part-01.png", "rect": [0.1, 0.2, 0.15, 0.08], "axis": [1, 0], "amplitude": 4}
    ]
  }
}
```

The example contains only one illustrative entry; production requires exactly five. `rect` is x,y,width,height normalised against background dimensions; retain source-pixel rectangles in the source manifest. The runtime owns the single3000ms out-and-back cycle, maximum4pttranslation, zoom100%→105% over3000ms, and clipping within the board.

## Required evidence per scene

- Theme and dominant-colour label, previous-level comparison, explicit no-landmark review.
- Clean background, five RGBA parts, flattened puzzle image, original source filenames, full briefs and SHA-256 hashes.
- Exact pixel rectangles plus matching runtime normalised rectangles.
- Automated dimensions/alpha/path/exactly-five validation.
- Pixel comparison: composing the delivered layers at rest must reproduce the delivered flattened image exactly before any intentional export compression.
- A contact sheet showing flattened scene, clean background, five cutouts against a checker or contrasting backing, plus the at-rest reconstruction.
- A recording of the complete3000ms motion; static screenshots cannot certify motion.

## Current environment limitation

Fresh built-in image generations work. Reading local paths through view_image currently fails with the Windows filesystem sandbox ACL helper. The image generation reference-path editing route had the same failure in the previous art pass. Do not silently claim an edited existing master or identical reference-guided extraction under that limitation. Read-only image inspection can use a rendered preview; fresh layered painting can follow the authoring workflow above. An existing painted image still requires actual clean-plate and layer art before runtime metadata is marked production-ready.
