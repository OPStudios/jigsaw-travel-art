# Scenes 21–30: artwork and renderer review

Ten unique complete compositions are staged for integration. They contain 50 separately purpose-painted transparent details and 70 unique runtime PNGs. This report is internal implementation acceptance; it does not assert Product Manager approval or publication.

- Every master is 1280×1600, with exactly five scene-specific alpha parts and a complete clean background. Recomposition matches the master byte-for-byte in RGBA.
- All complete silhouettes were inspected on ivory and navy backgrounds. Crop edges have alpha at most 2; no actual painted subject was clipped. The exporter preserves source images, exact prompts, isolation rectangles and attachment choices.
- Strict ingestion passed and preserved existing puzzle rule fingerprints. Candidate SHA-256: `016f3b7add41f6c8e82952341d446efd9b30184b374b28a0631bf3c6077f3ad7`.
- Actual production board/runtime rendered 61 frames per scene over 3000 ms: 610 GPU frames on NVIDIA GeForce RTX 3080 Ti. Each of all 50 parts caused visible pixel motion; no changed pixels escaped the allowed part regions. This is desktop renderer proof, not physical-phone acceptance.
- Every composition, all 50 alpha cutouts and the ten in-game completion views were visually reviewed. The ten animated WebP previews are beside their motion traces.
- Nine internal adjacent pairs have different themes and visibly different palettes. Whole-image mean colour differences range from 12.02 to 33.84 in DeltaE76, as supplementary measurements rather than a substitute for review. The coarse exporter hue bucket merges warm families and can pick parchment over a blue table; actual rendered labels and six-swatch evidence are retained in palette-review.json.
- Boundary 30/31 remains a root integration check. 20/21 crosses a city boundary; ingestion does not treat it as an adjacent pair.

## Reviewed scenes

| Level | Theme | Rendered palette | Five painted details |
|---|---|---|---|
| 21 | food-drink | warm olive green with lemon and wicker accents | young olive twig beside lemonade, fresh flowering thyme at hamper, pink daisy in small cream bud vase, pale blue garden butterfly, mint garnish on peach plate |
| 22 | markets-shops | berry red | cream berry pennant, awning tassel, white daisy, olive sprig, parcel ribbon |
| 23 | nature-gardens | coral pink with green foliage | jasmine vine, banana leaf, fern frond, spider plant, window cloud |
| 24 | streets-squares | warm terracotta | awning pennant, window jasmine, near cloud, foreground olive, wet paving reflection |
| 25 | interiors | golden yellow | tea steam, ficus leaves, vase daisy, window butterfly, teapot ribbon |
| 26 | transport | cocoa brown with blue canoe | morning cloud, mooring ribbon, shore alder, shore reeds, lake reflection |
| 27 | crafts-objects | sky blue and parchment cream | table ribbon, yellow butterfly, fresh loose botanical sprig resting on the map, notebook tassel, loose daisy |
| 28 | animals | soft violet | peach pond reflection, violet pond reflection, pond reeds, lily leaf, dragonfly |
| 29 | water-coast | warm ivory sand | near reflection, far wave glints, dune grass, near cloud, far cloud wisp |
| 30 | festivals-music | turquoise | flower pennant, peach lantern, coral bow, flower garland, ivory streamer |

## Corrections retained in evidence

Scene 21’s provisional cloth fold was rejected for a pattern seam mismatch and replaced with a newly painted butterfly. Scene 23’s spider plant was moved inward after a bounds check. Scene 26’s alder was anchored by its actual stem, not its lower leaf tip. Scene 27’s disconnected ivy extension was moved to rest as a botanical sample on the map. Scene 30’s first atlas overflowed its nominal cells and touched the source boundary, so a new complete atlas replaced it. Original rejected art and prompts are retained.

## Evidence

- `complete-scene-manifest.json`: exact merge input for root.
- `batch-validation.json`: 70 file sizes and SHA-256 values, aggregate proof.
- `batch-compositions.jpg`: neighbouring full compositions and measured palette swatches.
- `alpha-light-dark-021-025.jpg` / `alpha-light-dark-026-030.jpg`: all 50 transparent silhouettes.
- `palette-review.json`: numerical palette evidence and nine pair reviews.
- `ingestion.json` and `candidate/`: strict staged candidate; no catalogue installed.
- Each `scene-NNN/`: complete scene spec, retained originals, source crop checks, exact assembly manifest/contact sheet.
- Each `scene-NNN/gpu/`: 61 original frames, `motion-proof.json`, `completion.webp`.
- `runtime-summary.json` / `runtime-contact.jpg`: all actual renderer results and board views.

Source gameplay, SDK, deployments and release versioning were not changed by this art batch.
