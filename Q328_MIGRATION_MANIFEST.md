# Q328 migration manifest

Created: 2026-11-15
Target: https://github.com/tailsparrot1-mind/Q328

## Source snapshots
- Native app + local marketplace: `tailsparrot1-mind/vkus--3.17-button`, branch `main`, commit `3afe7b837fe311d6d3252ffa0cab5af6e9f0ca32`.
- Project passport + Store: `tailsparrot1-mind/Vkus-Development`, branch `VKUS`, commit `4377c91ab7e8ab2e8e3941db2a73e5b031dad9b0`.
- Cloud marketplace: open PR #2, head `6325c6e6edee9a05c729a68a719d5d0634d4bd8d`, deliberately separate from the mainline.

These exact snapshots are attached as Git submodules: `app-source`, `project-docs`, `cloud-marketplace-pr`. Clone with `git clone --recurse-submodules https://github.com/tailsparrot1-mind/Q328.git`. Submodules preserve the full upstream trees, including binary assets.

## 3.28 build evidence
- Actions run: `43623882237`
- Artifact ID: `14124759940`
- Artifact name: `Vkus-3.28-build-and-launch-evidence`
- Created 2026-11-14 17:57 UTC; expires 2027-02-12 17:57 UTC.
- ZIP: `Vkus_3.28_NO_SPLASH.zip`, 7,613,720 bytes.
- SHA-256: `1ac3ac52afbcf4b4584df57af8d4fa1b12a69aed5978680f18d7864b2cc3e414`.
- ZIP integrity check passed.
- Launch screenshot: `Vkus_3.28_LAUNCH.png`, 1672×941.
- Screenshot label reads 3.27 despite 3.28 ZIP name. A separate visible-label update followed later; this mismatch is explicitly retained, not hidden.
- Artifact download page: https://github.com/tailsparrot1-mind/vkus--3.17-button/actions/runs/43623882237

## Changes after 3.28 artifact
- `80ccf51b1972e3a20af5ee52989bf657bca9ee1f`: local SQLite marketplace.
- `e7f4e3678a8a7819e2b1bd4ec553480fc17cb8b1`: marketplace CI screenshot capture.
- `3afe7b837fe311d6d3252ffa0cab5af6e9f0ca32`: filters/layout and dark Combobox fix.
- Local module: `vkus/exchange_marketplace.py`; local DB runtime path: `data/marketplace.db`.
- Features: «Ищу» / «Предлагаю», category, city, price/budget, author/contact, filtering, Active/Completed/Archive.

## Infrastructure and outstanding work
See `infrastructure/SUPABASE_AND_PAYMENTS.md`. Existing Frankfurt Supabase project is not copied or recreated. Taplink webhook exists; Robokassa is not connected. Real two-user marketplace flow and real payment/license flow still need manual end-to-end tests.

## Security
No API keys, tokens, webhook secrets, encryption keys, session files or service-role keys belong in this repository.


## Supabase source snapshot added to Q328
The deployed source of `taplink-payment-webhook` (version 9) and `activate-vkus-license` (version 1) was retrieved from the existing Frankfurt project and committed under `infrastructure/supabase/functions/`. A read-only technical state capture, including all 11 applied migration identifiers, table inventory, RLS state and environment-variable names, is under `infrastructure/supabase/PROJECT_STATE.md`. No secret values or database rows were exported, and no database operation was performed.

## 3.28 artifact import into Q328
- Imported files: `recovered-builds/3.28/Vkus_3.28_NO_SPLASH.zip`, `recovered-builds/3.28/Vkus_3.28_LAUNCH.png`, `recovered-builds/3.28/SHA256SUMS.txt`, and `recovered-builds/3.28/ARTIFACT_SOURCE.txt`.
- Import workflow run: `43735569619` — completed successfully; download, file-presence checks, SHA-256 verification and commit steps all passed.
- Q328 import commit: `29e9f70eed53ad798e5e91ce2d993bba7dd030b8` (`Import verified Vkus 3.28 build and launch evidence`).
- The import bootstrap was replaced afterward with a manual verification-only workflow; no temporary signed download URL remains in the repository.
