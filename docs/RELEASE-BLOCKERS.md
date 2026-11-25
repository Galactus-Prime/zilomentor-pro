# ZiloMentor Pro release gates and remaining blockers

### Full 104/104 integration and modern IcoMoon work (25 November 2026)

Exact revision `d47b9852a610952eb933e8079ac310197281f306` passed
104/104 full disposable WordPress integration observations (301.07
seconds, exit 0), including genuine Fontello import/delete and actual
Elementor Icon widget desktop/mobile Chromium rendering. Local WOFF2
loaded, zero page errors and zero failed font requests. All previous
forms, WooCommerce, security and Apache/Nginx checks passed; cleanup
confirmed. This is pre-modern-IcoMoon source evidence.

A genuine modern beta IcoMoon download was produced using a self-authored
star SVG in a fresh public generator browser session, without login,
subscription or hosting. Original ZIP SHA256
`39474db6e4549190e9a62774fc05dd3ceff016c1c399088f372ccce67cfb12fa`
retained privately. The actual output contains root *.icomoon.json,
glyphs[].extras, font/style.css, font/fonts and a separate svg folder.
Its WOFF2 reference points to a missing file, with WOFF/TTF/OTF present.
The adapter at `ce4d24cbcc25bcd567b56913f89ba152b683383a` accepts this
format, validates project/glyph names and integer Unicode scalar values,
checks basic font magic signatures and one font stem, generates a
local-only glyph stylesheet, scopes publication to the font subtree,
retains conventional license text, and retains legacy importer support.
It does not execute or publish the original SVG/demo exports or project
JSON. Basic signatures are not comprehensive binary font validation.
On both PHP 8.4/8.5, the old handler was shown not to recognise the real
archive; the new handler passed genuine acceptance and rejection of
invalid codepoint, malformed glyph name, and invalid font magic (8/8
targeted assertions with minimal WP stubs). PHP syntax also passed.
Actual importer/publication/deletion regression and pinned archive
staging added at `48affddbd39b91ced046bc56e223ad6ea68e590f`; runtime
verification and browser rendering of the modern pack remain open.
The modern beta adapter deliberately accepts a conservative named
single-font subset, not all modern export variants. Independent audit,
Fontastic genuine exports, accessibility, payment, signing and
production acceptance remain open. No GitHub Actions or paid services.




### Recursive asset publication verified (25 November 2026)

Exact source `4eee6637e70d5b848e860285f7c1b8d5b93f4510` passed 29/29
runtime observations (exit 0, 132.66 seconds), including the expanded
nested publication regression and all seven genuine Fontello extraction,
import and deletion assertions. Disposable WordPress/database/network
cleaned. The next opt-in browser test seeds an actual Elementor Icon
widget using the pinned genuine pack and checks desktop/mobile glyph
and WOFF2 loading; integration at `d47b9852a610952eb933e8079ac310197281f306`
and manual runner option at `c1f2ff21fbfc16a64430556ea5c1eabc02a013e9`.
PHP fixture syntax and Python runner syntax/argument checks passed.
The new browser test is not yet certified. Full frontend integration,
modern IcoMoon/Fontastic, independent security audit, genuine payments,
operational signing and production acceptance remain separate gates.

### 25 November 2026: genuine archive acceptance and recursive publication

Exact revision `ce3d94832bc5580832fd6afccd6360c264829fb9` passed
**29/29** disposable WordPress runtime observations (122.1 seconds,
exit 0), including all seven genuine Fontello archive assertions:
ZIP extraction, importer acceptance, CSS/WOFF2 publication, sanitized
SVG, license preservation, attachment creation, and scoped deletion.
The environment was cleaned. Browser glyph rendering remains open.

