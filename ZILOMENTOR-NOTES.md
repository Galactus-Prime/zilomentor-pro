# ZiloMentor Pro (pre-release 0.1.0)

Independent GPLv3-or-later derivative of PRO Elements v4.4.0.
Upstream: https://github.com/proelements/proelements
Upstream pinned commit: 58d52e0f10640088aa179e28b40b161c33c57de4

## Goal
Preserve Elementor Pro's PHP classes, widgets, template data, hook identifiers
and standard WordPress plugin basename elementor-pro/elementor-pro.php for
third-party WordPress themes, without modifying those themes.

## Critical limitations
- Prototype only. Static checks are not full WordPress/theme runtime tests.
- Free Elementor must be installed and compatible.
- Only one of Elementor Pro, PRO Elements and ZiloMentor Pro may be active. Never
  install ZiloMentor Pro over a live shop without full backup and rollback plan.
- Does not confer an Elementor subscription, cloud templates, AI, support or
  remotely licensed services. No licence-server impersonation is included.
- The upstream PRO Elements self-updater is disabled to avoid overwriting
  this independently maintained fork. WordPress Update URI is reserved;
  implement a verified release updater before production deployment.
- Keep source copyright and GPL notices, including those in license.txt.
- GitHub: https://github.com/Galactus-Prime/zilomentor-pro (fork exists; local
  ZiloMentor changes require publication to a review branch).

## Verified checks (17 November 2026)

- Upstream source pinned at commit 58d52e0f10640088aa179e28b40b161c33c57de4.
- All 14 static source and Fiore compatibility checks passed.
- Full PHP syntax lint passed on **928/928 files under PHP 8.4**.
- Full PHP syntax lint passed on **928/928 files under PHP 8.5**.
- The first disposable WordPress installation attempt failed at DB connection;
  this was a test harness failure, not a verified plugin defect. Plugin
  activation, Fiore runtime and checkout testing are **still pending**.
- The disposable test containers were cleaned up. The production WooCommerce
  installation, database and Elementor Pro plugin were not modified.
- GitHub repository exists but connector branch creation returns a 403;
  pending additional GitHub write authorisation.

## Test harness and load-order regression

The first isolated WordPress/Fiore/WooCommerce activation test loaded all plugins,
but detected an absent ElementorPro bootstrap: the standard plugin directory
elementor-pro/ is loaded before elementor/ alphabetically. The early
did_action('elementor/loaded') guard returned before free Elementor initialized.
The development fix defers the bootstrap until plugins_loaded.

A disposable staging installation should run the following read-only regression:

    wp eval-file wp-content/plugins/elementor-pro/tests/runtime_bootstrap.php
    wp eval-file wp-content/plugins/elementor-pro/tests/runtime_widgets.php

This test checks the Elementor and ZiloMentor version constants, the
ElementorPro Plugin class, and theme location helper. Repeat on each supported
PHP version and after plugin updates. Never run this against a live shop.

## Isolated Fiore runtime results (18 November 2026)

Using **no production database or configuration**, isolated WordPress was
created from public WordPress core plus the installed site code for free
Elementor 4.4.1, WooCommerce, Fiore and Vamtam Elementor integration.

- **PHP 8.4:** WordPress installation, all plugin/theme activations and
  ZiloMentor Pro bootstrap regression passed.
- **PHP 8.5:** The same read-only bootstrap regression passed.
- **Both versions:** Elementor registered 196 widgets. The form, nav-menu,
  posts, theme-site-logo and WooCommerce menu-cart widgets were present.
- **Both versions:** Vamtam Fiore integration plugin was confirmed active,
  with Elementor Pro compatibility API version 4.4.0.
- All disposable MariaDB/WordPress containers, networks and test files were
  cleaned up. **Live ItzyBitzyWorkshop was unchanged.**

These are WordPress CLI/registry tests, **not** proof that front-end designs,
popup triggering, forms, dynamic tags or WooCommerce payments work end-to-end.

## Synthetic browser-facing HTTP results (18 November 2026)

In a private Docker network with a temporary PHP web server, Fiore,
Vamtam integration, WooCommerce and ZiloMentor Pro:

- A synthetic Elementor page rendered a **heading** and **Form widget** on
  the server (2,500 bytes of widget markup); HTTP page output included
  the heading and was approximately 45 KB.
- Synthetic WooCommerce cart and checkout shortcode pages returned HTML
  (approximately 95 KB each). No checkout transaction or payment executed.
- A synthetic WooCommerce product initially appeared blank to the tester,
  because it requested the numeric post ID without following the
  canonical **HTTP 301 redirect**. The same redirect occurred without
  ZiloMentor Pro and under the standard Twenty Twenty-Five theme.
  Following the redirect returned **HTTP 200** and the expected product
  name. This was a test-harness URL error, not a detected plugin fault.
- The whole source with user-interface brand refinements passed PHP syntax
  checks for **930/930 PHP files** on **PHP 8.4 and PHP 8.5**.
- Test containers, synthetic DB, network and temporary files were removed.

The source retains upstream PRO Elements copyright, attribution, changelog
and compatibility version header where needed; only user-visible product
labels were replaced with ZiloMentor Pro.

**Still unverified:** actual storefront visual fidelity, live templates,
popup triggers, form delivery, dynamic tags, checkout/session behaviour and
payment integrations. Do not deploy this preview to production.

## Suggested validation sequence
1. Install a disposable WordPress 7.1+, Elementor 4.4.x staging environment.
2. Record baseline pages/templates and widgets under genuine Elementor Pro.
3. Back up DB, wp-content and WooCommerce configuration; anonymize customer data.
4. Swap to ZiloMentor Pro only on staging and verify activation, headers, navigation,
   archive/post templates, ACF dynamic tags, popups, forms and WooCommerce views.
5. Check dashboard editor, desktop/mobile responsive views, PHP error logs,
   AJAX, REST API and checkout including payment sandbox.
6. Revert the staging copy after comparison if any functional difference appears.
7. Do not deploy to production until the end-to-end suite passes.
