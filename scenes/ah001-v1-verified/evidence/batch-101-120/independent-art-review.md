# Independent review of scenes101–120

Reviewed all 20 actual final masters and all 100 exported painted alpha details. Each detail was viewed against both cream and dark teal and in its actual master context. Review-only sheets and alpha/opacity hashes are in `independent-review/`. No parent-owned source or artwork was edited by this reviewer.

## Findings

1. Scene 118 part 5 appeared unsupported on a vertical trunk. Root moved it to original-image center (400,1000) (exported (456,1141)), where the broad sloping bough supports the loose leaf. The corrected placement was visually inspected and accepted.
2. Scene 120 part 3 had only 4 source pixels of right clearance and clipped during the completion motion/zoom. Root generated a unique left-leaning flower with its stem in the same actual vase. The corrected master was visually inspected and the new silhouette passes the agreed conservative boundary measurement.
3. The newly quantified visibility check found additional actual clipping:106 part 2 (1.22% of weighted alpha),111 part 2 (12.66%),111 part 3 (0.67%),113 part 5 (0.68%). These are art-export placement/scale issues despite the prior GPU changed-pixel checks passing. Root is correcting them and must provide final visibility and recapture evidence.
4. Conservative 105% zoom plus independent peak movement additionally warned 101 part 1, 107 part 1, 108 part 4, and 117 part 4. They did not clip on the sampled actual motion curve but require the common conservative clearance before freeze.

The replacement 119 ripple was reviewed from the actual updated master, not the stale contact sheet. It is a calm, subdued surface reflection and fits the lake. Larger attachment crops confirmed the 102 flower, 110 pumpkin leaf and 118 lower hanging leaf pair meet their actual scene anchors; no correction was requested for those.

No additional clearly severed loops/stems/wings, rectangular matte remnants, missing parts or stretched cutout shapes were observed in the 100 alpha panels. Fine resized edges can have nonzero border alpha; this alone was not treated as proof of a clipped shape. Final edge visibility is instead measured on the actual silhouette in motion.

## Limits and evidence

`independent-review/geometry-review.json` records the initial 100-part analysis. `independent-review/118-120-corrected-placements.jpg` records the two confirmed composition fixes. Initial review sheets preserve the initially reviewed masters and therefore must not be represented as final captures after root's subsequent corrections.

The reusable report-only tool is `../review_scene_visibility.py`. It uses the production shader projection at343×428.75 logical points, alpha >8, 61 times from 0–3000 ms and a separate 105% plus peak envelope. The required conservative clearance is ≥1 source pixel. Geometry results are not a substitute for fresh production GPU captures or physical-phone acceptance. This is independent implementation review, not Product Manager approval.


## Final independent closure

Root froze the corrected artwork after the initial findings. I re-inspected the actual final masters and light/dark alpha panels for scenes 101, 106, 107, 108, 111, 113, 117 and 119. The corrected 118 leaf and 120 flower had already been checked at their final positions. The revised flower scales and plant tips still meet their actual scene anchors; the new 111 flower leans into the composition and retains a natural vase contact. No additional concrete composition, missing-part, matte, or scale blocker was observed.

The final 100-part visibility report has zero actual-curve clipping and a minimum 1.4297-source-pixel conservative clearance. All 20 `gpu-verified-config/motion-proof.json` files were inspected and report verified staged session construction, 61 frames, five moving painted parts, zero changed pixels outside their allowed regions, and a successful result. The old `gpu-final/` directories are superseded evidence and must not be used as the clean acceptance record.

Final measurements, candidate/proof hashes and the complete manifest hash are recorded in `independent-review/final/closure.json`; the eight final inspection sheets are alongside it. All findings above are closed within this artwork-review scope. This remains implementation review rather than physical-phone acceptance or PM approval.
