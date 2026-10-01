# AH-001 production UI artwork

UI export freeze:2026-09-30.50painted asset subjects,61PNG files including states. This freeze excludes the still-unfinished120unique non-landmark puzzle scene paintings and their five-part motion art.

- `asset-contract.json`: exact filenames, nominal sizes, state names and integration aliases.
- `artwork-manifest.json`: every original source hash, crop, exact export dimensions, export hash, full generation brief, calibration, typography/layout metadata and six approved board hashes.
- `source/`: unchanged original source generations or unchanged reused painted art. The `.gdignore` prevents these large authoring masters from entering the mobile resource import/export pipeline.
- Runtime PNGs are ~7MiB total. All have real RGBA; source alpha is preserved. Painted brushwork, silhouettes and surface detail come from image-generation artwork or the previous reviewed bespoke painted set, not synthetic geometry placeholders.

## Integration

Use exact specified logical dimensions from the contract. Icons preserve their source proportions inside exact export boxes; do not crop away intentional transparent padding or stretch a winged ticket into a square.

`wood_panel`:128×128logical nine-slice,13ptcorners. `hud_pill`:132×33logical, full16.5ptend caps. Both measured flat-face colours match D1772B and91490D. `paper_tile`matchesEBCFB0; `join_glow`matchesFBF3E1 and should render white×fade alpha at up to4ptorthogonal width.

`loading_frame`:329×38logical, exact9ptinsets,20ptrecessed track (the requested21ptwith±1tolerance). Inner rectangle is[9,9,311,20]. Measured wood face209,119,43; track178,112,67 (target177,112,67). `loading_fill`:311×21logical with central51BE2B, align/clip into the inner track. Geometry was reflowed from the authored painted capsule skin because the initial generated loading frame had excessive end-rim width.

`city_banner_<destination>` includes exact51ptLilitaOne title and a51×24ptpainted flag, on the common painted leaf/flower plaque. Longer names are horizontally condensed while keeping the51ptfont height. Do not draw a second city name or flag on top. `level_complete_banner` already contains its painted English title. Its baked text is English; localized asset variants are outside this packet.

`stamp_<destination>` has no paper backing and is upright; the renderer applies the requested−12°rotation. All six city names andARRIVEDare readable; all stamps contain a plane and worn double rounded outlines.

`gift_daily_unclaimed` contains the20ptgreen dot within its36×37ptstate canvas, so the gift body is smaller in that self-contained state. To keep the idle gift body at36×37ptwhile adding the dot outside its corner, compose `gift_daily` and separate `green_dot` in the UI. Goals continue using the previous green gift per the packet.

`departure_window` is780×1688(390×844logical). Its transparent aperture bounds are[123,327,535,899]pixels, approximately[61.5,163.5,267.5,449.5]points. Draw sky/cloud layers behind it; opacity belongs to the painted cabin wall. Both cloud banks are painted RGBA layers. Runtime owns the near60pt/s,far30pt/s timing.

## Reproducible export and checks

Run in order:

1.`python reports/ah-001-2026-09-30/export-art-assets.py`
2.`python reports/ah-001-2026-09-30/finalize-art-exports.py`
3.`python reports/ah-001-2026-09-30/validate-ui-art.py`

Read `reports/ah-001-2026-09-30/ui-art-validation.json` and the full contact sheet for evidence. Validation checks exact dimensions, RGBA mode, source/export hashes, states and calibrated button-face colours. UI screenshots and runtime animation tests remain root's integration responsibility; a correctly-sized PNG alone does not prove the displayed screen matches the PM layout.
