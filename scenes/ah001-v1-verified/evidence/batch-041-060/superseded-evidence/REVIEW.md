# Authored scene review

Staged candidate: `2649a1504cc2b51ba42a084729f3885bf029d59de41ce75f6dd5b74b2ff94245`. This is implementation evidence, not PM approval or a published release.

20 scenes with five unique painted cutouts each, one clean plate and exact RGBA composite master. All masters are 1280Ã—1600. Geometry revision2 and content contract1 are preserved.

Strict ingestion passed after the shared visibility gate was added. All 40 master/plate images are fully opaque. Every cutout extraction border is empty above alpha 2. All scene/art hashes verified. Total runtime PNG size is 159,823,172 bytes; largest object 4,716,644 bytes, below 16 MiB.

Actual GPU renderer: all 20 scenes passed, 61 frames each across 0â€“3000ms, all five layers change and zero pixels outside their regions change in the same-zoom comparison. All 1,220 PNG frame hashes reverified; no script/engine error markers. This offscreen desktop fixture does not claim physical-phone acceptance.

Full authored-alpha visibility: 61 time samples,343Ã—428.75point reference picture. Conservative105% zoom plus independent peak motion preserves at least 1.4750 source pixels on each edge (requirementâ‰¥1). No clipped alpha >8 pixels.

Review files:

- `complete-scene-manifest.json`: complete runtime input contract.
- `master-review-*.jpg`: full scene compositions.
- `final-gpu-contact-sheet.jpg`, `scene-*-completion.gif`: actual runtime evidence.
- `visibility-final.json`, `final-frame-verification.json`, `opacity-audit.json`: numerical checks.
- `final-freeze.json`: exact final hashes.
- `generation-sources.json`, per-scene `scene-spec.json`, retained scene `source/`: original painting prompts, provenance and anchors.

The ten distinct themes repeat twice with visibly varied neighboring scenes. Scene 40â†’41 changes blue outdoor kite festival to golden indoor cocoa;60â†’61 changes sage music stage to warm ivory orchard food. See `boundary-review-40-41-60-61.jpg`. Color labels describe visually defining surfaces. Scene 44 uses its violet pixel population because warm sunlit masonry would bias a whole-image median; scene 47 is warm sage/olive gray rather than saturated green. Adjacent variety was inspected visually, not inferred merely from distinct hex strings.

Rejected translucent 43/44 backgrounds are preserved under`rejected-backgrounds/`. The overlapping crane/star draft and unwanted cloth-roll bow remain in original atlas provenance; final 57 crane/star and 55 bow were purpose-painted separately. No rejected source is a final runtime layer.

One full 20-level New York city specification is staged. Native shipping exclusions, archive transfer, consolidation with other ranges and publication remain with the lead workflow.
