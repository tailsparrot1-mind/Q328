# Vkus infrastructure and payment status (non-secret)

## Existing Supabase project
- Name: Vkus Marketplace
- Project ref: `tynutsraotlptyznbpfc`
- Region: `eu-central-1` (Frankfurt)
- Status at last audit: `ACTIVE_HEALTHY`
- PostgreSQL 17
- API URL: `https://tynutsraotlptyznbpfc.supabase.co`
- Created: 2026-11-14 17:40:05 UTC

**Do not recreate, reset, migrate or delete this project** during repository consolidation.

### Tables from last audit
Marketplace: `marketplace_profiles`, `marketplace_listings`, `marketplace_responses`.

Billing/licensing: `vkus_billing_identities`, `vkus_license_orders`, `vkus_licenses`, `vkus_payment_events`, `vkus_license_delivery`, `vkus_payment_review_queue`.

Last audit: 11 migrations; 0 rows in listed tables; 10 marketplace RLS policies; billing-table RLS enabled.

## Edge Functions
- `taplink-payment-webhook`: active version 9.
- `activate-vkus-license`: active version 1.

Taplink webhook code includes signature verification, payment/refund handling, license creation and email via Resend. Secret names only (values intentionally omitted):
- `TAPLINK_WEBHOOK_SECRET`
- `LICENSE_ENCRYPTION_KEY`
- `RESEND_API_KEY`
- `LICENSE_EMAIL_FROM`
- Supabase URL and server-side key variables.

Never commit secret values. Configure them in Supabase secrets / GitHub Actions secrets.

## Payment status
- No Robokassa webhook or payment integration was found in audited code.
- Store README says Robokassa is not connected; tariff selection does not create an order/payment.
- No real payment confirmed; billing tables were empty at last audit.
- Previously agreed Robokassa + Supabase architecture is not yet implemented end-to-end. Treat payment and license delivery as incomplete until a test transaction and webhook-to-license flow are verified.

## Cloud marketplace
PR #2: https://github.com/tailsparrot1-mind/vkus--3.17-button/pull/2
- Supabase REST client, auth, listing CRUD, search/filter/pagination, responses and owner inbox are described in the PR.
- CI reports 12 client tests and UI smoke checks.
- Not verified: real two-user signup/login and response exchange.
- Session is memory-only; SQLite-to-cloud sync is absent; moderation/anti-spam remain incomplete.
