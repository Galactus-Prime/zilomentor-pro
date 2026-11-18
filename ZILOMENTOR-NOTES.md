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

## Disposable HTTP form and WooCommerce session test (18 November 2026)

A reusable, **local-only** integration runner has been prepared at
tools/qa_isolated_site.py. It requires an explicit WordPress source-code path,
copies allowlisted WordPress core and the Fiore/Vamtam/WooCommerce/Elementor
sources only, and uses a fresh synthetic MariaDB database. No production
wp-config.php, customers, uploads, orders, licence data or database are copied.
The temporary test intercepts all outgoing WordPress mail. Docker's network is
internal and no web ports are published.

Run manually on the existing Docker-enabled QA server:

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress

Observed isolated tests with Elementor 4.4.1, WooCommerce 11.3.0 and Fiore:

- PASS: Real Elementor Form widget renders; synthetic invalid AJAX submission
  is rejected and valid synthetic AJAX submission is accepted.
- PASS: Synthetic WooCommerce product is published/purchasable and HTTP
  product rendering succeeds.
- PASS: After correcting the disposable curl container's private-directory
  permissions, WooCommerce issues its session/cart cookies.
- PASS: A subsequent independent HTTP request confirms the synthetic cart
  contains exactly one product; the AJAX mini-cart fragments include the
  product. Repeated with ZiloMentor Pro deactivated: WooCommerce's cart
  session and fragments still work.
- **OPEN:** The synthetic cart **page HTML** does not display the item,
  despite successful session storage, with or without ZiloMentor Pro and
  with Fiore or the standard Twenty Twenty-Five theme. This is not
  demonstrated to be a ZiloMentor Pro regression. The checkout page
  returns HTTP 200, but a functional checkout is not yet proven.
- All test containers/networks/temp copies are cleaned up; no payments or
  messages are sent; the live website is unchanged.

The isolated HTTP QA command intentionally exits nonzero while this
synthetic cart-page rendering check remains unresolved. Do not mistake
passing session/API tests for full storefront or payment validation.

## ACF dynamic widget and cart shortcode findings (18 November 2026)

Using source-code copies of ACF Pro 6.8.11, Elementor 4.4.1 and Fiore
in private, disposable WordPress/PHP 8.4 staging:

- Elementor's acf-text dynamic tag registered and returned the synthetic
  ACF field value from the current WordPress page.
- A real Elementor Heading widget configured with that dynamic tag
  rendered the synthetic ACF value in the HTTP page output.
- With one synthetic item in WooCommerce's session, an HTTP request
  executed the Cart page's woocommerce_cart shortcode and produced
  4,879 bytes of HTML including the product and a cart form.
  The queried page was correctly recognized as the WooCommerce Cart.
- The normal full-page template omitted that cart content with and
  without ZiloMentor Pro, under both Fiore and Twenty Twenty-Five.
  This is a page rendering discrepancy in the isolated environment,
  **not a demonstrated ZiloMentor Pro regression**.
- All synthetic records/cookies were confined to the private test
  database and network. No live site modification or purchase.

The isolated QA command deliberately exits nonzero while cart page
rendering is unresolved. Do not overstate this as a complete editor,
checkout, payment, ACF field-type or cross-version certification.

## Optional Chromium DOM smoke (18 November 2026)

Using the already cached Playwright Chromium image on the QA VPS, with
only a private Docker network and a synthetic WordPress installation:

- Desktop (1366x768): the browser returned 0 and the DOM contained the
  synthetic Elementor Heading, ACF-generated Heading value and Form widget.
- Narrow viewport (390x844): the same browser DOM checks passed.
- No public network endpoint, paid cloud browser service or GitHub Actions
  was used. The temporary environment was removed after the test.

The above checks confirm browser-level markup is present at both viewport
sizes, **not** pixel-accurate theme fidelity, mobile layout correctness,
Elementor editor functionality, popup behavior or payment flows. The separate
baseline Cart-page rendering issue remains unresolved.

Run on a Docker-enabled QA server using its existing browser image:

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --browser-image mcr.microsoft.com/playwright:v1.63.0-noble