Further review reproduced deep nested-directory publication of demo HTML,
double-extension executable names and unsupported binary assets in a
minimal filesystem stub (baseline 1/4 assertions passed on PHP 8.4 and
8.5). Recursive file-by-file publication at `4570c3fc91b4b9489939244f2cf409f273a49edc`
passed 4/4 on each PHP version and retained legitimate nested WOFF2.
The disposable WordPress regression was extended at
`4eee6637e70d5b848e860285f7c1b8d5b93f4510`; its runtime validation
is not yet certified. ZIP extraction and CSS/SVG checks remain in place.
No production modifications, independent audit, or release approval.

### Comprehensive integration rerun (24 November 2026, retrieved 25 November)

Exact source `55875d6f5d6075a9a5ecd3b9cb13cb0cb748aa85` passed **102/102**
disposable WordPress integration observations (exit 0, 313.7 seconds).
WordPress 7.1.5, free Elementor 4.4.1, WooCommerce 11.3, Fiore,
Nginx/PHP-FPM, real disposable Apache and Chromium frontend checks.
All 26 genuine-format integrity/acceptance assertions passed, eight
HTTP multipart scenarios passed, and Chromium Popup checks had zero
page errors and zero failed local requests. Synthetic guest BACS order
persisted on hold with no payment transaction. Disposable database,
site and network cleaned. No real payment or email was sent.
This exact revision includes the legacy JSON metadata fixes, but predates
the genuine Fontello export normalization at `958e1a1`. The subsequent
runtime regression and full acceptance remain separate gates.

### Additional exact-source manual release QA (24 November 2026)

On exact source SHA `49d92f89fb4eeff871fef88248c6ea1facd799a6`, the
complete non-WordPress manual release suite passed (exit 0) on existing
QA infrastructure in a detached temporary Git worktree. PHP 8.4 and 8.5
each linted 952 PHP files and passed 16/16 isolated legacy icon metadata
regressions, now required by the manual runner's offline Docker matrix.
Static checks, 9 installer/rollback, 3 migration, 1 archive hygiene,
4 manifest, 16 signed feed/key rotation and 2 reduced-motion tests passed.
The unsigned staging-only archive contained 1,435 files, 3,614,888 bytes,
SHA256 `20682fbe08ec5f7ed12991a93d5b47e3845b7fd4ffdc46bfab8b77f8ca6e0b68`.
Temporary checkout/archive removed after verification; no release was
published. No production WordPress or full browser integration tests were
run on this SHA. The 102/102 WordPress result below remains evidence for
its earlier exact SHA only. All operational signing, payment, external
review and genuine export gates remain open. No GitHub Actions used.

### Latest comprehensive manual QA (23 November 2026)

The **unreleased ZiloMentor Pro 0.1.2** exact tested code SHA
`8590da23aa7b48622cd0b46aad5bf63829c85e74`
completed the manually invoked **102/102 disposable WordPress
integration checks** (exit 0), including new strict SVG/CSS custom
icon pack validation and independent Fontello/IcoMoon format fixtures.
The stack used WordPress 7.1.5, free Elementor 4.4.1,
Fiore, WooCommerce 11.3, Nginx/PHP-FPM, a real disposable
loopback Apache 2.4 server and Chromium.

**New security assertions** include valid local CSS/WOFF/legacy SVG
font acceptance; denial of remote CSS imports, obfuscated
CSS url() and @import functions, traversal, nonexistent and
external font files, active SVG script/foreignObject/event/style
attributes, external XML stylesheet processing instructions and
unsafe XML declarations. A real importer-manager regression confirms
a malicious SVG pack is rejected **before any public files are
copied**. Fontastic class-prefix/family parsing no longer
greedily captures subsequent quoted strings. Two separate self-authored
Fontello and IcoMoon source structures retain fonts and CSS, build
valid icon configuration and do not publish demo HTML.

The suite also passed 13 independently authored real
Office/ODF/PDF/audio/video/image validation fixtures,
eight anonymous **real HTTP multipart** Form uploads,
attach-only Email action with no-delivery interception/cleanup,
private Form visibility tests, malformed ZIP defense,
Chromium Popup behaviour and synthetic offline WooCommerce guest
checkout. PHP **8.4 and 8.5** syntax matrices,
static/security checks, offline signed-manifest simulations,
rollback and package-hygiene checks passed.

