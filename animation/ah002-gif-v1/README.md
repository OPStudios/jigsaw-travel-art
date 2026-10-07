# AH002 completion GIF authoring

The game consumes actual GIF files containing the painted scene actions and zoom. The CDN publishes immutable GIF bytes; the game does not reconstruct moving cutouts during completion.

`profiles.json` defines one explicit physical action and hinge for each of the 600 existing painted details across 120 scenes. It retains the original source identities, semantic labels and placement anchors. Historical sources use both `anchor.kind` and `anchor.mode`. In particular, `top_left` may specify the sprite rectangle's placement rather than a physical hinge. The separate rig anchor follows the actual painted stem, loop or knot; inspected corrections are retained in `overrides.json`.

Actions include steam rising/dissipating, anchored plants bending, cloth fluttering from its attachment, pendants swinging from their loop, bird/insect wings moving about the body, a perched bird nodding with fixed feet, water reflections rippling, floating leaves bobbing, and small resting details settling. Actual painted source pixels and alpha are deformed offline; no substitute geometric art is drawn. Source placement and original artwork are unchanged.

Every GIF has 75 frames of 40 ms, lasts exactly three seconds, plays once and holds the final 105% view. All five parts return to their original pose. The encoder checks visible part clipping, non-static poses, input identities, exact GIF frame timing and an independent GIF decode. The hard cap is **5,000,000 bytes per file**. The palette retains 255 colors. Encoding starts at 376×450, tries restrained compression, and can use 352×421 or 320×383 rather than add conspicuous sky noise. Every actual output records its chosen dimensions and bytes; one setting is not assumed to fit all levels.

`encoder-source/` is a hash-recorded archival snapshot of the client repository's offline authoring tools. Run the tools from the client repository so they use its current strict source/GIF validators; this archive is not a standalone publisher. `provenance.json` records tool hashes, source catalogue, timing and encoding policy.

Example from the client repository root, using your own explicit art/optimizer paths:

```text
python tools/prototypes/completion_gif/encode_batch.py --catalogue builds/cdn/releases/abd71aee7d39fa611a2ca0f27178b8fd24301b4df871d510e3cbd2db1af846f5.json --art-root <art-repository> --profiles <art-repository>/animation/ah002-gif-v1/profiles.json --gifsicle <gifsicle-1.93> --output reports/gif-completion-final --levels 1-120 --workers 3
```

The process writes one GIF and a detailed receipt per level, a source-bound `index.json`, and a download summary with totals and per-city bytes. GIF binaries are delivery artifacts; they are not bundled into game assets. The package publisher independently verifies the index, each level's unchanged still-image composition identity, every GIF hash, timing and download/memory budgets before publishing immutable objects. The unchanged PNG/WebP quality gates still apply to still images.

Review uses complete scene GIFs at actual board size and multi-frame contacts grouped by city. First-pass experiments remain separate from the final output directory. Reviews only approve the exact final GIF/profile hashes recorded in their evidence.

Publication is on hold: the user explicitly requested review of all 120 actual GIFs before any upload. The local review gallery and its exact GIF identities are the approval set. Local validation or an implementation QA pass is not upload approval.

Level 43 uses an explicitly reviewed camera pivot at [564, 661] instead of [564, 675] in the 1128 x 1350 authoring canvas. This shifts the final framing by only 0.70 source pixel (0.233 pt at 376 px display) and keeps the sage tip visible at 105% zoom. No painted part is moved, and the strict clipping gate remains.

The art repository pins `encoder-source/**` to byte-preserving Git storage (`-text`). Existing `authoring.portable.json` inputs are pinned to CRLF checkouts: all 120 were verified byte-for-byte against their committed LF data normalized to CRLF. This preserves the already recorded raw input hashes on every platform without changing their JSON data or any artwork.
