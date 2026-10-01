# Painted scenes 31–40

Status: implemented and visually reviewed artwork candidate, not PM approval or published content.

Ten unique 1280×1600 masters, ten fully opaque clean plates and fifty independently painted transparent details. Every rest-state composition reconstructs exactly. Original image-generator outputs and exact built-in generation prompts are retained in scene source folders and generation-records.json. No scene identifies a destination landmark.

Strict candidate: builds/ah001-art-candidate-031-040/scene-candidates/dbb07fb75477d65222f4459a3be0c15b4588d22abff6fa351c350ef136f4294d.json. Geometry revision 2 is preserved. A non-normalized butterfly direction was rejected by ingestion, corrected to a unit vector, and revalidated without weakening the gate.

## Art review

All ten composites, all fifty layers against light/dark grounds, and the final production-game screenshots were visually inspected. Atlas boundary problems were resolved by a fresh bounded steam sheet (31), documented removal of empty four-pixel grid gutters (32), a complete new hanging lantern (34), new flat thread/leather details with natural table contact (37), lossless complete-subject extraction rectangles (38), and a new kite without an unrelated white mark (40). Original sources remain retained; the rejected objects are not runtime layers. Vessel mouths, stems, hooks, strings and surfaces determine placement.

The neighboring visible palettes progress violet cloth → ivory bookstall → turquoise water → olive/amber night market → berry-red library → coral wall/yellow tram → terracotta leather → golden meadow → cocoa woodland → blue sky. Global hue histograms and actual representative surface samples remain in authoring provenance; different hex values alone are not presented as visual proof. Boundary 30/31 is reviewed in the combined catalogue, and 40/41 waits for scene 41.

## Renderer evidence

Ten real GPU runs passed, covering 610 frames from 0–3000 ms. All fifty details visibly change pixels; zero changed pixels fall outside authored regions. All 610 saved frame hashes were rechecked. Final evidence is runtime-validation.json and each scene-NNN/gpu-final/motion-proof.json. The 30 source/background/master opacity checks all pass alpha 255 throughout. This is desktop production-renderer evidence, not physical-phone acceptance.

Runtime artwork totals: 81,566,457 bytes in 70 unique PNG files; largest 5,038,978 bytes. art-freeze.json records their final hashes.
