# Vkus 3.28 — License Store + Marketplace baseline

This branch is the continuation baseline for subsequent Vkus development.

## Integrated
- Main sidebar entry **«Купить лицензию»** opens the current hosted license storefront in the system browser.
- **Биржа → Доска объявлений** opens the full-window Marketplace role gate.
- Role gate uses the approved artwork asset `vkus/assets/marketplace_role_gate.png`, without the Vkus sidebar or header.
- The two visible role cards have independent scale-aware hitboxes: **Соискатель** and **Рекламодатель**.
- Selecting a role opens the corresponding registration/login screen; the role is written to Supabase user metadata.

## Build
- Immutable recovered Vkus 3.28 base: `recovered-builds/3.28/Vkus_3.28_NO_SPLASH.zip`.
- Final integration patch: `recovered-builds/3.28/Vkus_3.28_License_and_Marketplace_PATCH.tar.gz`.
- Reproducible builder: `tools/build_vkus_328_marketplace.py`.
- CI workflow: `.github/workflows/build-vkus-328-marketplace.yml`.
- CI produces the final ZIP, SHA-256 checksum, launch screenshots, and a permanent GitHub Release.

## Local verification
- Python compilation passed.
- 17 unit/integration tests passed.
- Xvfb UI smoke test passed for the role gate, outside-hitbox rejection, and both role-specific registration screens.
- ZIP integrity passed.
- Local archive SHA-256: `95842b9b97b00882507301d0195fd57057b4117055acfef25a9588f940bc4241`.

## Explicit limitations
- Store payment processing and automatic license issuance are not implemented.
- Live Supabase email confirmation/session persistence and a complete two-user listing/response flow were not verified against the live project.
- Full VK/Selenium workflow was not run in this environment.

**Future development must start from this branch and preserve both integrations and the approved role-gate artwork.**
