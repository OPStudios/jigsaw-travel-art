# AH-001 final verified scene archive

This additive archive contains all 120 final authored scenes, 840 runtime PNGs, retained original paintings/atlases/derived alpha sources, exact generation prompts, original specs and compact review evidence. The existing partial `../ah001-v1` archive is preserved.

`complete-scene-manifest.json` is the portable full manifest. Its runtime paths and every `authoring.sources[].path` are relative to this archive root. Master/background/part hashes match the frozen client manifest. Each scene has `source/` and `authoring.portable.json`; `portable-specs/` contains source-path-normalized copies of original specs. Use this directory as the art root and working directory for portable specs.

All copied bytes were read back and SHA-256 verified, and source files were checked for changes during copying. No hardlinks, image retouching or runtime re-encoding were used. `archive-index.json` records every copied path/hash, exact original identity, source mappings, portable spec derivations and any omitted noncompact report. The original full manifest is retained byte-for-byte under `evidence/input-complete-120-scene-manifest.json`.

Historical workstation/generated-image paths remain only as provenance; they are not required runtime or authoring source paths. Approved Art Direction V2 PNGs are copied unchanged under `references/`. Frame-by-frame GPU PNG sequences and .import/.uid files are deliberately excluded. Compact motion proof JSON/logs, review sheets and available GIFs are retained in evidence. Failed/superseded attempts are labelled by their original report paths and do not replace final verified-config evidence.

This archive is internal implementation/desktop-renderer acceptance, not Product Manager approval, publication or physical-phone certification. No git commit or push was performed by the archive operation.
