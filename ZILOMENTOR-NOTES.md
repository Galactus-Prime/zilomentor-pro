# ZiloMentor Pro (pre-release 0.1.0)

Independent GPLv3-or-later derivative of PRO Elements v4.4.0.
Upstream: https://github.com/proelements/proelements
Upstream pinned commit: 58d52e0f10640088aa179e28b40b161c33c57de4

## Goal
Preserve Elementor Pro's PHP classes, widgets, template data, hook identifiers
and standard WordPress plugin basename elementor-pro/elementor-pro.php for
third-party WordPress themes, without modifying those themes.

## Current QA position (19 November 2026)

- The **synthetic Heading edit -> Publish -> database persistence** test
  passed; 32/32 focused checks with the private Nginx/PHP-FPM editor.
- The **registered WooCommerce Cart page now renders correctly** once the
  fresh disposable store is explicitly switched out of Coming Soon mode.
  A second synthetic A/B run reproduced hide/show by toggling Coming Soon;
  the full isolated WooCommerce suite passed **50/50 checks**.
- The earlier cart-page errors documented below are *historical and now
  resolved in the QA harness*, not ZiloMentor plugin defects.
- The synthetic WooCommerce guest BACS checkout created and independently
  verified an on-hold GBP 7.49 order. Real card payments, taxes, shipping,
  notifications and refunds remain unverified.
- Page-scoped Header, automatic Popup Page Load, On Scroll and desktop
  Exit Intent passed in real Chromium against disposable pages: **61/61**
  integrated HTTP/browser/WooCommerce checks and no page JavaScript or
  local HTTP request errors. Theme Builder editing, other trigger types,
  visual fidelity and secure independent updating remain outstanding.
  **No production deployment.**

## Popup On Scroll and Exit Intent browser regression (19 November 2026)

The QA harness seeds three independently conditioned popup templates in a
fresh private WordPress database: Page Load, On Scroll (down 20%) and desktop
Exit Intent. The Scroll target contains disposable tall content; the mouse
pointer leaves the top of a separate Exit target in real Chromium. Neither
popup is activated by a direct API call.

- **61/61 isolated integration checks passed**, including WooCommerce's
  previously verified offline guest checkout and Cart page controls.
- On Scroll and Exit Intent each remained closed before their respective
  browser interaction, then opened with the expected template heading.
- Per-page display conditions excluded each popup from unrelated pages.
- Automatic Page Load popup still opened and closed correctly at desktop
  and mobile sizes; zero browser page errors or failed local requests.
- The PHP 8.4 and PHP 8.5 syntax matrices each parsed **932/932** PHP files.
- A cPanel PHP CLI transient cache race was corrected in the source-copy
  allowlist; the staging ZIP builder now also excludes that cache.
- The temporary Docker network, containers and WordPress database were
  cleaned; no public ports, real payments, customer data or live shop changes.

This validates tested front-end behaviours, not the Popup editor UI,
additional popup triggers, real messages, checkout gateway payments, or
cross-theme visual fidelity.

## Real Pro Form editor save and browser cancellation diagnosis (19 November 2026)

The `--verify-editor-form-save` test exercises a **Pro-only widget** through
the actual Elementor editor, not direct WordPress writes. Playwright selects
the known synthetic Form widget, confirms its initial Form Name, changes the
text in Elementor's panel, observes the name change in the preview and clicks
the real Publish/Update button. Independently, WP-CLI confirms the correct
Form widget's `form_name` persisted in `_elementor_data` without changing
its Submit button text. A separate anonymous HTTP request confirms the new
Form Name appears in rendered markup.

- **40/40** focused editor/runtime/integration checks passed against
  disposable WordPress, Fiore and ZiloMentor Pro on Nginx/PHP 8.4-FPM.
- A further **42/42** combined regression passed: the synthetic Heading and
  Pro Form were both changed using Elementor's real Publish/Update buttons
  and their new values independently confirmed in WordPress, within the
  same isolated WordPress installation. The Form's new name also rendered
  over HTTP. Zero genuine local request, HTTP or JavaScript page errors.
- The initial run saved and rendered the Form correctly but reported one
  browser request failure and therefore exited nonzero.
- Instrumentation identified the request as `/index.php`,
  `net::ERR_ABORTED`, an intentional Chromium request cancellation. The
  runner counts it separately from actual local request failures and from
  HTTP 4xx/5xx responses. The second run passed with zero JS errors, zero
  genuine local request failures and zero local HTTP errors.
- Free Elementor-only editor baseline still populated correctly; the
  ZiloMentor editor's Heading selection and Pro widget accessibility passed.
- Both the disposable WordPress database and internal Docker resources
  were cleaned up. No production administrator, user, Form or customer data
  was used. No outbound form mail or actual payment was sent.

This is not certification of Form field repeaters, integrations,
transactional delivery, responsive layouts, undo/redo, Theme Builder editing
or pixel-level design fidelity. Release remains blocked.

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

## Verified Elementor Heading edit and synthetic cart control (18 November 2026)

In private Nginx 1.29 / PHP 8.4-FPM staging with a disposable WordPress
database, Playwright found the Heading widget in the editor preview and
opened its Title control. An optional end-to-end test then changed the
**synthetic-only** Heading title to "ZiloMentor QA Saved Heading",
clicked the editor's actual **Publish** button and independently read the
saved _elementor_data from WP-CLI. The new title was present in the
database. **32/32** focused test checks passed, including comparisons to
free Elementor. The test made no changes on the live shop.

