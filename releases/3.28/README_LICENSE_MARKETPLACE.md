# Vkus 3.28 — License Store + Marketplace Role Gate

This is the continuation checkpoint for the Vkus 3.28 desktop build.

## Build delivered
- Archive: `Vkus_3.28_License_and_Marketplace.zip`
- SHA-256: `PLACEHOLDER`
- Base candidate: GitHub Actions run 43752802702, artifact 14176793865 (`Vkus-3.28-Marketplace-Candidate`).
- Base source branch: `feature/vkus-328-marketplace-board`.

## Included integration
1. **License Store** — a sidebar item opens the current hosted Store page in the system default browser:
   https://raw.githack.com/tailsparrot1-mind/Vkus-Development/VKUS/Vkus_Store_PC/index_logo_fullscreen.html
   Payment and license issuance are not represented as implemented.
2. **Marketplace role gate** — the Marketplace board opens behind a full-window role-selection screen. It uses the approved `marketplace_role_gate.png` artwork, shows no Vkus sidebar on the gate, and maps transparent click regions only to the visible `Соискатель` and `Рекламодатель` cards. The selected role is carried into Supabase registration; existing accounts can sign in from the selected-role registration screen.

## Verification
- Python compile check: passed.
- ZIP integrity check: passed.
- UI smoke test under Xvfb with a stub Supabase client: passed; opening the Marketplace creates the gate and clicking the first role card opens the registration form.
- Live Supabase registration, email confirmation, and two-user listing/response flow: not run in this build environment.
- Full application launch with Selenium/VK integration: not run; Selenium was unavailable in the environment.

## Continuation rule
Use this checkpoint as the base for subsequent Vkus work. Do not revert to the older drawn role selector, and do not remove the Store sidebar entry. Keep the Store payment flow explicitly marked as unavailable until the payment backend is completed.
