# Stripe payment acceptance without a subscription

**20 November 2026; unreleased ZiloMentor Pro 0.1.2.**
The present manual QA tests synthetic Stripe checkout request construction,
nonce checks, amount/currency validation, and the isolated WooCommerce BACS
journey. **They do not establish real Stripe acceptance, webhook or refund
behaviour.** No live customer data or payment provider secret is needed for
this acceptance test.

## No-cost, no-registration sandbox option

Stripe officially supports **claimable sandboxes** as of November 2026.
An up-to-date Stripe CLI can create a sandbox with real *test-mode* API keys
without a pre-existing Stripe account:

```sh
stripe sandbox create --email OWNER_APPROVED_EMAIL --non-interactive
```

The supplied email is used in any subsequent claim process. The owner must
choose and approve the email. Do **not** infer an address from somebody's Git
profile, another site, or project correspondence, and do not run this action
without the owner's authorisation. Do not paste the resulting API keys or
claim URL into chat, GitHub, log archives, test reports or cPanel.

Stripe's documentation says an unclaimed sandbox **expires after seven days**.
After claiming it, access can be retained under an account. This does not
create a recurring WordPress plugin fee or require GitHub Actions. The keys
are saved in the local CLI profile; run the CLI only on a disposable, trusted
test machine with restricted file permissions. `--from-git` is also
available but deliberately **not** recommended here because it silently
selects personal identity metadata.

Official sources:

- https://docs.stripe.com/cli/sandbox
- https://docs.stripe.com/sandboxes
- https://stripe.dev/blog/claimable-sandboxes-frictionless-stripe-accounts-for-agents

## Safe ZiloMentor acceptance plan

1. Create a disposable Stripe sandbox **only with an approved email**. Confirm
   the returned key is test-mode/restricted (`rkcs_test_`, `sk_test_` or a
   documented equivalent); never substitute a live `sk_live_` key.
2. Use **only a separately deployed disposable WordPress and WooCommerce**
   installation with fake customers/products, a private Docker network and
   webserver/browser smoke tests. Keep all production Stripe settings untouched.
3. Configure a ZiloMentor Stripe widget with sandbox mode, a genuine sandbox
   key and a known synthetic amount and currency. Verify an actual Checkout
   Session is created server-side and cannot be controlled by submitted
   amount, quantity, tax, shipping, currency, widget ID or external return URL.
4. Exercise successful and declined cards with Stripe's published **test
   values**, duplicate submissions, expired sessions, webhook signature
   verification, refund APIs (if the sandbox key permits them), and replay/
   idempotency scenarios. Test zero-decimal currencies and minimum amounts.
5. Capture **redacted** request IDs, expected/actual outcomes, WordPress/PHP
   errors, and a key-free security summary. Revoke/expire the sandbox when
   the tests finish. Do not publish a signed release until this passes.

The claimable CLI's restricted sandbox key may have permissions unlike a
permanent account's API keys. Verify supported operations rather than
assuming that Checkout, refunds, webhooks and WooCommerce plugins share the
same permissions. If claimable sandbox features are limited, use an
owner-controlled general Stripe sandbox instead (also not a plugin
subscription).

**Status: plan only.** No sandbox was provisioned, no email sent, no test
API key stored, and no payment attempted during this review.
