# Scenes 2-10: authored art and renderer review

Nine distinct non-landmark paintings are complete at 1280x1600. Each has a clean painted background and exactly five unique painted alpha details. This is implementation review, not Product Manager art approval.

- Strict ingestion with the level1 pilot passed for 10 scenes, 70 artwork objects and exact RGBA composition. Candidate SHA256: `1e615358a396d3275089b4c16964ba5d0be160b122572b8e91cdf722a0779907`.
- All nine new scenes passed the real production board capture: 61 frames per scene, 549 frames total. Every one of 45 layers produced changed pixels, with zero changed pixels outside authored regions. These are desktop GPU captures, not physical-phone acceptance.
- Reviewed final masters and actual GPU completion frames. Scene-specific stems, strings, tags, reflections and moving animals belong to physical objects or spaces in each scene.
- Scene 8 flower stem was moved into its window pot, away from the cat face. A clipped tassel was discarded and regenerated with its entire loop. Scene 5 steam was discarded because the painted table contains a vase; a unique window bumblebee replaces it.
- Atlases 2/3/4/7 have uneven original spacing. Complete painted silhouettes were extracted using recorded unchanged RGBA rectangles; all extraction boundaries have alpha at most 2. Original atlases and exact crop provenance are retained. A one-pixel empty cell edge on scene 5 removes faint alpha 3 noise.
- Adjacent themes differ. Actual visible palettes progress lavender, pond olive, turquoise, sage olive, berry red, peach porcelain, terracotta, cyan-green water and cocoa. Colors are measured from visible subject regions; global warm-light hue statistics remain separately recorded. Scene 7 is labeled peach porcelain rather than the provisional ivory brief.

## Evidence

- `complete-scene-manifest.json`: new scenes 2-10 and source/hash/part metadata.
- `pilot-plus-batch-manifest.json`: boundary check with scene 1.
- `final-master-contact-sheet.jpg`: final paintings and measured palette labels.
- `gpu-review-contact-sheet.jpg`: actual production renderer at 750 ms.
- `scene-*/gpu/motion-proof.json`: per-frame hashes, offsets, zoom, GPU and motion-region checks.
- `palette-review.json`, `atlas-alpha-review.json`, `extraction-provenance.json`: actual palette samples and source alpha/crop review.

No runtime source, approved Art Direction boards, catalogue, publishing state, native build or backend was changed by this batch. Scene 10-to-11 remains a cross-batch visual check for final consolidation. The full 120-scene requirement remains unfinished until every assigned batch is delivered and consolidated.

Explicit opacity check: all 30 original backgrounds, exported clean plates and masters for scenes 1-10 have alpha 255 in every pixel. Evidence: `opacity-review.json`.


## Completion visibility correction and clean recapture

The current masters and manifests supersede their earlier completion evidence. The final authored-alpha audit and all clean renderer captures are documented in `../VISIBILITY-CORRECTION-REVIEW.md` and `../visibility-owned-gpu-summary.json`. Every part meets the common ≥1-source-pixel conservative105%zoom-plus-motion clearance; all current source/background/master images are fully opaque. New evidence is in each scene’s `gpu-visibility-v2/`. The prior captures are retained as superseded records.
