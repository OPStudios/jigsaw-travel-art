# Approved refined completion method

The user approved the exact level-1 GIF identified in the preserved provenance as the motion reference, requested this method for all 120 scenes, and subsequently authorized implementation of the reviewed set with the coordinated level-43 source repair. Earlier review evidence retains its original approval status.

Complete original authoring archive: `review-set-0475c07d4cceb946`.

Current coordinated repair and replay-provenance binding: [rules-provenance-043-9f68a0bf7b873b2e](rules-provenance-043-9f68a0bf7b873b2e/README.md). The repaired picture/GIF and all 119 other GIFs are unchanged from their reviewed bytes. Original revision-3 piece measurements and geometry provenance remain exact; fresh artwork measurements are retained separately as QA evidence.

[View the exact approved tea animation](review-set-0475c07d4cceb946/approved-reference/level-001.gif) (4,406,079 bytes; SHA-256 `1542f4938ad508fd465a3d4b5c81a38a0db92259a550b909c65de080fb1bf45d`). This is the user-approved later refinement and is retained as the visual reference for future animation work.

The archive preserves final per-scene profiles, independent review decisions and corrections, exact code/input capsules, original approved prototype sources/masks, source-bound final GIF identities, download totals, and known visual defects. Only the exact approved tea reference GIF is preserved here; the other generated GIFs remain in the client review output.

Reproduce with the client `tools/completion_gif_refined/encode_batch.py`, the immutable source catalogue and objects, this art repository, Pillow 12.3.0, NumPy, and the explicit Gifsicle 1.93 binary identified by hash in each source capsule. Verify the source hashes before use. To replay an older capsule, reconstruct its source files under their recorded `tools`-relative paths; filenames in each capsule retain exact original bytes. Rebase only global `profiles.reviewSources[].path` values to this archive's `review-overrides/` files while retaining and checking their SHA-256 values; per-scene profile data must remain unchanged. Supply the original source catalogue with its object directory through the CLI. Level 1 reuses the exact preserved approved reference GIF, verified by SHA. The reviewed level 3 output remains in the client review output with its original source/mask capsule preserved here.

Each GIF is limited to 5,000,000 bytes, 75 frames of 40 ms, 255 painted colors, and final 105% zoom. Still-image delivery/compression requirements remain unchanged. Source snapshots use a narrow Git byte-preservation rule so platform line endings cannot invalidate recorded hashes.

The original review set records level 43's pre-existing rosemary stem gap. The subsequent [source repair](source-repair-043-bd0a67c9ae6720a4/README.md) translated the unchanged painted cutout onto its supporting branch in both the still and GIF; independent actual-frame review confirmed the contact. Its first metadata draft failed the native rule gate, and the current replay-provenance binding above resolves that failure without changing the reviewed pixels. Historical review and rejected staging records remain intact.

No CDN upload, backend deployment, native build, commit, or push is performed by these offline authoring tools.
