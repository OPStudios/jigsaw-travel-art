# Artwork repair with immutable replay rules

This revision supersedes only the rule/catalogue binding of the earlier level 43
repair. All 120 GIF files and the repaired still pixels are unchanged. The exact
repaired GIF remains [in the preceding archive](../source-repair-043-bd0a67c9ae6720a4/level-043.gif).
The physical source defect is resolved by the matching still/GIF placement.

The first repair draft incorrectly copied fresh artwork measurements into
revision-3 piece detail and geometry.detailSource fields. The strict native gate
rejected that draft. Those values drive exact Hint/Sort ordering and replay, so
this revision retains every original authoritative rule byte instead. The new
artwork measurements remain in source-repair/source-repair-receipt.json, bound to
the repaired master and the exact Godot measurement request/result hashes. The
historical detailSource honestly records the original geometry authoring image;
it is not a claim that the current picture's measurements equal those values.

The corrected source and contract-3 catalogue identities are in provenance.json.
rules-provenance-migration.json proves all 120 rendered compositions/GIF hashes
are unchanged and points to their unmodified render-time receipts. No new render
receipt is fabricated for the metadata-only migration. The corrected source and
the retained old source both passed the unchanged native compatibility gate;
the new contract-3 candidate and 940 catalogue regression checks also passed.
Full publication still requires every strict still/GIF/native gate.

Reproduction uses the preserved source files under source/tools and source/tests:

1. Run repair_completion_source_043.py with the original abd71aee source
   catalogue, sibling art repository, original reports/gif-refined-final profile
   set, a fresh output directory, and Godot 4.7.2. This writes immutable repaired
   source data while keeping replay rules exact.
2. The already reviewed repaired GIF can be reused byte-for-byte. Restore the
   cdn-metadata files into an isolated staging tree containing the retained
   original CDN art/GIF objects; verify every content-addressed filename first.
   Run rebind_completion_rule_provenance_043.py with the prior repair index,
   preserved fc194 candidate, new source-repair directory, and fresh output.
3. Pass the resulting candidate to the normal publisher without skipping any
   validation. The staging helper deliberately does no GIF decode or publication.

Index paths are relative to the original client report directory. Rebase paths
only after verifying their SHA values. The original failed staging and previous
review archives are preserved as history, not marked approved for publication.
No hundreds-of-megabytes GIF set is duplicated here. Narrow Git attributes retain
the archived sources and JSON byte-for-byte on any checkout platform.
