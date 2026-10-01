# Completion artwork visibility review

The authoring review found details that fit their flattened master but clipped during the required centered 105% completion zoom and point-based movement. The existing GPU changed-pixel check did not detect lost silhouette pixels. This review adds a separate alpha visibility measurement; it does not change production rendering.

## Scope and method

All 150 painted parts in scenes 1–10 and 61–80 were checked at 61 times from 0 to 3000 ms, using the exact production shader projection. The common preparation gate uses343×428.75 logical picture points, alpha>8, and also requires at least 1 source pixel clearance with 105% zoom plus the independently largest declared displacement. Root measured the actual supported profiles and confirmed this picture size is conservative.

Current measured result: zero clipped alpha samples on the actual animation curve; every part exceeds the 1 source pixel conservative margin. Minimum clearance is1.8979 source pixels. Original backgrounds, exported backgrounds and masters for all 30 scenes are fully opaque:90 images checked. Both strict candidates pass byte hashes, unique paintings, exact RGBA composition, geometry preservation and opacity.

## Corrections

| Scene/part | Change and visual review |
| --- | --- |
|1/2 | Thyme sprig slightly smaller around the same real planter anchor;2pt sway. |
|4/5 | Lavender sway reduced 4→3 pt; raster and placement unchanged. |
|5/3 | New uniquely generated inward-leaning linen tassel, complete loop on the actual curtain tie. The old source is retained. |
|6/3 | Ivy placed farther along the real roof/branch junction and slightly smaller. |
|62/3 | Hydrangea scaled inward; stem enters visible pot foliage at the rim instead of ending on the pot face. |
|67/2 | Sea oats scaled around the original craft-jar anchor. |
|69/1 | Cattail slightly smaller around its existing marsh root. |
|71/3 | Fern root meets the actual potted stem junction; frond remains inside the picture. |
|73/3 | Scabious scaled around its original garden root. |
|76/3 | Daisy scaled around its original garden root. |
|80/2,4 | Lemon sprig and ivy scaled around their original branch contacts. |

Every changed master/detail was visually inspected after export. Detail comparisons are `visibility-corrected-details-1.jpg`, `visibility-corrected-details-67.jpg`, and `visibility-corrected-details-76.jpg`. Sources and generation prompts remain under each scene's `source/` directory and authored spec. The new tassel was made with the built-in image generator, inspected against light/dark surfaces, and exported from preserved RGBA without a background-removal substitute.

## Evidence

- `visibility-owned-corrected.json`: all 150 silhouette measurements and part hashes.
- `visibility-owned-opacity-review.json`:90 opaque-image hashes.
- `visibility-corrections-owned.json`: before/after export settings; scene 4 amplitude correction is additionally recorded in its spec.
- `batch-002-010/pilot-plus-batch-manifest.json` and `batch-061-080/complete-scene-manifest.json`: current exact-composition manifests.
- Strict candidates: `0dd95b91dd8d0574fabf89f60580a99d0d7fee675e1f92b8dd658da00ad0ff03` (1–10), `24cb88580bda650f2a1373fc02245e78cd103898c0f870738a7b679062825d8f` (61–80).

Final GPU recapture passed for all 30 scenes: 1,830 frame hashes verified, all 150 painted details visibly moved, zero changed pixels outside their allowed regions, zero runtime errors, and the staged session was verified before construction. The corrected harness hash is recorded in every proof. Movement stays within 4 points, returns at 3000 ms, and the picture zoom reaches 105%. See `visibility-owned-gpu-summary.json`. Earlier level >60 captures contained a catalogue assertion and are superseded by each scene’s `gpu-visibility-v2/` evidence. No physical-phone acceptance is claimed. This is implementation art review, not PM approval.
