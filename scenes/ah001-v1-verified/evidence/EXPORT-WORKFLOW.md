# Shared painted-scene exporter

Use `export_scene.py` in this directory. It exports one visually reviewed scene from real generated source images. It does not generate images, change gameplay, publish content or turn planned rows into completion claims.

Use the full prompts in `scene-art-plan-120.json` as initial briefs. They are plans: inspect the generated background and adapt every moving part to real anchors. Add explicit anchor locations to the background brief where useful, then derive the atlas brief from that actual painting. The pilot replaced a mismatching patterned napkin with a purpose-painted butterfly. Avoid exact fabric-seam matching unless the patterns and lighting really agree.

Generate one portrait 4:5 clean plate and one transparent 3×2 atlas with five scene-specific details; the sixth cell should be empty. Keep every original, exact prompt and generator output path. Inspect alpha against two contrasting backgrounds. Never use rectangular scenery crops as moving details. The source style reference is the detailed warm painted puzzle picture in approved `02-gameplay.png`. Each scene and each painted part must be unique.

Create a JSON spec, using the example below. Parts use zero-based atlas cells. `maxSize` preserves the part's aspect ratio. `bottom` aligns the actual lowest painted tip (for stems/steam) with a background pixel anchor; `center` aligns its bounding-box center; `top_left` places the exported box directly. Choose anchors by inspecting the actual background, not by blindly copying plan rectangles.

```json
{
  "levelId": 2,
  "sceneId": "ah001-002-markets-shops",
  "theme": "markets-shops",
  "masterPixels": [1280, 1600],
  "atlasGrid": [3, 2],
  "visualReviewed": true,
  "noDestinationLandmark": true,
  "visualReviewNotes": "Describe real anchors, alpha checks and composition review here.",
  "sources": [
    {"name": "background", "path": "C:/.../background-original.png", "prompt": "Full actual generation brief"},
    {"name": "atlas", "path": "C:/.../atlas-original.png", "prompt": "Full actual generation brief"}
  ],
  "parts": [
    {"subject": "scene-specific leaf branch", "source": "atlas", "cell": [0, 0], "maxSize": [220, 250], "anchor": {"mode": "bottom", "point": [1000, 460]}, "axis": [1, 0], "amplitude": 4}
  ]
}
```

The example has one illustrative part; actual specs require exactly five. For a separately regenerated part, add another source entry and omit `cell` on that part. `mainColour` can be supplied only after visual review; otherwise the exporter measures the median colour of the dominant saturated hue bucket. Its five hue buckets are evidence, not a complete perceptual colour classifier: inspect neutral backgrounds and adjacent scenes yourself. Set `mainColourLabel` to the actual reviewed colour family. A different hex value alone does not prove a different main colour.

Run from the repository root:

```powershell
python reports/ah-001-2026-09-30/scenes/export_scene.py --spec reports/.../scene-spec.json --art-root assets/art/ah001-scenes --report-dir reports/.../scene-002
python tools/ingest_painted_scenes.py --manifest reports/.../scene-002/complete-scene-manifest.json --art-root assets/art/ah001-scenes --output builds/ah001-art-candidate-002
```

Each scene gets seven runtime files, unchanged originals under its ignored `source/`, a one-scene complete manifest, contact sheet and exact-composition validation. Keep individual scene manifests separate. For a batch, concatenate only their `scenes` arrays under the same schema header, then run strict ingestion again. Root consolidates ranges later.

Before marking a batch ready: inspect every composite and all five layers, verify actual palette difference at each neighboring boundary, compare exact reconstruction, pass ingestion, and capture the 3000 ms renderer animation. Implementation review is not PM approval. Remaining scenes stay explicitly unfinished until their paintings and checks exist.

## Inspected transparent gutter extraction

A part may set `cellInset` to a nonnegative integer (all four sides), or `[left, top, right, bottom]` pixel values inside its atlas cell. This is only for removing verified empty-gutter border artifacts from a generated atlas, never for clipping a real painted subject or hiding a bad overlapping atlas. Nonzero values require `cellInsetReview` describing the inspected empty gutters and discarded border pixels. Inspect both light and dark alpha previews and alpha values before use. The exporter preserves the original atlas, original cell rectangle, actual inset extraction rectangle, inset values, review, and subsequent alpha crop in each part's provenance. Omit this option for clean atlases.

## Opaque clean plates

The original background, resized exported clean plate and final composite master must have alpha255 at every pixel. The exporter rejects translucent backgrounds before emitting a complete manifest. Do not flatten a defective generated clean plate onto an invented matte to conceal source alpha; regenerate it and preserve the rejected original for evidence. Cutout sprites still require genuine transparency.
