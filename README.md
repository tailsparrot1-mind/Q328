# VKUS — Q328 master repository

Q328 is the canonical continuation point for Vkus development.

## Contents
- `app-source/` — pinned submodule of `tailsparrot1-mind/vkus--3.17-button` at `3afe7b837fe311d6d3252ffa0cab5af6e9f0ca32`. Includes the complete native app tree, local SQLite marketplace implementation, assets, tests and CI workflows.
- `project-docs/` — pinned submodule of `tailsparrot1-mind/Vkus-Development` at `4377c91ab7e8ab2e8e3941db2a73e5b031dad9b0`. Includes the latest project passport, Store and historical package materials.
- `cloud-marketplace-pr/` — pinned to the open cloud-marketplace PR head `6325c6e6edee9a05c729a68a719d5d0634d4bd8d`; kept separate because PR #2 is not merged.
- `docs/PROJECT_PASSPORT_Vkus_v2.0.md` — current audited passport copied into Q328.
- `store/` — copied Store README and both HTML variants.
- `infrastructure/SUPABASE_AND_PAYMENTS.md` — concise Frankfurt DB and payment inventory.
- `infrastructure/supabase/` — detailed schema/migration snapshot and source of the two deployed Edge Functions (no secrets).
- `Q328_MIGRATION_MANIFEST.md` — provenance, version checkpoints, checksums, evidence and outstanding work.

## Clone all source trees
```bash
git clone --recurse-submodules https://github.com/tailsparrot1-mind/Q328.git
```

## 3.28 build artifact
The original 3.28 application ZIP, launch screenshot and checksum manifest have already been imported into `recovered-builds/3.28/` and verified. The manual Actions workflow **Verify Vkus 3.28 artifact** rechecks the files and ZIP checksum; it does not download or import the source artifact again. The original source artifact expires 2027-02-12.

## Important
- Do not recreate/reset the existing Frankfurt Supabase project.
- Do not commit secrets, tokens, session files or service-role keys.
- The cloud marketplace is a separate open PR; real two-user testing remains outstanding.
- Taplink webhook exists, but Robokassa is not connected and payments are not production-ready.

## Vkus 3.28 recovered build

The imported application ZIP, launch screenshot, SHA-256 manifest and source provenance are stored in `recovered-builds/3.28/`. The workflow `.github/workflows/import-vkus-328-artifact.yml` is now verification-only: it checks that the files exist and that the ZIP checksum matches the manifest.