The integration runner still exits nonzero while the synthetic Cart-page
template rendering check fails in the baseline without ZiloMentor Pro.

## Authenticated Elementor editor baseline (18 November 2026)

A synthetic WordPress administrator is authenticated using a random per-run
token inside a temporary **internal-only** Docker network. The token cannot
authenticate any real administrator or access the production site.
The editor and storefront use separate cookie jars.

- Authenticated editor page: HTTP 200, expected Elementor editor page title
  and server-rendered panel markers.
- Bounded Playwright (local image): editor document and preview iframe
  loaded; Elementor editor JavaScript object available; zero page errors.
- **Panel controls: 0 in the observed period**, both with ZiloMentor Pro
  enabled and with it deactivated on exactly the same synthetic Fiore site.
  This is not evidence of a plugin-specific failure. The editor is **not**
  certified for editing or saving.
- The browser blocks external requests, the app panel is still empty, and
  the controlled QA environment may not faithfully reproduce a normal
  internet-connected Elementor editing session.
- The same QA run confirmed guest WooCommerce cookies are independent
  from the temporary editor login; the full synthetic Cart page is still
  missing content with and without ZiloMentor, although its cart API,
  shortcode and WordPress content-filter output contain the product.

Use the existing QA host (no GitHub Actions or paid services):

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --editor-playwright-image haven-browser-qa:1.62.1

The integration test remains a **nonzero** exit until the synthetic cart
page and any optional editor panel parity failures are resolved. A complete
editor interaction/edit/save test and production-like staging visual
comparison remain release blockers.

## Nginx/PHP-FPM editor and WooCommerce comparison (18 November 2026)

The QA runner also supports a fully disposable **Nginx 1.29 + PHP 8.4-FPM**
web stack. It uses locally cached images, **no published ports**, a private
Docker network and a separate synthetic MariaDB. PHP-FPM can process
multiple WordPress/Elementor requests concurrently, unlike the PHP
development server. The only directory made writable to PHP-FPM is the
temporary copy of wp-content. Nothing in the live site's tree is changed.

A first full isolated Nginx/PHP-FPM run passed **42 of 46 HTTP checks**;
the remaining four were the established cart-page rendering discrepancies,
including cases where ZiloMentor was disabled or a default WP theme was used.
The synthetic product remains in session, the shortcode and WordPress
the_content filter render the cart form and item, and ordinary WordPress
pages display their content. The full synthetic cart page still does not.

A focused editor comparison using Playwright and an explicit wait for a
populated widget panel passed **29/29 checks**. On the same synthetic
WordPress installation:

- ZiloMentor enabled: editor panel **156 controls**, 6,472 characters;
  DOM complete, **0** JS page errors, **0** failed local requests,
  **0** local HTTP errors.
- ZiloMentor disabled, free Elementor alone: **81 controls**, 3,558
  characters, DOM complete, no JS or local HTTP errors.
- Both tests used the same isolated Fiore theme, temporary admin login
  and local browser image. A too-early snapshot initially reported only
  six ZiloMentor controls. **Waiting for actual panel population
  resolved that false indication.**

Repeat editor-only comparison, no cloud runner or external services:

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --web-server nginx-fpm --focus editor --editor-playwright-image haven-browser-qa:1.62.1

This validates the editor shell and populated widget panel, but not yet
editing/saving a page, responsive visual fidelity or payment handling.
A read-only Heading selection probe has been added for a subsequent test;
until independently checked, it must not be marked as passed.

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

## Testing without GitHub Actions

This project deliberately uses no GitHub Actions or hosted CI. The inherited
upstream release workflow was removed from the development branch. Run
python3 tools/run_manual_checks.py on an existing Docker-enabled QA server
(with the already-installed PHP 8.4/8.5 images). On the development VM without
Docker, use --skip-php and explicitly treat PHP linting as outstanding until
it is completed on the QA server.

This requires no GitHub-hosted runner minutes. Do not push release tags or
enable the inherited workflow on the untouched upstream-based master branch.
