# ZiloMentor Pro release gates and remaining blockers

**Audit date: 20 November 2026**  
**Production:** Itzy Bitzy Workshop runs ZiloMentor Pro 0.1.1, independently
installed as `zilomentor-pro/elementor-pro.php`. It remains a limited
owner-authorised beta.  
**Development:** 0.1.2 is an unreleased, unsigned candidate on draft PR #1.
No GitHub Actions, subscriptions, automatically applied updates, live payment
operations, customer database mutations or operational signing keys were used.

This list is canonical until every criterion has been genuinely verified.
Do not replace open boxes with 100% claims or install the candidate simply
because its synthetic tests pass. GitHub Issues are disabled in this
repository, so blockers are tracked in this version-controlled document.

## Critical dependency: untrusted 4.4.1 package is NOT source evidence

The previously quarantined package claiming to be official Elementor Pro
4.4.1 contains inserted fake licence data, altered licence HTTP responses,
and a third-party template download link over plain HTTP with disabled TLS
verification; its readme references an unauthorised distribution site.
**Do not install, trust, diff for vendor patch parity, or redistribute it.**

The live version was restored to byte-verified 0.1.1 with no matching
malicious hostnames in its code, WP options, posts or cron. This does not
prove the old code never executed or made network requests. Quarantine
evidence is retained outside webroot. Full analysis:
`docs/UNTRUSTED-PLUGIN-INCIDENT.md`.

## 1. Independent official Elementor Pro 4.4.1 security review

- [ ] Obtain an authentic, lawfully accessible Pro 4.4.1 source diff or vetted
  community update; avoid cracked, redistributed or untrusted vendor ZIPs.
- [ ] Audit PHP, JavaScript, REST, CSS and Atomic elements across attributes,
  template permissions, ownership and data handling, not just version labels.
- [ ] Reconcile applicable historical advisories and CVEs with exact code-path
  tests. CVE-2026-32475 empty-first/second-executable Form upload regression
  was added to the synthetic suite.
- [ ] Review security-sensitive forms/submissions, notes, assets, global widgets,
  MCP abilities and all anonymous AJAX paths, including access to private posts.
- [ ] Obtain an independent code/security review; document every unresolved
  upstream difference. Source scanner and smoke tests alone cannot prove parity.

Official changelog: https://elementor.com/pro/changelog/  
Public upstream source: https://github.com/proelements/proelements

## 2. Offline Ed25519 release signing and supported update channel

- [ ] Owner creates and securely backs up a private signing key **offline**
  on a personally controlled computer, never the VPS, chat, GitHub or CI.
- [ ] Public verification key is fingerprint-verified out of band and copied
  only into the owner-controlled private deployment directory.
- [ ] Rebuild the final tracked-source ZIP from the approved exact Git SHA,
  verify file count/hash, sign its manifest offline, and reject tampering.
- [x] Implement a read-only, HTTPS-only, GitHub Releases signed asset
  downloader with pinned Ed25519 PUBLIC key, exact ZIP/manifest validation,
  temporary owner-only private staging and no WordPress install. Initial
  no-network adversarial regression **12/12 passed**, without Actions or fees.
  See docs/SIGNED-GITHUB-RELEASE-FEED.md.
- [ ] Owner privately signs, approves and **publishes a genuine release**
  through GitHub Releases; test the real online feed, including allowed
  GitHub asset redirects and current rate-limit behaviour.
- [ ] Test key rotation, revocation, expiry and complete rollback.
- [ ] Keep production WordPress and WP Toolkit automatic ZiloMentor updates
  disabled until all the release gates are approved.

Procedure: `docs/OFFLINE-RELEASE-SIGNING.md`.

## 3. Payment-provider sandbox

Read-only live inspection showed **no enabled WooCommerce payment gateway**
and **no configured Elementor Stripe test/live secret keys**. These
conditions do not allow a real provider sandbox checkout.

- [ ] Owner enables a provider's official test mode / provides test-only
  credentials in disposable WordPress, not the live shop.
- [ ] Verify authorised amounts, currency minor-unit rounding, shipping/taxes,
  rejected caller-supplied prices/return URLs, idempotent duplicate attempts,
  declined/failure recovery, callback signatures, refunds and charge records.
- [ ] Test authenticated/unauthed roles, invalid nonces and unpublished
  Stripe-button documents without touching real customer or order data.
- [ ] Capture repeatable provider-sandbox evidence. Synthetic BACS checkout and
  Stripe request validation unit tests are not sufficient.

## 4. Editor and real-world file compatibility

- [ ] Validate the Pro Form repeater UI and all actions, popup editing and
  persistence, history undo/redo, dynamic conditions, Nav Menu and Posts
  controls, responsive style persistence, keyboard/screen-reader access.
- [ ] Test real, legally supplied sample PDF, DOCX, XLSX, ODT, audio and video
  files, including common MIME aliases. The new strict content gate can reject
  special-purpose types that previously passed based on extension alone.
- [ ] Test image ZIP/PHAR polyglots and executable multi-file upload bypass
  fixtures in a **disposable** WordPress instance.
- [ ] Confirm Nginx and Apache actually prevent script execution from
  `wp-content/uploads/`, set download-only/no-sniff protections when serving
  Form uploads, and avoid relying solely on .htaccess under Nginx.
- [ ] Repeat desktop/mobile pixel-level comparisons, browser JS and asset
  checks, WooCommerce cart/checkout, PHP8.4/8.5 and synthetic online test
  before any controlled production update.

## What is already verified

- [x] Independent plugin basename deployed live with verified 1,419-file
  0.1.1 package and original appearance retained.
- [x] Version 0.1.1 has external MU vendor-update guard, Fiore early
  bootstrap and owner-only file rollback.
- [x] 0.1.2 development has tests for upload type/content validation,
  private Posts-widget visibility, role permissions and Stripe request
  validation with no live payment transaction.
- [x] Signed GitHub Releases *staging-only* client passes 12 synthetic
  signature/tamper/expiry/host/permission tests; it never enables
  WordPress automatic updates or installs anything.
- [x] Staging signed-manifest format, SHA256-locked manual installer and
  migration rollback covered by synthetic tests.
- [x] Manual isolated browser, WordPress and PHP suites use no GitHub Actions.
- [x] Stable private backups of the live 0.1.1 beta retained outside webroot.

Full source evidence: `docs/SECURITY-REVIEW-2026-11-19.md` and
`docs/INDEPENDENT-PLUGIN-IDENTITY.md`.
