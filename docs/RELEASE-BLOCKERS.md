# ZiloMentor Pro release gates and remaining blockers

### Latest comprehensive manual QA (20 November 2026)

The **unreleased 0.1.2 source commit**
`1ce553b9d010eb9f93e66bdec71225a8c6b029b4` completed the complete
manual suite on the disposable WordPress/Fiore/WooCommerce/Nginx/PHP-FPM
stack. **87 of 87 integration checks passed**, including all three real
anonymous HTTP Form rejections (draft, private and password-protected
documents), a valid published Form submission, browser popups,
Nginx attachment/no-sniff and executable extension denial, PHP 8.4/8.5
syntax matrices and local signed-manifest/manual-swap regressions.
No GitHub Actions, customer payment, live database or live plugin change
was involved. The branch gained only documentation after this test.
This result is an acceptance *preview*, not proof of official Elementor
Pro 4.4.1 patch parity, an independent security audit or live-vhost safety.


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
  temporary owner-only private staging and no WordPress install. No-network
  adversarial regression **14/14 passed**, without Actions or fees.
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


## Targeted icon archive, import cleanup and PHP upload-shape hardening (20 November 2026)

The **unreleased 0.1.2 development branch** adds further controls beyond the
previous 87/87 acceptance preview. The inherited custom-icon uploader no longer
attempts to unlink a path supplied as a client filename; it requires a valid ZIP,
limits archive and extracted sizes/entry count/compression ratio, rejects unsafe
and executable multi-extension entries (including symlinks), and removes the
server-side ZIP in its cleanup path. Its import rollback and normal delete
handlers now require the saved icon directory to be a real, non-symlink direct
child of the configured icon storage root. Details and caveats:
[ICON-ARCHIVE-SECURITY.md](ICON-ARCHIVE-SECURITY.md).

A disposable WordPress runtime identified a PHP fatal from malformed
nested `$_FILES` names reaching WordPress's string filename sanitiser. The
shared helper now validates and recursively sanitises multi-upload filenames
without changing the matching temporary-file indices. Regressions also cover
valid multi-file structure and malformed arrays. A missing global WP_Post now
safely short-circuits the Posts Full Content skin.

**QA environment correction:** the previously cached PHP-FPM images lacked
`ZipArchive`. Real Office/icon ZIP tests were therefore incomplete despite
earlier green results. A new QA-only `zmp-php84-zip-qa:local` image has been
manually built with the tracked `tools/docker/Dockerfile.qa-php84-zip`;
the isolated runner now refuses to start when its PHP image lacks ZipArchive.
The focused isolated runtime check at source SHA
`011f72b46d3ff971f5fa5e2d6b5e0b340c4d64b6` passed with the
ZIP-enabled image. Later test-only additions for multi-file names, archive
symlinks, and preflight assertions must be covered by the final full-suite
source-SHA check before promoting any release.

**Live Apache read-only inspection:** both HTTP/HTTPS vhosts use the expected
site document root and PHP-FPM; `httpd -t` reported `Syntax OK`, with
`headers`, `authz_core` and `proxy_fcgi` modules loaded and general
AllowOverride rules. This is not a physical upload-directory execution
probe, and the Apache and Nginx live-policy gate remains unchecked.

## What is already verified

- [x] Independent plugin basename deployed live with verified 1,419-file
  0.1.1 package and original appearance retained.
- [x] Version 0.1.1 has external MU vendor-update guard, Fiore early
  bootstrap and owner-only file rollback.
- [x] 0.1.2 development has tests for upload type/content validation,
  private Posts-widget visibility, role permissions and Stripe request
  validation with no live payment transaction.
- [x] Signed GitHub Releases *staging-only* client passes 14 synthetic
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
- [x] Fresh **0.1.2 development** isolated WordPress/Fiore/WooCommerce
  integration test on 20 November 2026 passed **80/80** assertions in
  disposable private Nginx/PHP-FPM + MariaDB with no live database,
  customers or payment provider. Includes independent plugin identity,
  theme/Popup conditions, read-only popup browser interactions,
  Form/REST/Stripe security, ACF, custom attributes, menu, Posts,
  WooCommerce cart/AJAX/guest checkout with **offline synthetic BACS**
  and upload execution restrictions. Run used `--plugin-folder zilomentor-pro`
  and `--frontend-playwright-image haven-browser-qa:1.62.1`.
  Both PHP 8.4/8.5 syntax matrices passed. This is **not** a live paid
  transaction or a replacement for 4.4.1 vendor security parity.
- [x] Read-only sensitive-key signature scan of the development checkout
  found **no PEM private-key blocks, Stripe `sk_live_`/`sk_test_` secrets
  or GitHub personal-token signatures** on 20 November. This is a
  limited heuristic, not a complete historical secret scan or proof that
  no key was ever exposed. Owner's real signing key must still be created
  offline and never committed.
- [x] Research confirmed Stripe's new **no-registration, no-subscription
  claimable sandbox** can provide genuine test keys through `stripe
  sandbox create --email OWNER_APPROVED_EMAIL`. It expires after seven
  days unless claimed. Setup requires an explicit owner-approved email;
  no external Stripe account/sandbox/key was created. Acceptance plan:
  [STRIPE-CLAIMABLE-SANDBOX-QA.md](STRIPE-CLAIMABLE-SANDBOX-QA.md).
  **The real provider-backed payment test remains unchecked.**
- [x] **0.1.2 development** adds a shared published/document-editor
  authorization check for anonymous classic and Atomic Form target IDs,
  restricting classic Form dynamic `queried_id` context and embedded
  `templateID` access as well. The new role-based
  `tests/runtime_form_document_visibility.php` fixture checks missing,
  malformed, draft, private, password-protected and published posts.
  It is intended to run only in the disposable WordPress test site,
  **not** against production forms. Independent live-form preview
  and anti-spam compatibility acceptance remain open.
- [x] **0.1.2 development** bounds Word/Excel/PowerPoint/OpenDocument ZIP
  entry count, per-entry/aggregate expanded bytes, compression ratio and
  traversal/absolute entry names. Synthetic high-compression DOCX and
  traversal fixtures were added; independent MIME/real-document compatibility
  samples are still required.
- [x] **0.1.2 development** classic and Atomic Form upload handlers create
  executable-extension denial and download-only/no-sniff Apache rules for
  new Form upload directories. Runtime checks exercise both writers and
  preservation of owner-customised rules. The actual production Apache/Nginx
  effective-policy and physical uploaded-file tests remain open.
- [x] **0.1.2 development** Form-submission MCP read/write and WooCommerce
  settings abilities now check the original capability policy inside
  `execute()` too, protecting direct callers outside the registry.
  Low-privilege direct-execution cases are in the disposable REST/MCP test.
- [x] Stable private backups of the live 0.1.1 beta retained outside webroot.

Full source evidence: `docs/SECURITY-REVIEW-2026-11-19.md` and
`docs/INDEPENDENT-PLUGIN-IDENTITY.md`.
