# Coordinated level 43 source repair

The rosemary cutout is translated by (-15,+7) original 1280 x 1600 pixels onto the existing branch stub. The painted pixels, dimensions, other parts, puzzle contours and game rules are preserved. The still composition and completion GIF use the same repaired placement, so the repair introduces no still-to-animation placement change.

The repaired GIF is `level-043.gif`; its exact hash and new source/completion-index hashes are in `provenance.json`. `opening-contact-comparison.png` compares the repaired delivered still, unquantized opening and actual indexed GIF opening. GIF color quantization/resampling remain measured differences; no pixel-exact PNG/GIF claim is made. The source still's existing compression and transition gates passed unchanged.

`catalogue-rebinding.json` proves all 119 other level packages, still descriptors and GIF hashes are unchanged. Its index paths describe the original client authoring workspace; copy or rebase paths only after verifying their exact hashes. The prior 120-GIF review set remains unchanged, including its historical level 43 defect disclosure.

To reproduce, use the frozen source capsule's encoder for level 43 only with `source-repair/profiles-repaired.json`, the retained immutable CDN object root and the new source catalogue. The original parts remain in `scenes/ah001-v1-verified`; repaired source metadata/master are in `scenes/ah002-contact-repairs/level-043-v1`. Run the preserved `rebind_completion_source_043.py` against the prior reviewed set to produce the complete new index. The new master detail values were measured with the existing Godot 4.7.2 image-detail script; geometry vertices remain byte-identical.

Only this repaired GIF is duplicated in the archive. No publication, native build, commit or push is performed by the repair tools.