The **exact tested staging-only ZIP** comprised **1,435 files**,
**3,611,110 bytes**, SHA256
`3c66237b3f83fb8484c734260f7bae6df144c5fa4f8a55fcf26092a78f72a708`.
The archive was **not owner-signed, published, merged, installed or
approved for production**. No GitHub Actions, subscriptions,
real payments, outbound mail, customer files or live WP DB
modifications were used. Later documentation-only commits are
not included in this exact-SHA ZIP. A final approved ZIP must be
rebuilt, reverified and signed from a frozen source SHA.

A separate full **real editor/browser suite** passed (exit 0)
on `46ec6c2e446c151dcd374fbad24423edc65cfff5`,
including Heading editing, History Undo/Redo, Pro Form
repeater fields and form name, Theme Header, Popup,
Nav Menu/Posts and Desktop/Tablet/Mobile switching with
independent database/frontend checks. Another 16/16
no-network **ephemeral-key** Ed25519 simulation passed on
`82d1a99847d39e1907c8633039fd535e359cd1f5`
including synthetic key rotation and revocation.
No operational signing key exists.

**Still open:** real independently vetted vendor-exported icon
archives and security audit; lawfully accessible official
Elementor Pro 4.4.1 patch/source parity; full PHP/JS/REST/CSS
audit; owner-controlled offline signing and publication;
legitimate Stripe sandbox payment/refund/webhook QA;
production Apache/Nginx upload-vhost checks; SMTP
deliverability; WCAG, real-device and broad editor
visual acceptance. Targeted synthetic tests do not
constitute these approvals.

**Audit date: 23 November 2026**  
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
- [x] **Offline simulated** key rotation, emergency trust-anchor
  revocation and signature expiry rejection passed 16/16 tests with
  throwaway keys. Prior manual rollback simulation also passed;
  neither required GitHub Actions or a subscription.
- [ ] Verify **operational** key rotation/revocation, expiry and
  rollback against a genuinely owner-approved public trust anchor and
  signed published release. No operational private key exists yet.
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

- [x] **Representative real editor-browser input and persistence**:
  Pro Form repeater field label and Form name, Heading edit/History
  Undo and Redo, Theme Builder Header and Popup template editing
  with page-scoped conditions, Nav Menu and Posts widget,
  Desktop/Tablet/Mobile device switcher, independent WP database
  save verification and frontend-render verification all passed.
  Exact editor source SHA `46ec6c2e`; see
  docs/EDITOR-ACCEPTANCE-2026-11-21.md.
- [ ] Exhaustive Form actions, keyboard and assistive-technology
  accessibility, desktop/mobile visual and pixel-level acceptance,
  real-device checks, dynamic third-party conditions and full
  responsive style persistence are still required.
  Representative editor smoke passes are **not** WCAG certification.
- [x] Test self-authored **genuine** DOCX, XLSX, ODT, ODS, ODP, PDF,
  JPEG, PNG, PCM WAV and MP4 samples produced by independent libraries;
  verify SHA256, document reopenability and safe upload content acceptance
  within disposable WordPress. Reject fake PDF, script text and valid
  PNG-with-embedded-ZIP. Exact source-SHA **99/99** run passed on
  21 November 2026. See docs/REAL-FORMAT-UPLOAD-QA.md.
- [x] Exercise **eight actual anonymous HTTP multipart** submissions
  through Nginx/PHP-FPM, WordPress admin-ajax and classic Form widget:
  genuine PDF link saved with CSPRNG filename, DOCX attach-only
  intercepted at real Email action with SHA256 and cleanup verified,
  two valid files persisted, PHP/forged PDF/PNG-ZIP/empty-first-file
  bypass and excessive file count all rejected. No outbound email.
  See docs/HTTP-MULTIPART-FORM-QA.md.
