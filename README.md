# ZiloMentor Pro

**An independently maintained, GPL-licensed Elementor Pro compatibility fork for WordPress.**

> **Limited live beta, v0.1.1, not a general production release.** Itzy Bitzy
> Workshop now runs the independently identified plugin at
> `zilomentor-pro/elementor-pro.php`, with free Elementor 4.4.1. The 20 November
> 2026 guarded folder migration passed desktop/mobile visual acceptance, kept
> private rollback files, and required no WooCommerce data rollback. Payment
> gateways and the full paid Elementor security patchset remain uncertified.

ZiloMentor Pro is a fork of [PRO Elements](https://github.com/proelements/proelements),
which in turn incorporates GPL-licensed code originally developed by Elementor Ltd.
The aim is to preserve Elementor Pro's widely used widget identifiers, PHP classes,
hooks and template formats so compatible third-party WordPress themes can continue
working without editing the themes. Actual compatibility varies by theme and
plugin version and must be tested.

## What it is and is not

- **Is:** an independent, open-source compatibility-focused plugin derived from
  PRO Elements 4.4.0, retaining relevant Elementor Pro interfaces.
- **Is not:** Elementor Pro, an official Elementor product, an activated Elementor
  subscription, or access to Elementor cloud services, AI, commercial templates,
  proprietary support or remotely licensed features.
- **Requirement:** the free Elementor plugin must also be installed.
- **Do not run alongside Elementor Pro or PRO Elements.** They share PHP identifiers.
- **Safe starting point:** use disposable staging QA before any new installation
  or upgrade. One explicitly authorised live beta is under controlled testing.

## Compatibility

| Area | Status |
| --- | --- |
| Original Elementor Pro PHP namespace and hooks | Retained from upstream; static check passes |
| Theme Builder, dynamic tags and product widgets | 196 widgets registered; ACF text renders in a real Elementor Heading; synthetic Header conditions and Popup Page Load, On Scroll and Exit Intent browser triggers passed in isolated Fiore; other template/trigger combinations pending |
| Vamtam Fiore integration on ItzyBitzyWorkshop | Live independently named ZiloMentor beta **0.1.1** alongside free Elementor 4.4.1. Migrated desktop visual delta **0.0035 mean RGB**, mobile **0.0**, with **85/89 widgets** and no new browser errors. The header early-bootstrap adapter preserves Vamtam callback order. Other templates and gateway journeys remain uncertified |
| Independent WordPress plugin identity | Installed live under `zilomentor-pro/elementor-pro.php` to avoid WP Toolkit's false Elementor Pro slug mapping. Compatible `ElementorPro` PHP classes remain. Legacy layout available only as an explicit test build |
| WordPress editing and responsive layouts | 156 editor controls vs 81 free; isolated Heading, Pro Form and Theme Builder Header edits use real Publish/Update and independent database/conditional-render checks. Desktop → tablet (768px) → mobile (360px) → desktop editor switching passed; additional workflows pending |
| WooCommerce cart, checkout and payments | 55/55 isolated HTTP/integration checks passed; registered Cart, AJAX mini-cart, guest checkout and synthetic offline bank-transfer order creation verified; card gateways, shipping and tax scenarios remain untested |
| Release management | Original/proprietary updater disabled. Independent Ed25519-signed **manual** 0.1.2 candidate and ZIP/rollback tests implemented, with private owner-only release backups. No operational signing key or auto-update feed is live |

The initial source tracks PRO Elements **v4.4.0** at commit
[58d52e0](https://github.com/proelements/proelements/commit/58d52e0f10640088aa179e28b40b161c33c57de4).
The public fork retains its original upstream commit history.

## Independent live plugin identity (20 November 2026)

After a cPanel WP Toolkit collision between ZiloMentor and the official
`elementor-pro` slug, the owner-approved beta was migrated using a verified
**unchanged 0.1.1 ZIP** into the independent WordPress plugin directory
`zilomentor-pro/`. A separate external MU release guard protects both
plugin names from WordPress-managed vendor replacements, and a conditional MU
bootstrap restores the Elementor/Fiore initialization order. The first trial
had a genuine desktop header regression, which was immediately rolled back
and corrected. An intermediate mobile difference was independently shown to
persist after rollback, proving it was not caused by plugin identity.

The final controlled live migration passed the strict visual gate using a
current restored-site baseline (desktop **0.0035** average RGB delta, mobile
**0.0000**, at 1366x768 and 390x844). Homepage, shop, cart, checkout and a
product page returned HTTP 200 and no longer reference old plugin assets.
Refreshed WP Toolkit lists **ZiloMentor Pro 0.1.1** under `zilomentor-pro`,
not as official Elementor Pro, with no vendor update offer. Backup, file-only
rollback and a private SQL snapshot were preserved.

**The code is still 0.1.1**, based on PRO Elements 4.4.0 with targeted
attributes fixes; this identity migration is not an automatic 4.4.1 patch.
See [independent migration evidence](docs/INDEPENDENT-PLUGIN-IDENTITY.md)
and [WP Toolkit collision investigation](docs/WPTOOLKIT-UPDATE-COLLISION.md).

## Unreleased 0.1.2: additional Form upload security checks

The development branch now validates the **actual file contents** of
anonymous uploads in both classic Elementor Form and Atomic Form widgets.
Administrators cannot make an unsafe file acceptable simply by listing
its extension. The shared implementation in `core/utils.php` requires a
registered WordPress MIME, inspects content with FileInfo, applies PDF,
Office, image and audio/video checks and denies disguised executable/script
formats. Atomic Form failure cleanup is restricted to its own upload
directory and cannot unlink arbitrary supplied paths.

Disposable WordPress tests confirmed valid sample files and rejection of
PHP disguised as PDF/Office, arbitrary Office ZIP files, scripts in text
and `.php8` extensions. **44/44 initial focused editor/runtime checks**, **68/68 complete
isolated frontend/popup/WooCommerce checks**, **53/53 combined editor
publishing/responsive checks**, and a further **38/38 role/REST-focused
isolated runtime checks** passed. The REST tests checked icon/SVG route
permission callbacks for guest, subscriber, contributor and editor roles,
without dispatching any privileged write operation.

**Compatibility caution:** a special-purpose CAD or other unusual extension
previously accepted via a Form field alone can now be rejected. Register
custom types using WordPress's `upload_mimes` filter and test their actual
MIME/content before enabling this unreleased candidate. File validation is
not a replacement for malware scanning.

The verified live site **still runs 0.1.1**, unchanged by this security
development. Signing and independent updates remain manual; see the
[offline signing and rollback procedure](docs/OFFLINE-RELEASE-SIGNING.md).
**No automatic update service or operational private signing key has
been installed.**

## Current beta deployment and limitations (19 November 2026)

The owner explicitly authorised testing on `https://itzybitzyworkshop.co.uk/`.
A private database snapshot and exact original Elementor Pro 4.4.0 plugin files
were preserved **outside public_html** before a checksum-verified, cPanel-owner
deployment. The original Pro plugin was replaced in-place with ZiloMentor
0.1.0 at the compatible `elementor-pro/elementor-pro.php` basename, then
upgraded through the owner-only, SHA256-verified manual updater to **0.1.1**.
The previous 0.1.0 and original Pro plugin code remain available for rollback. Free
Elementor 4.4.1, WooCommerce, Fiore and caching plugins remained active.

- WordPress bootstrap passed Core, Pro compatibility, WooCommerce and fork
  identity checks; 213 Elementor widgets registered in the real site runtime.
- Read-only public homepage tests at desktop **1366×768** and mobile
  **390×844** yielded **pixel-identical before/after screenshots** and unchanged
  widget types/counts (85 desktop, 89 mobile). The pre-existing single broken
  image and desktop JavaScript error count of two were unchanged.
- Shop, guest Cart, guest Checkout and a product page returned HTTP 200 and
  contained WooCommerce markup, with no observed PHP fatal errors. **No live
  payment, order, customer edit or outbound form submission was performed.**
- A private `tools/manual_live_swap.py` provides explicit SHA256 checks,
  read-only preflight, `--apply`, and owner-only `--rollback` /
  `--rollback-to-official` routes. Its synthetic installation, upgrade,
  malformed archive, downgrade and rollback tests run locally with no Actions.
  **Never automatically restore a WooCommerce database snapshot**, which
  could erase orders placed since the backup.

**Security release gate:** Elementor's official Pro 4.4.1 (16 November 2026)
lists improvements to attributes security. ZiloMentor **0.1.1** includes
an independently tested, narrow Atomic Attributes transformer hardening:
HTML attribute values are escaped, attribute names validated, unsafe event
handlers / `srcdoc` / inline `style` blocked and unsafe URL protocols rejected.
The isolated security runtime verified 10 adversarial and valid attribute
cases; the updated plugin passed 47/47 combined editor checks and PHP 8.4/8.5
syntax checks across 933 files. This does **not** establish complete parity
with the official 4.4.1 patchset: the rest of the source is still based on
community PRO Elements 4.4.0. A trusted,
reviewed upstream update and security audit remain necessary before a general
release. Do not install untrusted or so-called nulled ZIP archives. WordPress
recognises the fork's separate Update URI, but **there is no unattended online
release channel or cryptographically signed update manifest yet**.

**0.1.1 post-upgrade canary:** the public homepage at desktop 1366×768 and
mobile 390×844 returned HTTP 200, with identical widget types/counts,
unchanged error counts, and **pixel-identical screenshots** to the baseline
original Elementor Pro installation (mean RGB difference 0.0). No real
checkout, live mail or payment transactions were attempted.

### Optional manual release and rollback

These commands require the site's actual filesystem owner, a private
non-web-accessible backup directory, and a trusted release ZIP. Do **not**
point them at a production site merely to test the instructions.

    python3 tools/manual_live_swap.py --site /path/to/wp --backup-dir /private/backup --zip /path/to/staging.zip --sha256 FULL_64_CHARACTER_SHA256
    python3 tools/manual_live_swap.py --site /path/to/wp --backup-dir /private/backup --zip /path/to/staging.zip --sha256 FULL_64_CHARACTER_SHA256 --apply
    python3 tools/manual_live_swap.py --site /path/to/wp --backup-dir /private/backup --rollback
    python3 tools/manual_live_swap.py --site /path/to/wp --backup-dir /private/backup --rollback-to-official

A successful production WP bootstrap alone does **not** mean a store is fully
validated. Run the opt-in visual canary before/after manually, test representative
templates and payment integrations in a sandbox, and maintain a tested rollback
path and recent independent backups.

## 0.1.2 candidate: signed manual releases and additional security review

The **development branch** has moved to **0.1.2**, while Itzy Bitzy Workshop
continues to run the **verified live 0.1.1 beta**. Do not confuse the two.
The unreleased changes validate legacy custom attribute names, exclude
event-handling attributes and unsafe URL schemes on Elementor wrappers, and
avoid a null-post dereference during Posts widget pagination. The legacy
custom-attribute injection regression is exercised against a real synthetic
Heading in disposable WordPress/Fiore, not only a PHP unit mock.

From **0.1.2 onwards**, the safe manual deployment script refuses updates
without a valid, non-expired **Ed25519-signed manifest** independently
describing the *exact release ZIP* (version, filename, byte size, SHA256 and
plugin basename). A private trust anchor stored outside the webroot must
already be provisioned by the site owner; a supplied public key is never
taken from the ZIP or from the untrusted update manifest. It also rejects
downgrades, zip traversal, dangerous runtime files and oversized archives.
These protections are checked in synthetic installer/security tests.

**Manual, offline-key release workflow (no GitHub Actions or hosted CI):**

1. On a trusted **offline** machine with PHP Sodium, create and securely
   preserve a keypair **once** with
   `php tools/release_signature.php generate /secure/private-signing-key.b64 /secure/public-release-key.b64`.
   Never generate or store the private signing key on the production VPS,
   under `public_html`, in Git, or inside an installable plugin ZIP.
2. Build and thoroughly test the candidate on your disposable QA host:
   `python3 tools/run_manual_checks.py`. Generate the exact JSON with
   `python3 tools/create_release_manifest.py --zip /path/to/zilomentor-pro-compat-0.1.2-staging-only.zip --out /path/to/stable.json`.
3. Copy the manifest onto the offline signing machine and sign its **exact
   bytes**:
   `php tools/release_signature.php sign /path/to/stable.json /secure/private-signing-key.b64 /path/to/stable.json.sig`.
   Keep the private key offline. Verify key ownership/fingerprint through
   an independent trusted channel and place **only** the public key in the
   site's private backup directory.
4. With a fresh protected WordPress backup and all release gates passed,
   run a read-only preflight using the matching ZIP, full SHA256,
   `--signed-manifest /path/to/stable.json`,
   `--signature /path/to/stable.json.sig`,
   `--trusted-public-key /private/backup/public-release-key.b64` and
   `--require-signature`. Explicitly add `--apply` only for an approved
   deployment. The previous release and original Elementor Pro files are
   retained privately for file-only rollback.

The signer refuses to overwrite existing key/signature files and enforces
0600 permissions for private signing keys, refusing to create one in a Git
working tree. This is a **signed, owner-operated manual update pathway**,
not yet a self-hosted automatic update service or public one-click WordPress
updater. There is deliberately **no operational live signing key and no 0.1.2
production deployment** at this stage.

**0.1.2 isolated evidence:** 64/64 frontend/Popup/WooCommerce checks passed
(including a synthetic offline on-hold order). A separate 49/49 authenticated
editor suite passed Heading/Form/conditional Header save/publish and responsive
breakpoint switching. The Posts REST-preview guard was actually exercised,
with zero PHP warnings, and the legacy custom attribute injection regression
passed on rendered HTML. The manual release tests prove unsigned/expired/
modified signatures and unsafe packages are rejected; additional review
of real payment gateways and full official 4.4.1 patch equivalence remains.

## Build and test (development only)

    python3 tools/run_manual_checks.py  # existing Docker/PHP QA host

On the development VM, without Docker/PHP:

    python3 tools/run_manual_checks.py --skip-php

**GitHub Actions is intentionally not used.** Checks run on existing servers;
no hosted GitHub CI minutes or Actions billing are required.

To also test real synthetic WordPress forms, WooCommerce cart sessions and
Fiore templates on your QA host, supply a WordPress source-code location:

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress

To add isolated Chromium front-end DOM checks at desktop and narrow viewports,
using the already-cached browser image on the existing QA server:

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --browser-image mcr.microsoft.com/playwright:v1.63.0-noble

Browser checks verify Elementor headings, form markup and ACF dynamic values
after loading JavaScript. They do not certify visual pixel fidelity, editor
interactions or checkout functionality.

To compare the authenticated Elementor editor with and without ZiloMentor
using locally cached Playwright (no remote browser service):

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --editor-playwright-image haven-browser-qa:1.62.1

In the original single-worker PHP staging environment, editor panel controls
were empty in both configurations during the short observation window.
A private **Nginx 1.29 + PHP 8.4-FPM** multiworker test, with waits for widget
panel population, subsequently loaded **156 controls for ZiloMentor Pro**
and **81 controls for free Elementor**. Both editors reached DOM ready state
complete without JavaScript page errors or local HTTP errors.

To reproduce the faster, more realistic multiworker editor comparison:

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --web-server nginx-fpm --focus editor --editor-playwright-image haven-browser-qa:1.62.1

A separate opt-in **end-to-end synthetic Heading edit-and-save test** passed:
Playwright opened the Heading title control, changed it, clicked Elementor's
actual **Publish** button, and WP-CLI independently verified the new title
persisted in the disposable database.

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --web-server nginx-fpm --focus editor --editor-playwright-image haven-browser-qa:1.62.1 --verify-editor-save

A focused **40/40** isolated test run verified a real Form Name edit, editor
Publish/Update click, persisted Elementor document data and rendered frontend.
A combined **42/42** isolated run also confirmed the Heading and Pro Form can
both be edited and published within one disposable WordPress installation,
with the two saves independently checked through WP-CLI.
Chromium reported one benign `net::ERR_ABORTED` request cancellation, tracked
separately from network and HTTP failures; there were no real local request
failures, page JS errors or HTTP errors.

The separate opt-in **Pro Form editor persistence** check selects only the
synthetic Form widget, changes its Form Name through Elementor's normal editor
panel, uses the actual Publish/Update UI control, then independently checks
the saved WordPress Elementor data and rendered form markup. It requires an
internal Docker test site and a disposable WordPress database; it does not
send mail or edit real content.

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --web-server nginx-fpm --focus editor --editor-playwright-image haven-browser-qa:1.62.1 --verify-editor-form-save

This complements the Heading test but does not certify other Form settings,
repeaters, field validation and action integrations, popup editing, visual
fidelity, checkout or external payment functionality. No production site is
modified. All containers and their private Docker network are removed by
the harness.

**Theme Builder Header edit/Publish regression:** isolated Chromium selected a
real synthetic Header document Heading, edited its title, clicked Elementor's
Publish button, verified the saved WordPress template data, and verified the
new header appears **only** on the intended page: **40/40 checks passed**.

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --web-server nginx-fpm --focus editor --editor-playwright-image haven-browser-qa:1.62.1 --verify-theme-builder-save

**Responsive editor:** actual Elementor 4.4 device toolbar controls were used
to switch desktop 1140px → tablet 768px → mobile 360px → desktop 1140px,
retaining the Heading and Pro Form: **38/38 isolated checks passed**.

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --web-server nginx-fpm --focus editor --editor-playwright-image haven-browser-qa:1.62.1 --verify-editor-responsive

**Theme Builder / Popup regression:** a disposable Elementor Header and Popup
each use a real saved template and a display condition targeting only one
synthetic page. Both render on that page and are excluded from unrelated
pages. Playwright verifies the Popup opens automatically on page load at
desktop **1366x768** and mobile **390x844**, contains the expected Heading,
and closes successfully. Additional dedicated synthetic pages verify that On Scroll and desktop Exit Intent triggers open their own popups only after the corresponding user interaction, without cross-page leakage. The integrated **61/61** isolated checks passed.

Run the optional no-Actions frontend trigger test with an already-cached
Playwright image:

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --web-server nginx-fpm --frontend-playwright-image haven-browser-qa:1.62.1

This confirms conditional Header rendering, popup open/close, Page Load,
On Scroll and desktop Exit Intent triggers. Other trigger types (click,
inactivity, scroll-to-element and adblock detection), Theme Builder visual accuracy,
editing popup templates, and accessibility are not yet certified.
The temporary editor token is randomly generated per QA invocation and
does not provide access to the production website.

This copies only allowlisted WordPress core files and the required installed
plugin/theme source into a disposable environment. It never copies the live
wp-config.php, uploads, users, database or orders. Temporary containers use
a private Docker network with no host ports. The fixture prevents real email
from being sent, and no payments are processed.

**Important WooCommerce QA setup:** newly installed WooCommerce stores may
enable Coming Soon mode for registered store pages. The disposable test
runner explicitly sets only its **synthetic** storefront to live mode. With
this setting off, the registered Cart page displays the product and form.
A controlled Coming Soon on/off test confirmed that enabling it hides the
registered Cart and disabling it restores it, even with ZiloMentor and
Elementor disabled. **50/50 isolated HTTP/integration checks passed.**
An additional **isolated guest checkout and order-creation test** passed.
The runner uses a separate virtual product, a private guest cookie jar and
WooCommerce's offline bank-transfer method in the disposable database only.
The real wc-ajax=checkout handler returned success and a confirmation
redirect. WP-CLI independently found **one** synthetic order containing the
correct £7.49 item, offline payment method, on-hold status, and **no payment
transaction ID**. All **55/55** HTTP and integration checks passed.

This does not certify external payment gateways, real payments, card handling,
taxes, shipping, refunds or production checkout reliability. All outgoing
WordPress mail is intercepted in the disposable environment, and the checkout
customer uses a reserved .invalid email domain.

Run tests/runtime_bootstrap.php and tests/runtime_widgets.php via WP-CLI
in a disposable staging WordPress installation after activating free
Elementor and ZiloMentor Pro.

The ZIP build uses the elementor-pro/ directory and
elementor-pro/elementor-pro.php entrypoint for interoperability. This is an
implementation detail: the plugin's public name is **ZiloMentor Pro**.

For staging, first back up the WordPress database and files; capture baseline
screenshots; deactivate the current Elementor Pro installation; replace it with
the ZiloMentor Pro staging package; test page templates, forms, dynamic tags,
navigation, WooCommerce and the Elementor editor; then compare logs and
screenshots. **Never overwrite an active production plugin or a live store.**

## Development plan

1. Run PHP 8.4/8.5 syntax checks manually on existing servers, and extend full WordPress integration tests.
2. Add disposable WordPress/Elementor matrix tests and Vamtam Fiore fixtures.
3. Investigate compatibility differences and implement only justified fixes.
4. Introduce a verified update pipeline, security policy and changelog.
5. Publish a release only after end-to-end staging and rollback tests pass.

See [ZILOMENTOR-NOTES.md](ZILOMENTOR-NOTES.md) for the current staging checklist,
[SECURITY.md](SECURITY.md) for security reporting, and
[CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Licence, provenance and trademarks

Distributed under **GPLv3 or (at your option) any later version**, consistent
with the included [licence](license.txt). Copyright notices and attribution to
Elementor Ltd., PRO Elements contributors and ZiloMentor Pro contributors are
retained. Modified source must be identified as modified.

The names **Elementor** and **Elementor Pro** are used solely for compatibility
and attribution; they remain trademarks of their respective owner. ZiloMentor
Pro is **not endorsed, affiliated with, or supported by Elementor Ltd.**
