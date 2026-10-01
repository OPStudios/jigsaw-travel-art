# AH-001 painted scene source archive

This source archive preserves the unique paintings, five original cutouts per scene, complete image-generation prompts, unchanged generator originals, exact composition manifests, extraction provenance and implementation review evidence.

The current archive contains completed scenes 1–40. Scenes 41–120 are still being authored. No catalogue has been published from this archive.

Runtime content is delivered through immutable content objects. Raw source paintings are deliberately excluded from the mobile client export and its EAS source bundle. The corresponding consumer repository is jigsaw-travel-client; implementation ledger: docs/qa/AH-001-Implementation-2026-09-30.md.

Each scene folder contains background.png, master.png, part-1.png through part-5.png, and source/. Files in source/ retain original generator outputs. Historical authoring records retain their original workstation paths; the portable archive paths and exact SHA256 values are recorded in archive-index-first-40.json. Evidence manifests use scene-relative runtime image paths and can be ingested with this directory as the art root. Exact prompts are retained under evidence/ and inside each scene's complete manifest.

GPU motion proof metadata is retained in evidence/; full rendered PNG frame sequences remain in the consumer repository's local reports directory. This is implementation/desktop-renderer review, not PM approval or physical-phone certification.