- [ ] Expand real-world file compatibility to vendor-exported
  Office/ODF variants, MIME aliases, encrypted/large/macro documents,
  true email deliverability and all third-party Form actions.
  The current real samples and intercepted mail confirm representative
  content validation and multipart processing only.
- [x] **Custom icon pack public assets**: self-authored Fontastic
  with valid CSS/WOFF survives publishing without transferring
  temporary root/nested untrusted HTML; corrupt icon names/lists
  return `WP_Error` instead of crashing; per-instance Fontastic
  pack metadata cache is isolated. Exact **100/100** full suite
  included `runtime_icon_public_html_safety.php`.
  See docs/ICON-PUBLIC-ASSET-REVIEW.md.
- [x] **Targeted, fail-closed custom icon CSS/SVG pre-publication
  validation**: real local CSS font references and inert SVG webfont
  XML accepted; remote CSS imports/URL schemes, CSS hex escapes/
  comments, traversal, active SVG markup, external stylesheet
  processing instructions and XXE doctype/entities rejected.
  Actual `Custom_Icons` importer denies a malicious source before
  public file creation. Self-authored Fontello and IcoMoon pack
  structures still import and preserve CSS/fonts. Exact-SHA
  **102/102** full run passed on 23 November. See
  docs/ICON-PUBLIC-ASSET-REVIEW.md.
- [ ] **Independent SVG/CSS audit and real third-party pack
  compatibility**: test authenticated, lawfully obtained Fontello,
  IcoMoon and Fontastic exported archives, real font glyph rendering,
  SVG sprite differences, unusual CSS, MIME types and file headers.
  Strict synthetic validation is not a comprehensive security proof
  and may reject uncommon valid packages.
- [x] Test representative image ZIP/PHAR polyglots and executable
  empty-first/second-file upload bypass fixtures in **disposable** WordPress.
  Included synthetic and independently generated polyglot checks passed.
- [x] Test Nginx/PHP-FPM executable extension restrictions and attachment/
  no-sniff headers in disposable containers, plus *actual Apache 2.4*
  parsing of generated `.htaccess` via a disposable loopback HTTP server
  (8/8 Apache HTTP cases). See docs/FORM-ATTACHMENT-APACHE-QA.md.
- [ ] Confirm **production** cPanel Apache virtual-host inheritance and
  physical Form upload directory HTTP execution/headers after a
  controlled, owner-authorised 0.1.2 promotion. A localhost Apache test
  cannot prove effective live-vhost restrictions.
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

## 21 November follow-up: classic Form mail and genuine files

- [x] Classic Form Email attachments now require a real, non-symlink,
  regular file directly inside the configured protected Form upload
  directory for **both** attaching to mail and deleting Attach-only
  files. Owner-defined upload-path filters are preserved. Direct
  reflection and negative path/symlink/malformed-record regressions
  passed in disposable WordPress.
- [x] Real standalone Apache parsed the `.htaccess` emitted by the
  disposable Form initializer. It served an ordinary download with
  `attachment` / `nosniff` / `no-store` and denied PHP, PHP8,
  multi-extension PHP/PHTML/PHAR/Python/SHTML with HTTP **403**.
  The true production cPanel vhost remains a separate open gate.
- [x] 13 self-authored real-format fixtures were generated via
  python-docx, openpyxl, odfpy, ReportLab, Pillow, WAV and FFmpeg,
  with verified package structure and SHA256. Genuine content was
  accepted for 10 safe formats; all 3 disguised/script/polyglot
  variants were rejected. No fees, third-party file downloads,
  customer data, live email or unsafe `/tmp` execution were used;
  Python library dependencies ran in isolated Docker.
- [x] November official free Elementor and historical Pro advisory
  scopes were reviewed and recorded at
  [CVE-CROSSCHECK-2026-11-21.md](CVE-CROSSCHECK-2026-11-21.md).
  Neither official free-plugin patch status nor a specific prior CVE
  test establishes complete ZiloMentor/Pro 4.4.1 vendor parity.

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
