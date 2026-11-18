# ZiloMentor Pro

**An independently maintained, GPL-licensed Elementor Pro compatibility fork for WordPress.**

> **Development preview, v0.1.0. Not production-ready.** The compatibility work
> has passed structural and isolated WordPress/Fiore activation and widget tests,
> but not production-like visual comparisons, real form delivery, full checkout or payment tests.

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
- **Safe starting point:** test on an isolated WordPress staging site only.

## Compatibility

| Area | Status |
| --- | --- |
| Original Elementor Pro PHP namespace and hooks | Retained from upstream; static check passes |
| Theme Builder, dynamic tags and product widgets | 196 widgets registered; ACF text renders in a real Elementor Heading; synthetic Header conditions and Popup rendering/automatic page-load triggers passed in isolated Fiore; other template/trigger combinations pending |
| Vamtam Fiore integration on ItzyBitzyWorkshop | Isolated plugin activation passed on PHP 8.4/8.5; visual tests pending |
| WordPress plugin path elementor-pro/elementor-pro.php | Provided when staging ZIP is installed |
| WordPress editing and responsive layouts | Browser DOM passed at two sizes; Nginx/PHP-FPM editor panel populated (156 ZiloMentor controls vs 81 free); synthetic Heading title edited with the real Publish button and independently verified in WordPress post meta; pixel fidelity and more editor workflows pending |
| WooCommerce cart, checkout and payments | 55/55 isolated HTTP/integration checks passed; registered Cart, AJAX mini-cart, guest checkout and synthetic offline bank-transfer order creation verified; card gateways, shipping and tax scenarios remain untested |
| Automated updates | Upstream updater disabled; independent signed updater pending |

The initial source tracks PRO Elements **v4.4.0** at commit
[58d52e0](https://github.com/proelements/proelements/commit/58d52e0f10640088aa179e28b40b161c33c57de4).
The public fork retains its original upstream commit history.

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

This does not certify other widget types, popup editing, visual fidelity,
checkout or external payment functionality. No production site is modified.
All containers and their private Docker network are removed by the harness.

**Theme Builder / Popup regression:** a disposable Elementor Header and Popup
each use a real saved template and a display condition targeting only one
synthetic page. Both render on that page and are excluded from unrelated
pages. Playwright verifies the Popup opens automatically on page load at
desktop **1366x768** and mobile **390x844**, contains the expected Heading,
and closes successfully. The integrated **59/59** isolated checks passed.

Run the optional no-Actions frontend trigger test with an already-cached
Playwright image:

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --web-server nginx-fpm --frontend-playwright-image haven-browser-qa:1.62.1

This confirms conditional Header rendering, popup open/close and page-load
triggers. Other display conditions, triggers, Theme Builder visual accuracy,
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
