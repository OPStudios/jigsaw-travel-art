# Authored scene review

Staged candidate: `8852485190fb10e7ed5cc36d8ac9601941c0b90501f90cdb2f5e4b63fffb627c`. This is implementation evidence, not PM approval or a published release.

10 scenes with five unique painted cutouts each, one clean plate and exact RGBA composite master. All masters are 1280Ã—1600. Geometry revision2 and content contract1 are preserved.

Strict ingestion passed after the shared visibility gate was added. All 20 master/plate images are fully opaque. Every cutout extraction border is empty above alpha 2. All scene/art hashes verified. Total runtime PNG size is 78,734,108 bytes; largest object 4,581,976 bytes, below 16 MiB.

Actual GPU renderer: all 10 scenes passed, 61 frames each across 0â€“3000ms, all five layers change and zero pixels outside their regions change in the same-zoom comparison. All 610 PNG frame hashes reverified; no script/engine error markers. This offscreen desktop fixture does not claim physical-phone acceptance.

Full authored-alpha visibility: 61 time samples,343Ã—428.75point reference picture. Conservative105% zoom plus independent peak motion preserves at least 2.9479 source pixels on each edge (requirementâ‰¥1). No clipped alpha >8 pixels.

Review files:

- `complete-scene-manifest.json`: complete runtime input contract.
- `master-review-*.jpg`: full scene compositions.
- `final-gpu-contact-sheet.jpg`, `scene-*-completion.gif`: actual runtime evidence.
- `visibility-final.json`, `final-frame-verification.json`, `opacity-audit.json`: numerical checks.
- `final-freeze.json`: exact final hashes.
- `generation-sources.json`, per-scene `scene-spec.json`, retained scene `source/`: original painting prompts, provenance and anchors.

This is an ADDITIVE replacement proposal. Original batch11â€“20, its 70 artwork files, manifest, immutable candidate and GPU evidence remain unchanged. `lineage.json` and `original-preservation-proof.json` record the original manifest/hash proof. All scene IDs and folders end in`-visibility-v2`. No old asset/spec was edited, and no candidate was integrated/published.

Scale/placement corrections affect 12p3/p4, 13p1, 14p5, 15p1/p2, 16p4, 19p3 and 20p5. Changes preserve real vase/branch/peg anchors where possible; meadow flowers remain rooted within their bed, and the near-top cloud moved 4 master pixels. The earlier corrected 17 thread coil is retained.

The prior overwrite was automatically rejected. The safer additive proposal was accepted, preserving the whole prior version. Root selects this distinct manifest during review; boundary10â†’11 remains a consolidation check.
