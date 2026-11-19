"""Non-runtime checks for the ZiloMentor Pro prototype; no WordPress bootstrap."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "elementor-pro.php"
PLUGIN = ROOT / "plugin.php"
errors = []
def check(label, predicate):
    print(("PASS" if predicate else "FAIL") + " " + label)
    if not predicate:
        errors.append(label)

check("forked plugin entrypoint", MAIN.is_file() and not (ROOT / "pro-elements.php").exists())
main = MAIN.read_text()
plugin = PLUGIN.read_text()
check("honest independent plugin branding", "Plugin Name: ZiloMentor Pro" in main)
check("safe exact plugin basename at install path", "define( 'ELEMENTOR_PRO_PLUGIN_BASE', plugin_basename( ELEMENTOR_PRO__FILE__ ) );" in main)
check("Elementor Pro API version retained", "define( 'ELEMENTOR_PRO_VERSION', '4.4.0' )" in main)
check("independent fork release version", "define( 'ZILOMENTOR_VERSION', '0.1.0' )" in main)
check("ElementorPro PHP namespace preserved", "namespace ElementorPro;" in plugin)
check("original Elementor Pro bootstrap symbol available", "function elementor_pro_load_plugin()" in main)
check("ZiloMentor Pro user-facing interface labels",
      "ZiloMentor Pro Data Updater" in (ROOT/"core/upgrade/manager.php").read_text()
      and "ZiloMentor Pro Canvas" in
      (ROOT/"modules/theme-builder/documents/theme-page-document.php").read_text()
      and "ZiloMentor Pro Notes" in
      (ROOT/"modules/notes/user/preferences.php").read_text())
check("deferred bootstrap after free Elementor initialization",
      "add_action( 'plugins_loaded', 'pro_elements_plugin_load_plugin', 10 )" in main
      and "if ( did_action( 'plugins_loaded' ) ) {" in main)
check("upstream updater removed from load path", "new Updater( $config )" not in plugin)
check("custom Update URI set", "Update URI: https://github.com/Galactus-Prime/zilomentor-pro" in main)
check("original GPL notice retained", "Elementor Ltd." in (ROOT / "license.txt").read_text())
check("PRO Elements GPL notice retained", "PRO Elements team" in (ROOT / "license.txt").read_text())
check("no fake Elementor agency license", "elementor_pro_license_key" not in main
      and "10.10.2030" not in main and "pre_http_request" not in main)
# Observed in the real Vamtam Fiore theme/integration PHP source on 2026-11-17.
fiore_parent_class_files = (
    "plugin.php",
    "modules/theme-builder/module.php",
    "modules/theme-builder/widgets/archive-posts.php",
    "modules/assets-manager/asset-types/icons/custom-icons.php",
    "modules/assets-manager/asset-types/icons-manager.php",
    "modules/assets-manager/asset-types/fonts-manager.php",
    "modules/dynamic-tags/module.php",
    "modules/dynamic-tags/tags/base/data-tag.php",
    "modules/dynamic-tags/tags/base/tag.php",
    "modules/dynamic-tags/tags/author-profile-picture.php",
    "modules/popup/module.php",
    "modules/query-control/module.php",
    "modules/forms/widgets/form.php",
    "modules/forms/widgets/login.php",
    "modules/nav-menu/widgets/nav-menu.php",
    "modules/posts/widgets/posts.php",
    "modules/posts/skins/skin-classic.php",
    "modules/theme-builder/skins/posts-archive-skin-classic.php",
    "modules/carousel/widgets/testimonial-carousel.php",
    "modules/woocommerce/widgets/product-images.php",
)
missing = [x for x in fiore_parent_class_files if not (ROOT/x).exists()]
check("Fiore parent PHP class source files: 20/20", not missing)
if missing:
    print("Missing:", ", ".join(missing))
qa_script = (ROOT / "tools/qa_isolated_site.py").read_text()
qa_fixture = (ROOT / "tests/fixtures/seed_synthetic.php").read_text()
check("isolated QA does not copy live configuration or customer data",
      'core_root_files = (' in qa_script
      and 'source / "wp-content/plugins"' in qa_script
      and 'wp-config.php' not in qa_fixture
      and "ZMP_ISOLATED_QA" in qa_fixture
      and '"--internal"' in qa_script)
check("ACF Pro dynamic field widget has isolated regression coverage",
      "advanced-custom-fields-pro" in qa_script
      and "zmp_qa_acf_tag" in qa_script
      and "ACF dynamic value renders inside Elementor heading" in qa_script
      and "field_zmp_qa_text" in qa_fixture
      and (ROOT / "modules/dynamic-tags/acf/tags/acf-text.php").is_file())
check("optional browser QA is isolated and does not require hosted CI",
      "--browser-image" in qa_script
      and "--browser-image" in (ROOT/"tools/run_manual_checks.py").read_text()
      and '"--network", network' in qa_script
      and '"--no-sandbox"' in qa_script
      and '"--dump-dom"' in qa_script
      and not (ROOT/".github/workflows/release.yaml").exists())
check("isolated editor login requires disposable token and protects guest cookies",
      "ZMP_QA_EDITOR_TOKEN" in qa_script
      and "editor-cookies.txt" in qa_script
      and "hash_equals( $token, $received )" in qa_script
      and "Free Elementor editor baseline without ZiloMentor" in qa_script
      and (ROOT / "tests/browser_editor_smoke.js").is_file())
check("editor Playwright prevents outbound browser requests",
      "context.route" in (ROOT / "tests/browser_editor_smoke.js").read_text()
      and 'url.hostname === "web"' in
      (ROOT / "tests/browser_editor_smoke.js").read_text()
      and "--editor-playwright-image" in
      (ROOT / "tools/run_manual_checks.py").read_text())
check("private Nginx PHP-FPM QA has no public host port mapping",
      'choices=("php", "nginx-fpm")' in qa_script
      and '"--network-alias", "web"' in qa_script
      and '"--network-alias", "php"' in qa_script
      and '"--entrypoint", "php-fpm"' in qa_script
      and '"--entrypoint", "nginx"' in qa_script
      and "--web-server" in (ROOT / "tools/run_manual_checks.py").read_text())
check("editor readiness baseline requires populated controls",
      "panelPopulatedWaitPassed" in (ROOT / "tests/browser_editor_smoke.js").read_text()
      and "Free Elementor editor baseline sufficiently populated" in qa_script
      and "ZiloMentor editor panel matches baseline content" in qa_script)
check("synthetic Heading edit/save cannot run against production or unspecified QA",
      "--verify-editor-save" in qa_script
      and "ZMP_QA_SAVE_TEST=yes" in qa_script
      and "ZiloMentor QA Saved Heading" in qa_script
      and "Synthetic Heading title persisted to WordPress database" in qa_script
      and "--verify-editor-save" in
          (ROOT / "tools/run_manual_checks.py").read_text())
check("cart rendering test isolates designated Cart page from shortcode control",
      "zmp_qa_content_trace" in qa_script
      and "Ordinary page with WooCommerce cart shortcode displays item" in qa_script
      and "cart_control" in qa_fixture)
check("WooCommerce Coming Soon is disabled only for synthetic storefront QA",
      '"woocommerce_coming_soon", "no"' in qa_script
      and '"WooCommerce Coming Soon ON intercepts designated Cart"' in qa_script
      and '"WooCommerce Coming Soon OFF restores designated Cart"' in qa_script
      and '"Disposable WooCommerce storefront explicitly live"' in qa_script)
check("checkout QA uses a separate guest jar and only offline synthetic payment",
      "checkout-cookies.txt" in qa_script
      and '"payment_method": "bacs"' in qa_script
      and '"?wc-ajax=checkout"' in qa_script
      and "offline guest order persisted" in qa_script
      and "transaction_blank" in qa_script
      and "checkout_product" in qa_fixture
      and "set_virtual( true )" in qa_fixture)
check("Theme Builder/Popup fixtures require disposable WordPress",
      (ROOT / "tests/fixtures/seed_theme_popup.php").is_file()
      and "ZMP_ISOLATED_QA" in
      (ROOT / "tests/fixtures/seed_theme_popup.php").read_text()
      and "include" in
      (ROOT / "tests/fixtures/seed_theme_popup.php").read_text()
      and "save_conditions" in
      (ROOT / "tests/fixtures/seed_theme_popup.php").read_text()
      and "Theme Builder and Popup condition/render" in qa_script)
check("frontend Popup QA blocks external requests and verifies automatic trigger",
      (ROOT / "tests/browser_theme_popup.js").is_file()
      and 'context.route("**/*"' in
      (ROOT / "tests/browser_theme_popup.js").read_text()
      and "popupAutoOpenedMobile" in
      (ROOT / "tests/browser_theme_popup.js").read_text()
      and "popupAutoOpened" in qa_script
      and "--frontend-playwright-image" in
      (ROOT / "tools/run_manual_checks.py").read_text())
check("scroll and exit-intent popups are isolated in browser QA",
      all(key in (ROOT / "tests/fixtures/seed_theme_popup.php").read_text()
          for key in ("scrolling_offset", "exit_intent", "scroll_target", "exit_target"))
      and all(key in (ROOT / "tests/browser_theme_popup.js").read_text()
              for key in ("scrollPopupAbsentBeforeScroll", "scrollPopupOpenedByScroll",
                          "exitPopupAbsentBeforeIntent", "exitPopupOpenedByIntent"))
      and "Popup page-specific condition:" in qa_script)
check("staging ZIP excludes transient cPanel CLI cache",
      '.ea-php-cli' in (ROOT / "tools/build_zip.py").read_text()
      and '.ea-php-cli' in qa_script)
check("theme location function still supplied",
      "elementor_theme_do_location" in "\n".join(p.read_text(errors="replace")
      for p in (ROOT/"modules/theme-builder").rglob("*.php")))
print("RESULT:", "PASS" if not errors else "FAIL", "-", len(errors), "failed")
sys.exit(0 if not errors else 1)