To reproduce the optional write test (all writes are temporary):

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --web-server nginx-fpm --focus editor --editor-playwright-image haven-browser-qa:1.62.1 --verify-editor-save

WooCommerce Cart page analysis also confirmed that a separate ordinary
synthetic WordPress page containing the woocommerce_cart shortcode renders the
product and cart form correctly. On the specifically **registered**
Cart page, WordPress's the_content callback was not invoked at all,
while the ordinary control page invoked it once. The cart contents,
registered shortcode, and direct the_content filtering all worked.
A subsequent disposable Cart-page mapping comparison established that
the failure **follows the WooCommerce designated Cart-page setting**:
the formerly designated page displays the product when unassigned, while
the replacement designated page loses the content. The original registered
Cart page still fails in a **WooCommerce-only** baseline with free Elementor,
ZiloMentor, Vamtam integration disabled, and the standard Twenty Twenty-Five
theme active. The registered page runs **zero** the_content callbacks, while
the unregistered control page runs **one**. The registered page did not
reach the normal page.php template in the isolated request. This strongly
isolates a WooCommerce/designated-page rendering-path or staging discrepancy,
not an established ZiloMentor regression. It does not prove that production
WooCommerce has the same problem. No payments or customer data were involved.

## WooCommerce Coming Soon A/B resolution (18 November 2026)

In the installed WooCommerce 11.3 sources, the
Automattic WooCommerce Internal ComingSoon ComingSoonRequestHandler can
intercept assigned store pages during template loading. WooCommerce's
new-install defaults include woocommerce_coming_soon=yes and
woocommerce_store_pages_only=yes; assignment to the Cart page is checked
by the store-page helper. This explains why the registered Cart page
bypassed WordPress the_content while an ordinary page rendered the
same shortcode correctly.

The isolated QA runner now explicitly sets woocommerce_coming_soon=no
**only within its disposable database**, making the synthetic store
visible for anonymous Cart and Checkout tests. With that setting:

- **50/50 isolated HTTP and integration checks passed**, including Fiore
  Cart rendering, product display, WooCommerce session cookies, AJAX
  fragments, add-to-cart and default-theme comparisons.
- A controlled WooCommerce-only A/B test toggled Coming Soon **on** and
  verified the registered Cart item and form were hidden; it toggled
  Coming Soon **off** and verified both returned.
- No production store option, live content, real orders, user accounts,
  payment gateway or outgoing mail was touched.
- Rendering the Checkout page with HTTP 200 is *not* proof of completed
  orders, taxes, shipping, sandbox payments or checkout end-to-end flow.

The earlier notes that mark the Cart-page output unresolved refer to the
pre-fix QA setup and are superseded by these findings.

## Synthetic guest checkout and order-creation verification (18 November 2026)

Using the disposable Nginx/PHP-FPM WordPress environment, an additional
virtual checkout product priced at **GBP 7.49** was created. A separate
anonymous cookie jar added the product, loaded the actual WooCommerce
Checkout form and obtained the checkout nonce. The real WooCommerce
wc-ajax=checkout handler received synthetic billing details and only
the offline BACS bank-transfer payment method. WordPress mail was
blocked by the isolated test-only hook, and the Docker network has
no published ports or external access.

- HTTP checkout returned result=success and an order-received redirect
- A separate WP-CLI process independently verified exactly one matching
  synthetic order in the temporary WordPress database
- The order contained one correct virtual product, total **GBP 7.49**,
  payment method bacs, status on-hold and an empty transaction ID
- The full isolated HTTP/integration run passed **55/55 checks**
- No payment processor, real recipient, external order, customer data,
  production database or live shop configuration was involved

This is evidence for WooCommerce's **offline guest order-creation flow**
with Fiore and ZiloMentor Pro, *not* a payment sandbox, shipping, tax,
refund, accessibility or production visual validation. Those remain
release gates.

## Conditional Theme Builder and automatic Popup regression (18 November 2026)

In disposable Nginx 1.29 / PHP 8.4-FPM staging, the integration runner
seeds a dedicated WordPress page and two synthetic Elementor Library
documents: a **Header** and **Popup**. Both use actual Elementor document
types with include/singular/page/{synthetic-id} conditions saved through
ZiloMentor's Theme Builder conditions manager.

The tests verified that both documents were registered, selected and
rendered on the target page, while **neither** was selected or rendered
on an unrelated page. The header and popup had recognizable synthetic
Heading content. No production page/template or display condition was changed.

A real local Playwright browser then used the same temporary Fiore
installation and confirmed:

- Conditional Header visible on the target page
- Popup frontend API and document registered
- **On Page Load** popup appeared automatically at both 1366x768 and
  390x844 viewports, using separate private browser contexts
- Visible popup Heading correct; closing the modal worked
- Unrelated page did not load the Header or Popup
- Zero page JavaScript errors and zero failed local HTTP requests
- **59/59** isolated integration checks passed, including earlier forms,
  ACF dynamic values, Cart, and offline guest order creation

The browser only accesses the private web:8080 QA network and blocks
requests elsewhere. This does not establish scroll/exit-intent trigger
compatibility, popup editor/save behavior, focus-trap/accessibility,
visual precision, or external payment correctness.

Repeat on the Docker-enabled QA host (no GitHub Actions):

    python3 tools/run_manual_checks.py --source-wordpress /path/to/wordpress --web-server nginx-fpm --frontend-playwright-image haven-browser-qa:1.62.1

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
