# ZiloMentor Pro

**An independently maintained, GPL-licensed Elementor Pro compatibility fork for WordPress.**

> **Development preview, v0.1.0. Not production-ready.** The compatibility work
> has passed structural and isolated WordPress/Fiore activation and widget tests,
> but not full browser, forms-delivery, checkout or payment tests.

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
| Theme Builder, dynamic tags and product widgets | 196 widgets registered; ACF text rendered in a real Elementor Heading; other dynamic tags and templates pending |
| Vamtam Fiore integration on ItzyBitzyWorkshop | Isolated plugin activation passed on PHP 8.4/8.5; visual tests pending |
| WordPress plugin path elementor-pro/elementor-pro.php | Provided when staging ZIP is installed |
| WordPress editing and responsive layouts | Front-end Chromium DOM passed at two sizes; authenticated editor shell and preview load, but its panel controls remain empty even with ZiloMentor disabled; editing and visual fidelity pending |
| WooCommerce cart, checkout and payments | Synthetic session and cart shortcode both work; page template omits shortcode output even without ZiloMentor Pro; payment tests pending |
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

The synthetic editor shell, preview frame and Elementor JavaScript initialized.
In the restricted staging environment the panel controls remained empty
**in both configurations**, so actual editing/saving is not verified.
The temporary editor token is randomly generated per QA invocation and
does not provide access to the production website.

This copies only allowlisted WordPress core files and the required installed
plugin/theme source into a disposable environment. It never copies the live
wp-config.php, uploads, users, database or orders. Temporary containers use
a private Docker network with no host ports. The fixture prevents real email
from being sent, and no payments are processed. The isolated cart-page markup test currently
fails with and without ZiloMentor Pro, so full storefront QA still blocks release.

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
