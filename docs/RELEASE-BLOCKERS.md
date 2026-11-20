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
  no-network adversarial regression **13/13 passed**, without Actions or fees.
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
- [x] **0.1.2 development fix** for inherited Motion Effects crash with
  Reduced Motion enabled. The handler deliberately skips `initEffects()`
  when `prefers-reduced-motion: reduce` matches, but later resize callbacks
  still entered `toggle()` and dereferenced uninitialized `this.effects`.
  Both readable and shipped minified frontend assets now guard `toggle()`
  and `onElementChange()` when initialization was skipped. A read-only
  live-site browser prepatch reproduced two desktop `translateX` errors
  with Reduced Motion and zero under normal motion. The exact patched
  development bundle, substituted **only inside private browser contexts**,
  passed 4/4 desktop/mobile × reduced/normal cases: zero JS errors, existing
  85/89 widgets intact, and the normal desktop's 12 motion effects present.
  Two source regression tests and JS syntax checks passed. Similar upstream
  report: https://github.com/elementor/elementor/issues/34257.
  **Live 0.1.1 remains unchanged**: repeat normal browser QA after a later
  authorised, signed promotion.
- [x] Corrected a false-positive "broken image" count in the read-only
  public canary: the source-less `<img width="900" height="600">` is
  inside the custom `#ibw-unified-mega-menu`, whose computed visibility
  was **hidden**. It generates **no failed HTTP image request**. A
  subsequent **read-only mouse hover on Shop** made the mega-menu visible,
  populated its image source (`/wp-content/uploads/2026/09/ibw-menu/ibw-menu-shop-clean.webp`)
  and revealed 12 menu links. The canary now separately reports
  `brokenImages:0` and `emptySourceImages:1` before interaction at
  desktop and mobile. This is a QA classification correction, **not
  a change to live menu rendering**.


## What is already verified

- [x] Independent plugin basename deployed live with verified 1,419-file
  0.1.1 package and original appearance retained.
- [x] Version 0.1.1 has external MU vendor-update guard, Fiore early
  bootstrap and owner-only file rollback.
- [x] 0.1.2 development has tests for upload type/content validation,
  private Posts-widget visibility, role permissions and Stripe request
  validation with no live payment transaction.
- [x] Signed GitHub Releases *staging-only* client passes 13 synthetic
  signature/tamper/expiry/host/permission tests; it never enables
  WordPress automatic updates or installs anything.
- [x] Staging signed-manifest format, SHA256-locked manual installer and
  migration rollback covered by synthetic tests.
- [x] Manual isolated browser, WordPress and PHP suites use no GitHub Actions.
- [x] Removed the inherited tag-triggered GitHub Actions publisher from
  `master` in commit `f3d80e4`; the development branch has no workflows.
  This removes the automatic release job, independently of account settings.
- [x] 0.1.2 manual deployment and manifest builder reject ZIP central-directory
  expansion bombs and unsafe paths **before** archive decompression.
  New regression tests proved that `testzip()` is not reached for forged
  600 MiB entries. On a disposable QA host with PHP 8.4/Sodium,
  13/13 signed staging, 9/9 manual swap and 4/4 manifest tests passed.
  No production plugin, payment, customer or database record was changed.
- [x] Stable private backups of the live 0.1.1 beta retained outside webroot.

Full source evidence: `docs/SECURITY-REVIEW-2026-11-19.md` and
`docs/INDEPENDENT-PLUGIN-IDENTITY.md`.
