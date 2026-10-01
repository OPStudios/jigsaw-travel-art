# Authored scene review

Frozen candidate: `8852485190fb10e7ed5cc36d8ac9601941c0b90501f90cdb2f5e4b63fffb627c`.

10 unique scenes each contain five painted alpha cutouts, one clean background and an exact RGBA composite master. All masters are 1280 x 1600. Geometry revision 2 and content contract 1 remain unchanged. This is implementation evidence, not PM approval or physical-device acceptance.

## Current verified renderer evidence

All 10 scenes passed a fresh run with the current capture harness. The verified candidate was registered before the session was constructed; every proof confirms its staged configuration, seed and capture-harness hash. All 610 PNG frame hashes were independently rechecked. Each scene has 61 samples from 0 to 3000 ms, five moving painted details, zero changed pixels outside their allowed regions, and no engine or script error markers. Movement stays within 4 points and returns to rest; centered completion zoom reaches 105%.

Capture harness SHA-256: `297d896e5f31a1b4f5b9cc3524bf1128c333ea323210740d2f3dd11e5a41360d`.

Current captures are exclusively `scene-*/gpu-verified-config/`. Earlier `gpu-final/` captures and the previous review summaries are retained under their original folders and `superseded-evidence/`; they do not establish the current verified-session acceptance.

The separate alpha-visibility audit checks 61 time samples at a conservative 343 x 428.75 logical-point picture size. The independent 105% zoom plus peak-motion envelope retains at least 2.9479 source pixels at every edge, exceeding the 1-pixel requirement. No alpha pixels above 8 clip on the sampled actual curve. Strict ingestion, original geometry, opaque backgrounds/masters and exact at-rest composition had already passed and remain hash-identical.

## Evidence

- `complete-scene-manifest.json`: frozen authored content contract.
- `runtime-validation.json`: all verified-harness runs and renderer status.
- `final-frame-verification.json`: proof/log hashes and verification of every frame.
- `gpu-verified-config-contact-sheet.jpg`: current production renderer at 750 ms.
- `visibility-final.json`, `opacity-audit.json`, `strict-ingestion-result.json`: unchanged preparation gates.
- `final-freeze.json`: current acceptance hashes, including the unchanged artwork.
- `generation-sources.json`, scene specs and retained `source/` files: painting prompts, extraction provenance and natural anchors.

No source artwork or scene manifest was edited during this recapture. Root independently accepted the final compositions; this work refreshes the renderer evidence and review text only.

## Additive replacement lineage

This batch is the separate visibility-v2 replacement. Original scenes 11-20, their 70 artwork files, original manifest and original candidate remain unchanged. `lineage.json` and `original-preservation-proof.json` retain that history. All replacement scene IDs and art folders end in `-visibility-v2`.

The authored visibility changes cover 12 parts 3/4, 13 part 1, 14 part 5, 15 parts 1/2, 16 part 4, 19 part 3 and 20 part 5. Natural vase, branch and peg anchors are retained; meadow flowers remain in their bed and the near-top cloud moved 4 master pixels. The earlier corrected scene 17 thread coil is retained.
