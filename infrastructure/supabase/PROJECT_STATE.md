# Supabase technical state — Q328 snapshot

Read-only capture taken 2026-11-15. No database changes were made.

## Project
- Name: Vkus Marketplace
- Ref: `tynutsraotlptyznbpfc`
- Region: `eu-central-1` (Frankfurt)
- PostgreSQL 17.11
- Status: `ACTIVE_HEALTHY`
- API URL: `https://tynutsraotlptyznbpfc.supabase.co`

## Applied migrations
| Version | Migration |
|---|---|
| 20261114190915 | create_marketplace_core |
| 20261114190926 | index_marketplace_response_sender |
| 20261115001503 | create_vkus_billing_core |
| 20261115001521 | enforce_vkus_license_plan_prices |
| 20261115001541 | add_verified_billing_identity_map |
| 20261115001554 | add_encrypted_license_delivery_queue |
| 20261115001605 | prepare_taplink_license_order_delivery |
| 20261115002041 | secure_license_delivery_claim_state |
| 20261115002229 | scope_payment_id_uniqueness_by_provider |
| 20261115002306 | add_payment_manual_review_queue |
| 20261115002323 | make_provider_payment_unique_index_inferable |

## Public tables
Marketplace: `marketplace_profiles`, `marketplace_listings`, `marketplace_responses`.
Billing/licensing: `vkus_billing_identities`, `vkus_license_orders`, `vkus_licenses`, `vkus_payment_events`, `vkus_license_delivery`, `vkus_payment_review_queue`.

RLS enabled on every listed table. All had zero rows at capture time. No user data dump is included.

## Edge Functions
- `taplink-payment-webhook`: ACTIVE, version 9, verify_jwt=false; validates Taplink HMAC signature internally.
- `activate-vkus-license`: ACTIVE, version 1, verify_jwt=false; validates Supabase Bearer session internally.

The source snapshots under `functions/` were fetched from the currently deployed function versions. They are documentation/source copies only; do not redeploy without review.

## Secret names only
`TAPLINK_WEBHOOK_SECRET`, `LICENSE_ENCRYPTION_KEY`, `RESEND_API_KEY`, `LICENSE_EMAIL_FROM`, Supabase URL and server-side secret/publishable key settings. No values are stored here.

## Payment status
Taplink webhook exists. Robokassa implementation was not found in the audited source. The Store says payment buttons do not create live orders. No completed real payment was confirmed. Do not describe billing as production-ready.
