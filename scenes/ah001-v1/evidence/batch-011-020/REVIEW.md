# AH001 scenes 11–20 — authored batch review

Status: authored and independently inspected implementation candidate; not PM approval and not published. Gameplay source and revision-2 geometry were not changed.

The batch contains ten unique 1280×1600 portrait masters, ten clean plates and fifty individually painted RGBA moving cutouts. Each master reconstructs pixel-for-pixel from its clean plate and exactly five cutouts. Original generator outputs, exact prompts and the technical extraction rectangles remain in each scene's ignored `source/` directory and this batch's source/spec records.

## Final candidate

- Manifest: `complete-scene-manifest.json`.
- Candidate: `builds/ah001-art-candidate-011-020/scene-candidates/18986ec0fd4a761df7facf0cb0bf1ce88fe59a0198c833f98446ba739ff47cb2.json`.
- Strict ingestion: ten scenes, seventy unique PNG objects, ten scene-record objects; capability 1, geometry revision 2, immutable art revision `ah001-v1`.
- No complete twenty-scene city was fabricated from this ten-scene range. Cross-range adjacency 10/11 still needs the consolidated review.
- Seventy runtime PNGs: 78,792,490 bytes (75.14 MiB); largest PNG 4,584,552 bytes. Existing 16 MiB object, 4096-pixel decode and 256 MiB cache limits remain unchanged.

## Visual review

See `final-master-contact-sheet.jpg`, the three `review-masters-*.jpg` sheets, and both `alpha-contrast-*.jpg` sheets. All fifty cutouts were checked on cream and dark backgrounds. None has nontransparent pixels above alpha 2 on its original extraction border after choosing genuine empty gutters; no painted subject was clipped.

The defining surfaces vary from terracotta breakfast, golden market awning, cocoa-tan meadow, blue plaster, violet studio, ivory fence, turquoise sewing table, green garden, crimson harbor water to light coral stage cloth. The warm late-afternoon palette intentionally recurs, but adjacent defining surfaces and themes differ. Broad hue histograms also count beige wood and warm shadows, so they are recorded alongside measured representative surface colors and visual notes in `size-and-palette-review.json`; different hex strings alone are not treated as evidence of different dominant palettes.

The independent root review identified the scene-17 cloth as appearing suspended. A newly painted flat coil of sewing thread replaces it and visibly rests on the worktable. The initial cloth and atlas remain retained as provenance. The scene-12 atlas's unwanted packet was also replaced by a purpose-painted standalone cotton bow attached to the existing packet.

## Actual renderer verification

`runtime-validation.json` records ten passing production-renderer runs against the final candidate. Each run renders 61 frames from 0 to 3000 ms, for 610 freshly hashed frames total. Every one of the five authored layers moves in every scene; comparison with the same zoom and zero part offsets finds zero changed pixels outside the authored regions. All frame hashes were rechecked.

Evidence is under each `scene-NNN/gpu-final/` directory. `final-gpu-contact-sheet.jpg` and `scene-017-completion.gif` are convenient previews. Earlier captures against the pre-correction candidate are retained in `gpu/` and `pre-thread-runtime-validation.json`; these are not the final proof.

This fixture renders the production puzzle board and authored-content runtime with deterministic GPU samples. Its unused HUD space is intentional. It is not a whole-app, signed-build or physical-phone acceptance claim.

## Boundaries

This batch does not change saves, replay rules, wallet values, game code, approved boards, installed SDK files, shared master manifests or live content. Root consolidation/publication, remaining scene ranges, cross-range palette review and eventual device qualification are separate pending work.
