# Refined completion GIF authoring

This offline pipeline applies the user-approved level-1 method (GIF SHA-256 `1542f4938ad508fd465a3d4b5c81a38a0db92259a550b909c65de080fb1bf45d`) to the existing 120 painted scenes. Approval of the method is not approval to upload the final set. Every final GIF remains available for user review before publication.

The approved level 1 and independently reviewed level 3 prototypes are reused byte-for-byte. Other scenes use source-bound decisions: continuous emissions and reflection texture flow, fixed-root rigid plant responses, stationary resting objects, stable floating solids, restrained hanging objects and reviewed animal anatomy. There is no mandatory all-parts movement or forced return to the original pose. Ambiguous anatomy never receives a copied generic wing mask.

`build_profiles.py` combines the verified previous source/anchor inventory with explicit independent review overrides. Its `--corrections` inputs separately record actual-scene QA changes, preserving the prior action and correction source hash without modifying the frozen original review. Velocities are in reference 1128 x 1350 pixels/second; reviewed display-point velocities convert by a factor of 3. Original-pixel anatomical polygons scale with the actual cutout. Missing substantial painted mask pixels fail closed. Faint antialias fringes are preserved on the nearest painted component. Grouped butterflies use independent reviewed wing frequencies, entry delays and short flight directions; every clock begins at the exact original opening pose.

`encode_batch.py` uses at most three processes, retains only small in-memory frame arrays, and saves six decoded PNG poses for existing QA tools. Every GIF must contain 75 frames of 40 ms, use 255 painted colors, play once, retain the final 105% camera, remain below 5,000,000 bytes, and pass the independent strict GIF validator. The encoder first tries 376 x 450 and may reduce dimensions to preserve color quality within the cap. No quality budget is waived.

Each run preserves a content-addressed source capsule with exact source scripts, profile bytes, reviewer override bytes, immutable catalogue and external encoder identity. Each GIF receipt binds its own source capsule, per-scene profile, original art and composition identity. Subsequent reviewed profile corrections use a new capsule without rewriting previous evidence. Frozen inputs are checked before and after every scene; active runs must not be edited.

The production-compatible `index.json` contains only individually bound level IDs and GIF hashes. `download-summary.json` records exact total and per-city bytes. The pipeline never uploads, deploys, changes still artwork, or modifies the installed Base Client dependency. Level 43's existing source-art stem gap remains explicitly marked as a release blocker; its disputed part stays stationary at the original source placement until a synchronized still/GIF repair is approved.

Example (run from the client repository):

```powershell
python tools/completion_gif_refined/build_profiles.py --source <art>/animation/ah002-gif-v1/profiles.json --output <output>/profiles.json --overrides <review1.json> <review2.json> <anatomy-addendum.json> <timing-addendum.json> --corrections <actual-scene-corrections.json>
python tools/completion_gif_refined/test_actions.py
python tools/completion_gif_refined/encode_batch.py --catalogue <immutable-catalogue.json> --art-root <art> --profiles <output>/profiles.json --gifsicle <explicit-gifsicle1.93.exe> --output <output> --reuse-prototypes <approved-prototype-directory> --levels 1-120 --workers 3
```

Review actual GIF playback and independent decoded poses at final display size. Engineering conformance and anatomical pixel coverage do not by themselves establish natural motion or final visual acceptance.
