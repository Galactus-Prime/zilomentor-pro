#!/usr/bin/env python3
"""Manual, disposable WordPress/Fiore/WooCommerce HTTP regression tests.

This script NEVER connects to the production database. It copies only read-only
WordPress source/plugin/theme code from --source-wordpress to a private temp
directory, installs a fresh synthetic WordPress database and starts a PHP server
only on an internal Docker network (no host port mapping). It uses locally
cached Docker images, never GitHub Actions, and destroys test resources.
Do not pass production credentials or customer files into this tool.

Example on an already-provisioned private QA server:
    python3 tools/qa_isolated_site.py --source-wordpress /path/to/wordpress
"""
import argparse
import json
import re
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ("advanced-custom-fields-pro", "elementor", "woocommerce", "vamtam-elementor-integration-fiore")
THEME = "vamtam-fiore"


def execute(command, timeout=120):
    return subprocess.run(
        command, capture_output=True, text=True, timeout=timeout,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--source-wordpress", required=True, type=Path)
    argp.add_argument("--real-file-fixtures-dir", type=Path, default=None,
                      help="Optional self-authored Office/PDF/ODF/media fixtures under an isolated /tmp directory.")
    argp.add_argument(
        "--plugin-folder", choices=("elementor-pro", "zilomentor-pro"),
        default="elementor-pro",
        help="Exercise legacy compatibility layout or independent ZiloMentor folder using disposable WordPress only.",
    )
    argp.add_argument(
        "--focus", choices=("all", "editor", "runtime"), default="all",
        help="Full integration, editor-focused browser checks, or only synthetic runtime/security checks.",
    )
    argp.add_argument(
        "--verify-editor-save", action="store_true",
        help="Opt-in synthetic Heading edit/save on the disposable WordPress database only; requires --focus editor and Playwright.",
    )
    argp.add_argument(
        "--verify-editor-history", action="store_true",
        help="Opt-in real Elementor History undo/redo on a dedicated synthetic Heading and saved-data check.",
    )
    argp.add_argument(
        "--verify-editor-form-save", action="store_true",
        help="Opt-in synthetic Pro Form editor save with independent WordPress database/HTTP verification.",
    )
    argp.add_argument(
        "--verify-editor-form-fields", action="store_true",
        help="Opt-in real Pro Form repeater field-label edit/Publish with database and frontend checks.",
    )
    argp.add_argument(
        "--verify-theme-builder-save", action="store_true",
        help="Opt-in isolated Theme Builder Header template editor save plus page-condition render verification.",
    )
    argp.add_argument(
        "--verify-popup-editor-save", action="store_true",
        help="Opt-in isolated Popup template Heading edit and Publish, with database/condition verification.",
    )
    argp.add_argument(
        "--verify-posts-nav-editor", action="store_true",
        help="Opt-in Posts widget selection and Nav Menu label edit/Publish in isolated Elementor.",
    )
    argp.add_argument(
        "--verify-editor-responsive", action="store_true",
        help="Opt-in isolated real Elementor tablet, mobile and desktop editor switching checks.",
    )
    argp.add_argument("--verify-apache-uploads", action="store_true",
                      help="Run disposable localhost Apache against generated Form .htaccess and verify download/deny headers.")
    argp.add_argument(
        "--php-image", default="zmp-php84-zip-qa:local",
        help="Disposable PHP-FPM with ZIP extension; manually build using tools/docker/Dockerfile.qa-php84-zip.",
    )
    argp.add_argument(
        "--web-server", choices=("php", "nginx-fpm"), default="php",
        help="Use the existing PHP development server or a disposable Nginx + multiworker PHP-FPM pair.",
    )
    argp.add_argument("--nginx-image", default="nginx:1.29-alpine")
    argp.add_argument("--db-image", default="mariadb:11.4")
    argp.add_argument("--curl-image", default="curlimages/curl:8.16.0")
    argp.add_argument("--clean-image", default="alpine:3.21")
    argp.add_argument("--wpcli", default="/usr/local/bin/wp", type=Path)
    argp.add_argument(
        "--browser-image", default=None,
        help="Optional locally cached Chromium Docker image for real-browser DOM smoke tests.",
    )
    argp.add_argument(
        "--browser-bin",
        default="/ms-playwright/chromium-1243/chrome-linux64/chrome",
        help="Path to Chromium inside the optional browser image.",
    )
    argp.add_argument(
        "--frontend-playwright-image", default=None,
        help="Optional cached Playwright image for isolated front-end Popup open/close verification.",
    )
    argp.add_argument(
        "--editor-playwright-image", default=None,
        help="Optional cached image with Playwright available for bounded editor JS checks.",
    )
    args = argp.parse_args()
    plugin_folder = args.plugin_folder
    if (args.verify_editor_save or args.verify_editor_history or args.verify_editor_form_save
            or args.verify_editor_form_fields or args.verify_theme_builder_save or args.verify_popup_editor_save
            or args.verify_posts_nav_editor or args.verify_editor_responsive):
        require(args.focus == "editor" and args.editor_playwright_image is not None
                and args.web_server == "nginx-fpm",
                "Editor save verification needs --focus editor, --web-server nginx-fpm and --editor-playwright-image")

    source = args.source_wordpress.resolve(strict=True)
    require(source.is_dir() and (source / "wp-admin").is_dir()
            and (source / "wp-includes").is_dir(),
            "--source-wordpress must point to an existing WordPress installation")
    require((ROOT / "elementor-pro.php").is_file(), "Missing ZiloMentor entrypoint")
    require(args.wpcli.is_file(), "WP-CLI PHAR not available at --wpcli")
    images = [args.php_image, args.db_image, args.curl_image, args.clean_image]
    if args.web_server == "nginx-fpm":
        images.append(args.nginx_image)
    if args.browser_image is not None:
        images.append(args.browser_image)
    if args.editor_playwright_image is not None:
        images.append(args.editor_playwright_image)
    if args.frontend_playwright_image is not None:
        images.append(args.frontend_playwright_image)
    for image in images:
        p = execute(["docker", "image", "inspect", image], timeout=15)
        require(p.returncode == 0, f"Docker image must already be cached: {image}")

    # Fail before creating a DB/network if archive tests would be skipped.
    zip_probe = execute([
        "docker", "run", "--rm", "--network", "none", "--entrypoint", "php",
        args.php_image, "-r", 'exit(class_exists("ZipArchive") ? 0 : 7);',
    ], timeout=25)
    require(zip_probe.returncode == 0,
            "Disposable QA PHP image must contain ZipArchive; build "
            "tools/docker/Dockerfile.qa-php84-zip manually first.")

    tag = secrets.token_hex(4)
    network = f"zmp-qa-net-{tag}"
    database = f"zmp-qa-db-{tag}"
    web = f"zmp-qa-web-{tag}"
    db_password = "ZmpSynthetic" + secrets.token_hex(16)
    editor_login_token = secrets.token_hex(28)
    temp = Path(tempfile.mkdtemp(prefix="zmp-isolated-qa-", dir="/tmp"))
    active = []
    observations = []

    def record(name, success, detail=None):
        row = {"name": name, "passed": bool(success)}
        if detail is not None:
            row["detail"] = detail
        observations.append(row)
        print(("PASS " if success else "FAIL ") + name, flush=True)
        return bool(success)

    def docker(args_, timeout=120):
        return execute(["docker"] + args_, timeout=timeout)

    try:
        site = temp / "site"
        site.mkdir()
        for part in ("wp-admin", "wp-includes"):
            shutil.copytree(source / part, site / part)
        core_root_files = (
            "index.php", "wp-activate.php", "wp-blog-header.php",
            "wp-comments-post.php", "wp-cron.php", "wp-links-opml.php",
            "wp-load.php", "wp-login.php", "wp-mail.php",
            "wp-settings.php", "wp-signup.php", "wp-trackback.php",
            "xmlrpc.php",
        )
        for filename in core_root_files:
            core_file = source / filename
            require(core_file.is_file(), "Missing WordPress core file: " + filename)
            shutil.copy2(core_file, site / filename)
        # Do not copy wp-config.php, media, mu-plugins, or any other live data.
        plugins_path = site / "wp-content" / "plugins"
        themes_path = site / "wp-content" / "themes"
        plugins_path.mkdir(parents=True)
        themes_path.mkdir(parents=True)
        if args.real_file_fixtures_dir is not None:
            # Never stage files from production uploads or customer directories.
            fixture_root = args.real_file_fixtures_dir.resolve(strict=True)
            if (not fixture_root.is_dir()
                    or not str(fixture_root).startswith("/tmp/zmp-realfiles-")
                    or "public_html" in fixture_root.parts):
                raise RuntimeError("Real-file QA fixtures must originate in a private /tmp/zmp-realfiles-* directory")
            manifest = fixture_root / "manifest.json"
            if not manifest.is_file() or manifest.is_symlink():
                raise RuntimeError("Real-file QA fixture manifest missing")
            parsed_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            paths = parsed_manifest.get("files", {})
            if (parsed_manifest.get("generated") != "self-authored"
                    or not isinstance(paths, dict) or len(paths) != 13):
                raise RuntimeError("Real-file QA fixture manifest not self-authored or incomplete")
            staging = site / "wp-content" / "zmp-qa-real-formats"
            staging.mkdir()
            for name in ("manifest.json", *paths.keys()):
                p = fixture_root / name
                if (not isinstance(name, str) or not re.fullmatch(r"[a-z0-9.-]+", name)
                        or not p.is_file() or p.is_symlink() or p.stat().st_size > 16 * 1024 * 1024):
                    raise RuntimeError("Invalid real-file QA fixture: " + str(name))
                shutil.copy2(p, staging / name)
        for plugin in PLUGINS:
            from_dir = source / "wp-content/plugins" / plugin
            require(from_dir.is_dir(), f"Missing test dependency: {plugin}")
            shutil.copytree(from_dir, plugins_path / plugin)
        theme_path = source / "wp-content/themes" / THEME
        require(theme_path.is_dir(), f"Missing theme: {THEME}")
        shutil.copytree(theme_path, themes_path / THEME)
        default_theme = source / "wp-content/themes/twentytwentyfive"
        has_default_theme = default_theme.is_dir()
        if has_default_theme:
            shutil.copytree(default_theme, themes_path / "twentytwentyfive")
        shutil.copytree(
            ROOT, plugins_path / plugin_folder,
            # Ignore transient cPanel EA-PHP CLI cache files as well. They can
            # disappear between copytree's listing and file-copy phase.
            ignore=shutil.ignore_patterns(
                ".git", ".github", "dist", "__pycache__", "*.pyc",
                ".ea-php-cli*"),
        )
        # Test-only mail intercept: no messages may reach real recipients.
        mu = site / "wp-content" / "mu-plugins"
        mu.mkdir(exist_ok=True)
        if plugin_folder == "zilomentor-pro":
            early = ROOT / "tools/zmp-early-bootstrap.php"
            require(early.is_file(), "Missing independent plugin early bootstrap adapter")
            shutil.copy2(early, mu / "zmp-early-bootstrap.php")
        (mu / "zmp-qa-no-mail.php").write_text(
            r"""<?php
// Generated exclusively inside a disposable QA WordPress tree.
// Suppress ALL transport and store only synthetic attachment observations.
add_filter( 'pre_wp_mail', static function ( $pre, $mail ) {
    $attachments = $mail['attachments'] ?? [];
    if ( is_string( $attachments ) ) {
        $attachments = [ $attachments ];
    }
    if ( ! is_array( $attachments ) ) {
        $attachments = [];
    }
    $checks = [];
    foreach ( $attachments as $attachment ) {
        $checks[] = [
            'safe' => \ElementorPro\Core\Utils::is_safe_form_attachment_path( $attachment ),
            'exists_at_send' => is_string( $attachment ) && is_file( $attachment ),
            'name' => is_string( $attachment ) ? basename( $attachment ) : '',
            'sha256' => is_string( $attachment ) && is_file( $attachment )
                ? hash_file( 'sha256', $attachment ) : '',
        ];
    }
    // No recipient addresses or message bodies are recorded in QA.
    update_option( 'zmp_qa_intercepted_mail', [
        'attachment_count' => count( $attachments ),
        'attachments' => $checks,
    ], false );
    return true; // No real mail can leave this disposable QA instance.
}, PHP_INT_MAX, 2 );
add_action( 'template_redirect', function () {
    if ( ! isset( $_GET['zmp_qa_cart_state'] ) ) {
        return;
    }
    $cart = WC()->cart;
    $items = $cart ? $cart->get_cart() : [];
    wp_send_json( [
        'item_count' => $cart ? $cart->get_cart_contents_count() : 0,
        'product_ids' => array_values( array_map(
            static function ( $item ) { return (int) $item['product_id']; },
            $items
        ) ),
        'session_cookie_present' => count( array_filter(
            array_keys( $_COOKIE ),
            static function ( $key ) { return str_contains( $key, 'woocommerce_session_' ); }
        ) ) > 0,
    ] );
}, 30 );

// Test-only synthetic ACF metadata; never stored on the production website.
add_action( 'acf/init', function () {
    if ( ! function_exists( 'acf_add_local_field_group' ) ) {
        return;
    }
    acf_add_local_field_group( [
        'key' => 'group_zmp_qa_only',
        'title' => 'ZiloMentor QA Only',
        'fields' => [
            [
                'key' => 'field_zmp_qa_text',
                'name' => 'zmp_qa_text',
                'label' => 'ZiloMentor QA Text',
                'type' => 'text',
            ],
        ],
        'location' => [ [ [ 'param' => 'post_type', 'operator' => '==', 'value' => 'page' ] ] ],
        'active' => true,
    ] );
} );
add_action( 'template_redirect', function () {
    if ( ! isset( $_GET['zmp_qa_cart_render'] ) ) {
        return;
    }
    $id = get_queried_object_id();
    $post = get_post( $id );
    $raw = $post ? $post->post_content : '';
    $html = do_shortcode( $raw );
    wp_send_json( [
        'queried_id' => $id,
        'is_cart' => function_exists( 'is_cart' ) && is_cart(),
        'raw' => $raw,
        'shortcode_exists' => shortcode_exists( 'woocommerce_cart' ),
        'shortcode_length' => strlen( $html ),
        'shortcode_has_item' => str_contains( $html, 'ZiloMentor Synthetic Test Product' ),
        'shortcode_has_form' => str_contains( $html, 'woocommerce-cart-form' ),
        'session_count' => WC()->cart ? WC()->cart->get_cart_contents_count() : 0,
    ] );
}, 35 );
add_action( 'template_redirect', function () {
    if ( ! isset( $_GET['zmp_qa_acf_tag'] ) ) {
        return;
    }
    try {
        $tags = \Elementor\Plugin::instance()->dynamic_tags;
        $registered = $tags->get_tags();
        $value = $tags->get_tag_data_content( 'zmp-acf-test', 'acf-text',
            [ 'key' => 'field_zmp_qa_text:zmp_qa_text' ] );
        wp_send_json( [
            'acf_loaded' => function_exists( 'acf_get_field_groups' ),
            'acf_text_tag' => isset( $registered['acf-text'] ),
            'tag_value' => $value,
            'post_id' => get_queried_object_id(),
        ] );
    } catch ( \Throwable $exception ) {
        wp_send_json( [
            'acf_text_tag' => false,
            'error_class' => get_class( $exception ),
        ], 500 );
    }
}, 35 );


// Diagnose actual template rendering without leaking any production data.
// This runs only inside disposable QA WordPress and emits only booleans/counts.
$GLOBALS['zmp_qa_content_trace'] = [
    'calls' => 0,
    'has_item' => false,
    'has_cart_form' => false,
    'has_control_preamble' => false,
    'template_name' => '',
];
add_filter( 'template_include', function ( $template ) {
    if ( isset( $_GET['zmp_qa_trace'] ) ) {
        $GLOBALS['zmp_qa_content_trace']['template_name'] = basename( $template );
    }
    return $template;
}, PHP_INT_MAX );
add_filter( 'the_content', function ( $content ) {
    if ( ! isset( $_GET['zmp_qa_trace'] ) ) {
        return $content;
    }
    $state = &$GLOBALS['zmp_qa_content_trace'];
    $state['calls']++;
    $state['has_item'] = $state['has_item'] ||
        str_contains( $content, 'ZiloMentor Synthetic Test Product' );
    $state['has_cart_form'] = $state['has_cart_form'] ||
        str_contains( $content, 'woocommerce-cart-form' );
    $state['has_control_preamble'] = $state['has_control_preamble'] ||
        str_contains( $content, 'ZiloMentor Cart Control Before' );
    return $content;
}, PHP_INT_MAX );
add_action( 'shutdown', function () {
    if ( ! isset( $_GET['zmp_qa_trace'] ) ) {
        return;
    }
    $s = $GLOBALS['zmp_qa_content_trace'];
    $s['queried_page'] = (int) get_queried_object_id();
    $s['cart_condition'] = function_exists( 'is_cart' ) && is_cart();
    echo "\n<!--ZMP_QA_TRACE:" . wp_json_encode( $s ) . "-->\n";
}, PHP_INT_MAX );

// Inspect the normal WordPress the_content filter on a disposable cart page.
add_action( 'template_redirect', function () {
    if ( ! isset( $_GET['zmp_qa_content_filter'] ) ) {
        return;
    }
    $id = get_queried_object_id();
    $post = get_post( $id );
    $raw = $post ? $post->post_content : '';
    $html = apply_filters( 'the_content', $raw );
    wp_send_json( [
        'queried_id' => $id,
        'is_cart' => function_exists( 'is_cart' ) && is_cart(),
        'raw_has_shortcode' => has_shortcode( $raw, 'woocommerce_cart' ),
        'filter_bytes' => strlen( $html ),
        'filter_contains_product' => str_contains(
            $html, 'ZiloMentor Synthetic Test Product'
        ),
        'filter_contains_cart_form' => str_contains(
            $html, 'woocommerce-cart-form'
        ),
    ] );
}, 35 );

// Scoped synthetic Theme Builder/Popup inspection. No production path.
add_action( 'template_redirect', function () {
    if ( ! isset( $_GET['zmp_qa_theme_popup'] ) ) {
        return;
    }
    try {
        $module = \ElementorPro\Modules\ThemeBuilder\Module::instance();
        $locations = $module->get_locations_manager();
        $conditions = $module->get_conditions_manager();
        $header_docs = $conditions->get_documents_for_location( 'header' );
        $popup_docs = $conditions->get_documents_for_location( 'popup' );
        ob_start();
        $header_render = $locations->do_location( 'header' );
        $header_html = ob_get_clean();
        ob_start();
        $popup_render = $locations->do_location( 'popup' );
        $popup_html = ob_get_clean();
        wp_send_json( [
            'queried_id' => get_queried_object_id(),
            'header_doc_ids' => array_map( 'intval', array_keys( $header_docs ) ),
            'popup_doc_ids' => array_map( 'intval', array_keys( $popup_docs ) ),
            'header_render' => (bool) $header_render,
            'popup_render' => (bool) $popup_render,
            'header_marker' => str_contains( $header_html, 'ZMP Synthetic Conditional Header' ),
            'header_saved_marker' => str_contains( $header_html, 'ZiloMentor QA Saved Header' ),
            'popup_marker' => str_contains( $popup_html, 'ZMP Synthetic Conditional Popup' ),
            'popup_saved_marker' => str_contains( $popup_html, 'ZiloMentor QA Saved Popup' ),
            'scroll_popup_marker' => str_contains( $popup_html, 'ZMP Synthetic Scroll Popup' ),
            'exit_popup_marker' => str_contains( $popup_html, 'ZMP Synthetic Exit Popup' ),
            'header_bytes' => strlen( $header_html ),
            'popup_bytes' => strlen( $popup_html ),
            'popup_modal_markup' => str_contains( $popup_html, 'elementor-popup-modal' ),
        ] );
    } catch ( \Throwable $exception ) {
        wp_send_json( [
            'error_class' => get_class( $exception ),
            'error_seen' => true,
        ], 500 );
    }
}, 40 );

// One-time QA-only editor login: localhost-style private Docker hostname,
// a per-run 224-bit random token, and an admin user in a synthetic database.
// The token exists only in the disposable PHP server container environment.
add_action( 'init', function () {
    if ( ! isset( $_GET['zmp_qa_editor_login'] ) ) {
        return;
    }
    $token = getenv( 'ZMP_QA_EDITOR_TOKEN' );
    $received = is_string( $_GET['zmp_qa_editor_login'] )
        ? $_GET['zmp_qa_editor_login'] : '';
    $host = $_SERVER['HTTP_HOST'] ?? '';
    if (
        ! is_string( $token ) || strlen( $token ) !== 56 ||
        ! hash_equals( $token, $received ) ||
        'web:8080' !== $host
    ) {
        status_header( 403 );
        exit;
    }
    $user = get_user_by( 'login', 'qa-only' );
    $page_id = absint( $_GET['zmp_qa_page'] ?? 0 );
    $post_type = get_post_type( $page_id );
    $allowed_page = 'page' === $post_type;
    $template_type = get_post_meta( $page_id, '_elementor_template_type', true );
    $title = get_the_title( $page_id );
    $allowed_theme_fixture = (
        'elementor_library' === $post_type
        && (
            ( 'header' === $template_type && 'ZMP Synthetic Header' === $title )
            || ( 'popup' === $template_type && 'ZMP Synthetic Popup' === $title )
        )
    );
    if ( ! $user || ! user_can( $user, 'manage_options' ) ||
         ( ! $allowed_page && ! $allowed_theme_fixture ) ) {
        status_header( 403 );
        exit;
    }
    wp_set_current_user( $user->ID );
    wp_set_auth_cookie( $user->ID, false );
    wp_safe_redirect( admin_url( 'post.php?post=' . $page_id . '&action=elementor' ) );
    exit;
}, 1 );
"""
        )

        p = docker(["network", "create", "--internal", network], 25)
        require(p.returncode == 0, "Failed to create isolated Docker network")
        active.append(("network", network))
        p = docker([
            "run", "-d", "--name", database, "--network", network,
            "--network-alias", "db", "--memory=640m", "--cpus=1",
            "--tmpfs", "/var/lib/mysql:rw,size=800m",
            "-e", "MARIADB_ROOT_PASSWORD=" + db_password,
            "-e", "MARIADB_DATABASE=wordpress", args.db_image,
        ], 55)
        require(p.returncode == 0, "Failed to start disposable MariaDB")
        active.append(("container", database))

        def php(arguments, environment=None, timeout=130):
            command = [
                "run", "--rm", "--network", network, "--memory=850m", "--cpus=1",
                "-v", str(site) + ":/var/www/html",
                "-v", str(args.wpcli) + ":/usr/local/bin/wp:ro",
                "-w", "/var/www/html",
            ]
            if environment:
                for key, value in environment.items():
                    command.extend(["-e", key + "=" + value])
            command.extend([
                "--entrypoint", "php", args.php_image,
                "-d", "memory_limit=512M", "-d", "display_errors=0",
            ])
            return docker(command + arguments, timeout)

        def wp(*arguments, environment=None):
            return php([
                "/usr/local/bin/wp", "--path=/var/www/html", "--allow-root",
            ] + list(arguments), environment)

        php_ready = (
            'try{$db=new mysqli("db","root",getenv("ZMP_DB_PASS"),"wordpress");'
            'exit($db->connect_errno?3:0);}catch(Throwable $e){exit(3);}'
        )
        for attempt in range(55):
            ready = php(["-r", php_ready], {"ZMP_DB_PASS": db_password}, timeout=20)
            if ready.returncode == 0:
                break
            time.sleep(2)
        require(record("isolated MariaDB network ready", ready.returncode == 0),
                "Database did not become ready")

        p = wp(
            "config", "create", "--dbname=wordpress", "--dbuser=root",
            "--dbpass=" + db_password, "--dbhost=db", "--skip-check",
        )
        require(record("synthetic WordPress config", p.returncode == 0),
                "Could not configure synthetic WordPress")
        p = wp(
            "core", "install", "--url=http://web:8080",
            "--title=ZiloMentor-Disposable-QA",
            "--admin_user=qa-only",
            "--admin_password=" + secrets.token_hex(24),
            "--admin_email=qa@example.invalid", "--skip-email",
        )
        require(record("fresh WordPress installation", p.returncode == 0),
                "Could not install synthetic WordPress")
        for plugin in ("advanced-custom-fields-pro", "elementor", plugin_folder, "woocommerce",
                       "vamtam-elementor-integration-fiore"):
            p = wp("plugin", "activate", plugin)
            require(record("activate " + plugin, p.returncode == 0),
                    "Plugin activation failed: " + plugin)
        # Independently identify the WordPress plugin basename. The
        # compatibility PHP API should remain ElementorPro, but the plugin's
        # registered identity must be ZiloMentor's independent directory.
        identity_check = wp(
            "eval", '$list=(array)get_option("active_plugins",[]);'
            '$target="' + plugin_folder + '/elementor-pro.php";'
            'echo wp_json_encode(["target_active"=>in_array($target,$list,true),'
            '"legacy_active"=>in_array("elementor-pro/elementor-pro.php",$list,true),'
            '"new_active"=>in_array("zilomentor-pro/elementor-pro.php",$list,true)]);',
        )
        try:
            identity_state = json.loads(identity_check.stdout.strip())
        except ValueError:
            identity_state = {}
        require(record("Independent ZiloMentor plugin identity",
                       identity_check.returncode == 0
                       and identity_state.get("target_active") is True
                       and identity_state.get("legacy_active") is (plugin_folder == "elementor-pro")
                       and identity_state.get("new_active") is (plugin_folder == "zilomentor-pro"),
                       {"folder": plugin_folder, "identity": identity_state}),
                "Synthetic plugin identity does not match the requested folder")
        # A fresh WooCommerce 9.3+ installation starts in store-page-only
        # Coming Soon mode. Its ComingSoonRequestHandler exits during
        # template_include for the designated Cart/Checkout pages, hiding the
        # actual shortcode/form from anonymous HTTP tests. Our disposable
        # store must explicitly emulate a *live* storefront before testing.
        # This option is written ONLY in the freshly created synthetic DB.
        initial_visibility = wp("option", "get", "woocommerce_coming_soon")
        visibility_set = wp("option", "update", "woocommerce_coming_soon", "no")
        visibility_check = wp("option", "get", "woocommerce_coming_soon")
        require(record("Disposable WooCommerce storefront explicitly live",
                       visibility_set.returncode == 0
                       and visibility_check.returncode == 0
                       and visibility_check.stdout.strip() == "no",
                       {
                           "initial_store_coming_soon":
                               initial_visibility.stdout.strip() if initial_visibility.returncode == 0 else "unknown",
                           "final_store_coming_soon":
                               visibility_check.stdout.strip() if visibility_check.returncode == 0 else "unknown",
                       }),
                "Failed to disable Coming Soon mode in disposable WooCommerce QA store")

        p = wp("theme", "activate", THEME)
        require(record("activate Fiore theme", p.returncode == 0),
                "Fiore activation failed")
        for filename in ("runtime_bootstrap.php", "runtime_widgets.php",
                         "runtime_atomic_attributes_security.php",
                         "runtime_posts_null.php", "runtime_release_guard.php",
                         "runtime_bootstrap_order.php",
                         "runtime_form_upload_security.php",
                         "runtime_form_mail_attachment_safety.php",
                         "runtime_icon_zip_security.php",
                         "runtime_form_document_visibility.php",
                         "runtime_rest_auth_security.php",
                         "runtime_stripe_security.php",
                         "runtime_posts_visibility.php",
                         "runtime_rest_sensitive_controllers.php"):
            p = wp("eval-file",
                   f"wp-content/plugins/{plugin_folder}/tests/" + filename,
                   environment={"ZMP_ISOLATED_QA": "yes"})
            require(record("runtime " + filename, p.returncode == 0,
                           {"exit": p.returncode,
                            "security_checks": p.stdout.strip().splitlines()[:15]
                            if filename == "runtime_atomic_attributes_security.php" else
                            (p.stdout.strip().splitlines()[:6]
                             if filename in ("runtime_posts_null.php", "runtime_release_guard.php",
                                             "runtime_bootstrap_order.php",
                                             "runtime_form_upload_security.php",
                                             "runtime_rest_auth_security.php",
                                             "runtime_stripe_security.php",
                                             "runtime_posts_visibility.php",
                                             "runtime_rest_sensitive_controllers.php") else [])}),
                    "Runtime check failed: " + (p.stdout + p.stderr)[-500:])

        if args.real_file_fixtures_dir is not None:
            p = wp("eval-file",
                   f"wp-content/plugins/{plugin_folder}/tests/runtime_real_file_uploads.php",
                   environment={"ZMP_ISOLATED_QA": "yes"})
            require(record("real Office ODF PDF audio video and polyglot upload validation",
                           p.returncode == 0 and p.stdout.count("PASS ") == 26,
                           {"exit": p.returncode,
                            "checks": p.stdout.strip().splitlines()[:26]}),
                    "Real authored file QA failed: " + (p.stdout + p.stderr)[-1600:])

        if args.verify_apache_uploads:
            # Real policy emitted by the disposable WordPress Form runtime.
            # Apache listens only on localhost and a temporary high port.
            policy = site / "wp-content/uploads/elementor/forms/.htaccess"
            p = execute([
                sys.executable, str(ROOT / "tools/qa_apache_form_policy.py"),
                "--htaccess", str(policy),
            ], timeout=35)
            require(record("real disposable Apache Form upload executable denial",
                           p.returncode == 0 and "QA_APACHE_JSON=" in p.stdout,
                           {"exit": p.returncode,
                            "checks": p.stdout.strip().splitlines()[-9:]}),
                    "Apache upload policy test failed: " +
                    (p.stdout + p.stderr)[-900:])

        if args.focus == "runtime":
            # Lightweight fast feedback for file format/security regression
            # tests. No front-end HTTP server, mail, checkout or browser.
            print("QA_RESULTS_JSON=" + json.dumps(observations), flush=True)
            return 0 if all(item["passed"] for item in observations) else 1

        p = wp(
            "eval-file",
            f"wp-content/plugins/{plugin_folder}/tests/fixtures/seed_synthetic.php",
            environment={"ZMP_ISOLATED_QA": "yes"},
        )
        require(record("seed only synthetic page/product/cart/checkout",
                       p.returncode == 0), "Seed failure: " + (p.stdout + p.stderr)[-600:])
        try:
            fixtures = json.loads(p.stdout.strip())
        except json.JSONDecodeError as e:
            raise RuntimeError("Synthetic fixture did not output JSON") from e

        template_seed = wp(
            "eval-file",
            f"wp-content/plugins/{plugin_folder}/tests/fixtures/seed_theme_popup.php",
            environment={"ZMP_ISOLATED_QA": "yes"},
        )
        try:
            theme_fixtures = json.loads(template_seed.stdout.strip())
        except ValueError:
            theme_fixtures = {}
        require(record("seed isolated Header and Popup theme conditions",
                       template_seed.returncode == 0
                       and theme_fixtures.get("types_registered", {}).get("header") is True
                       and theme_fixtures.get("types_registered", {}).get("popup") is True
                       and theme_fixtures.get("conditions_saved", {}).get("header") is True
                       and all(theme_fixtures.get("conditions_saved", {}).get(key) is True
                               for key in ("popup", "scroll_popup", "exit_popup"))
                       and theme_fixtures.get("documents", {}).get("header", {}).get("location") == "header"
                       and all(theme_fixtures.get("documents", {}).get(key, {}).get("location") == "popup"
                               for key in ("popup", "scroll_popup", "exit_popup")),
                       {"exit": template_seed.returncode, "fixtures": theme_fixtures}),
                "Cannot register isolated Theme Builder/Popup fixtures")

        nav_seed = wp(
            "eval-file",
            f"wp-content/plugins/{plugin_folder}/tests/fixtures/seed_posts_nav.php",
            environment={"ZMP_ISOLATED_QA": "yes"},
        )
        try:
            nav_fixtures = json.loads(nav_seed.stdout.strip())
        except ValueError:
            nav_fixtures = {}
        require(record("seed isolated Posts and WordPress Menu widget fixtures",
                       nav_seed.returncode == 0
                       and nav_fixtures.get("page", 0) > 0
                       and nav_fixtures.get("menu", 0) > 0
                       and nav_fixtures.get("nav_id") == "9a0c1d01"
                       and nav_fixtures.get("posts_id") == "9a0c1d02",
                       {"exit": nav_seed.returncode, "fixtures": nav_fixtures}),
                "Cannot create isolated Posts/Nav Menu widgets: " +
                (nav_seed.stderr or nav_seed.stdout)[-500:])

        # The offline BACS method permits a complete synthetic order flow
        # without contacting a payment processor, sending money, or email.
        # These options exist ONLY in the fresh disposable QA WordPress DB.
        offline_setup = wp("eval",
            '$g=get_option("woocommerce_bacs_settings",[]);'
            '$g=is_array($g)?$g:[];'
            '$g["enabled"]="yes";$g["title"]="QA offline bank transfer";'
            'update_option("woocommerce_bacs_settings",$g);'
            'update_option("woocommerce_enable_guest_checkout","yes");'
            'echo wp_json_encode(["gateway_enabled"=>'
            'get_option("woocommerce_bacs_settings")["enabled"],'
            '"guest_checkout"=>get_option("woocommerce_enable_guest_checkout")]);'
        )
        try:
            offline_data = json.loads(offline_setup.stdout.strip())
        except ValueError:
            offline_data = {}
        require(record("enable offline checkout only in disposable database",
                       offline_setup.returncode == 0
                       and offline_data.get("gateway_enabled") == "yes"
                       and offline_data.get("guest_checkout") == "yes",
                       {"exit": offline_setup.returncode, "options": offline_data}),
                "Could not enable isolated offline checkout")

        product_debug = (
            '$p=wc_get_product(' + str(fixtures["product"]) + ');'
            'echo wp_json_encode(["exists"=>(bool)$p,'
            '"price"=>$p ? $p->get_price() : null,'
            '"purchasable"=>$p ? $p->is_purchasable() : false,'
            '"published"=>get_post_status(' + str(fixtures["product"]) + '),'
            '"cart_initialized"=>(bool)WC()->cart]);'
        )
        inspect_product = wp("eval", product_debug)
        try:
            product_data = json.loads(inspect_product.stdout.strip())
        except ValueError:
            product_data = {}
        record("synthetic WooCommerce product purchasable",
               inspect_product.returncode == 0
               and product_data.get("purchasable") is True,
               product_data)

        if args.web_server == "nginx-fpm":
            # Keep the existing synthetic site and all test-only credentials
            # internal to Docker. Two services can handle Elementor's multiple
            # concurrent JS/CSS/REST requests without the one-worker PHP -S.
            php_service = "zmp-qa-php-" + tag
            fpm_ini = temp / "zmp-qa-fpm.ini"
            fpm_ini.write_text(
                "memory_limit = 512M\n"
                "max_execution_time = 120\n"
                "display_errors = Off\n"
                "log_errors = On\n"
            )
            conf = temp / "zmp-qa-nginx.conf"
            conf.write_text(r"""server {
    listen 8080;
    server_name web;
    root /var/www/html;
    index index.php;
    client_max_body_size 16m;
    access_log off;
    error_log /dev/stderr warn;
    location / {
        try_files $uri $uri/ /index.php?$args;
    }
    # Explicitly model the no-executable-upload policy. Nginx ignores
    # Apache .htaccess files, so PHP-FPM must never receive uploaded scripts.
    location ~* ^/wp-content/uploads/.*\.(?:php[0-9]*|phtml|pht|phtm|phar|cgi|pl|py|rb|shtml|asp|aspx)(?:\.|$) {
        return 403;
    }
    # Serve saved Form attachments as downloads, never as renderable
    # HTML/scripts. This regex comes after the executable-extension deny
    # above and therefore cannot override that deny.
    location ~* ^/wp-content/uploads/elementor/forms/ {
        add_header Content-Disposition "attachment" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Cache-Control "private, no-store" always;
        try_files $uri =404;
    }
    location ~ \.php$ {
        try_files $uri =404;
        include /etc/nginx/fastcgi_params;
        fastcgi_pass php:9000;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME /var/www/html$fastcgi_script_name;
        fastcgi_param DOCUMENT_ROOT /var/www/html;
        fastcgi_param HTTP_HOST $http_host;
        fastcgi_read_timeout 120s;
        fastcgi_buffer_size 64k;
        fastcgi_buffers 32 64k;
    }
    location ~ /\.(?!well-known) {
        deny all;
    }
}
""")
            # Only synthetic wp-content is writable by the test PHP worker.
            # Never change the source installation or the Git repository.
            wp_content = site / "wp-content"
            wp_content.mkdir(exist_ok=True)
            ownership = docker([
                "run", "--rm", "--network", "none", "--memory=128m",
                "-v", str(wp_content) + ":/synthetic-content",
                "--entrypoint", "chown", args.clean_image,
                "-R", "33:33", "/synthetic-content",
            ], 100)
            require(record("make disposable wp-content writable to PHP-FPM",
                           ownership.returncode == 0),
                    "Synthetic WP content permission setup failed")

            backend = docker([
                "run", "-d", "--name", php_service, "--network", network,
                "--network-alias", "php", "--memory=1700m", "--cpus=2",
                "-e", "ZMP_QA_EDITOR_TOKEN=" + editor_login_token,
                "-v", str(site) + ":/var/www/html",
                "-v", str(fpm_ini) + ":/usr/local/etc/php/conf.d/zz-zmp-qa.ini:ro",
                "-w", "/var/www/html",
                "--entrypoint", "php-fpm", args.php_image,
                "-F",
            ], 55)
            require(backend.returncode == 0,
                    "Failed to start synthetic PHP-FPM: " + backend.stderr[-400:])
            active.append(("container", php_service))

            frontend = docker([
                "run", "-d", "--name", web, "--network", network,
                "--network-alias", "web", "--memory=280m", "--cpus=1",
                "-v", str(site) + ":/var/www/html:ro",
                "-v", str(conf) + ":/etc/nginx/conf.d/default.conf:ro",
                "--entrypoint", "nginx", args.nginx_image,
                "-g", "daemon off;",
            ], 55)
            require(frontend.returncode == 0,
                    "Failed to start isolated Nginx: " + frontend.stderr[-400:])
            active.append(("container", web))
            record("Nginx/PHP-FPM private multiworker web stack", True)
        else:
            p = docker([
                "run", "-d", "--name", web, "--network", network,
                "--network-alias", "web", "--memory=900m", "--cpus=1",
                "-v", str(site) + ":/var/www/html", "-w", "/var/www/html",
                "-e", "ZMP_QA_EDITOR_TOKEN=" + editor_login_token,
                "--entrypoint", "php", args.php_image,
                "-S", "0.0.0.0:8080", "-t", "/var/www/html",
            ], 55)
            require(p.returncode == 0, "Failed to start isolated PHP web server")
            active.append(("container", web))
        cookie_dir = temp / "http-cookies"
        cookie_dir.mkdir()

        def request(path, fields=None, cookie_file_name="cookies.txt"):
            # Keep privileged synthetic editor cookies out of guest cart tests.
            require(cookie_file_name in ("cookies.txt", "editor-cookies.txt",
                                         "checkout-cookies.txt"),
                    "Unexpected QA cookie file")
            cookie_path = "/qa-cookies/" + cookie_file_name
            command = [
                "run", "--rm", "--network", network, "--memory=128m",
                "--user", "0:0",  # curlimages default UID cannot write private test cookie jar.
                "-v", str(cookie_dir) + ":/qa-cookies",
                "--entrypoint", "curl", args.curl_image,
                "-sS", "--max-time", "65", "--max-redirs", "6",
                "--noproxy", "*", "-L",
                "-c", cookie_path, "-b", cookie_path,
                "-w", "\n__ZMP_HTTP_STATUS__:%{http_code}", "http://web:8080/" + path,
            ]
            if fields:
                command.extend(["-X", "POST"])
                for key, value in fields.items():
                    command.extend(["--data-urlencode", key + "=" + str(value)])
            result = docker(command, 75)
            if result.returncode != 0:
                return 0, "", result.stderr[-650:]
            body, separator, status = result.stdout.rpartition(
                "\n__ZMP_HTTP_STATUS__:"
            )
            if not separator:
                return 0, result.stdout, "Missing HTTP status"
            return int(status.strip()), body, ""

        if args.web_server == "nginx-fpm":
            for blocked_extension in ("php", "php8", "phtml", "phar",
                                      "php.jpg", "phtml.png", "phar.webp"):
                denied, denied_body, denied_err = request(
                    "wp-content/uploads/elementor/forms/"
                    "__zmp_nonexistent_private_qa_probe__." + blocked_extension
                )
                record("Nginx synthetic upload execution denied: " + blocked_extension,
                       denied == 403,
                       {"status": denied, "error": denied_err,
                        "test_scope": "Private disposable Nginx, no uploaded file"})

        if args.web_server == "nginx-fpm":
            attachment = docker([
                "run", "--rm", "--network", network, "--memory=128m",
                "--entrypoint", "curl", args.curl_image,
                "-sS", "--max-time", "18", "--noproxy", "*",
                "-D", "-", "-o", "/dev/null",
                "http://web:8080/wp-content/uploads/elementor/forms/zmp-qa-header-fixture.txt",
            ], 27)
            response_headers = attachment.stdout.lower()
            record("Nginx synthetic Form uploads require attachment and nosniff headers",
                   attachment.returncode == 0
                   and "http/1.1 200" in response_headers
                   and "content-disposition: attachment" in response_headers
                   and "x-content-type-options: nosniff" in response_headers
                   and "cache-control: private, no-store" in response_headers,
                   {"headers": response_headers[-700:],
                    "exit": attachment.returncode,
                    "test_scope": "Private disposable Nginx Form upload file"})

        for i in range(12):
            status, html, err = request("?page_id=" + str(fixtures["page"]))
            if status:
                break
            time.sleep(2)
        record("Elementor page HTTP 200", status == 200,
               {"status": status, "error": err})
        record("Elementor heading rendered", "ZiloMentor Synthetic Heading" in html)
        # Inspect ONLY the synthetic Heading's opening tag: a site may
        # legitimately contain other onclick strings in theme scripts.
        match = re.search(
            r'<[^>]*\bdata-id=[^ >]*1a2b3c01[^>]*>', html
        )
        wrapper = match.group(0) if match else ""
        record("Legacy custom HTML attributes reject executable injection",
               bool(wrapper)
               and 'data-zmp-security="visible"' in wrapper
               and "aria-label=" in wrapper
               and "onclick=" not in wrapper
               and "onmouseover=" not in wrapper
               and "javascript:" not in wrapper,
               {"widget_found": bool(wrapper),
                "safe_data_retained": 'data-zmp-security="visible"' in wrapper,
                "aria_retained": "aria-label=" in wrapper,
                "unsafe_event_present": "onclick=" in wrapper or "onmouseover=" in wrapper,
                "unsafe_protocol_present": "javascript:" in wrapper})

        record("Elementor Form widget rendered", 'elementor-form' in html and '<form' in html)
        widget_status, widget_body, widget_err = request(
            "?page_id=" + str(nav_fixtures["page"])
        )
        record("Pro WordPress Navigation Menu renders synthetic WP link",
               widget_status == 200
               and nav_fixtures["menu_label"] in widget_body
               and 'elementor-widget-nav-menu' in widget_body,
               {"status": widget_status,
                "menu_link_present": nav_fixtures["menu_label"] in widget_body,
                "nav_widget_present": 'elementor-widget-nav-menu' in widget_body,
                "error": widget_err})
        record("Pro Posts widget renders synthetic published post",
               widget_status == 200
               and nav_fixtures["posts_label"] in widget_body
               and 'elementor-widget-posts' in widget_body,
               {"status": widget_status,
                "post_marker_present": nav_fixtures["posts_label"] in widget_body,
                "posts_widget_present": 'elementor-widget-posts' in widget_body,
                "error": widget_err})
        plain_status, plain_html, plain_err = request(
            "?page_id=" + str(fixtures["plain"])
        )
        record("Ordinary WordPress page content displays in Fiore",
               plain_status == 200 and
               "ZiloMentor Synthetic Plain Content Marker" in plain_html,
               {"status": plain_status, "bytes": len(plain_html),
                "marker_present": "ZiloMentor Synthetic Plain Content Marker" in plain_html,
                "error": plain_err})
        record("ACF dynamic value renders inside Elementor heading",
               "ZiloMentor Synthetic ACF Value" in html,
               {"dynamic_value_present": "ZiloMentor Synthetic ACF Value" in html})

        # Header/Popup conditions must be limited to their synthetic target,
        # rather than leaking onto other posts or the working WooCommerce pages.
        for page_label, page_id, expect_match in (
            ("target", theme_fixtures["target"], True),
            ("unrelated", fixtures["plain"], False),
        ):
            theme_status, theme_body, theme_err = request(
                "?page_id=" + str(page_id) + "&zmp_qa_theme_popup=1"
            )
            try:
                theme_data = json.loads(theme_body)
            except ValueError:
                theme_data = {}
            target_doc_ids = theme_fixtures.get("documents", {})
            header_id = target_doc_ids.get("header", {}).get("id")
            popup_id = target_doc_ids.get("popup", {}).get("id")
            theme_passed = (
                theme_status == 200
                and ((header_id in theme_data.get("header_doc_ids", [])) is expect_match)
                and ((popup_id in theme_data.get("popup_doc_ids", [])) is expect_match)
                and (theme_data.get("header_marker") is expect_match)
                and (theme_data.get("popup_marker") is expect_match)
            )
            record("Theme Builder and Popup condition/render: " + page_label,
                   theme_passed,
                   {"status": theme_status, "render": theme_data, "error": theme_err})

        # Dedicated targets ensure Page Load, On Scroll and Exit Intent
        # do not mask one another or cross page-specific conditions.
        for label, target, expected_popup, marker_key in (
            ("scroll", theme_fixtures["scroll_target"], "scroll_popup", "scroll_popup_marker"),
            ("exit", theme_fixtures["exit_target"], "exit_popup", "exit_popup_marker"),
        ):
            trigger_status, trigger_body, trigger_err = request(
                "?page_id=" + str(target) + "&zmp_qa_theme_popup=1"
            )
            try:
                trigger_data = json.loads(trigger_body)
            except ValueError:
                trigger_data = {}
            expected_id = theme_fixtures["documents"][expected_popup]["id"]
            excluded_ids = (
                theme_fixtures["documents"][k]["id"]
                for k in ("popup", "scroll_popup", "exit_popup") if k != expected_popup
            )
            shown = trigger_data.get("popup_doc_ids", [])
            record("Popup page-specific condition: " + label,
                   trigger_status == 200 and expected_id in shown
                   and all(other not in shown for other in excluded_ids)
                   and trigger_data.get(marker_key) is True
                   and trigger_data.get("header_marker") is False,
                   {"status": trigger_status, "render": trigger_data,
                    "error": trigger_err})

        if args.frontend_playwright_image is not None:
            # Real browser Popup test: open/close via the product's own JS API,
            # with no public host ports or external network access.
            browser_test = plugins_path / plugin_folder / "tests/browser_theme_popup.js"
            require(browser_test.is_file(), "Missing private Popup browser test")
            browser_name = "zmp-qa-popup-" + tag
            browser_cmd = [
                "run", "--rm", "--name", browser_name,
                "--network", network, "--memory=1500m", "--cpus=2",
                "--shm-size=128m",
                "-e", "NODE_PATH=/usr/lib/node_modules",
                "-e", "ZMP_QA_TARGET_ID=" + str(theme_fixtures["target"]),
                "-e", "ZMP_QA_UNRELATED_ID=" + str(fixtures["plain"]),
                "-e", "ZMP_QA_POPUP_ID=" +
                    str(theme_fixtures["documents"]["popup"]["id"]),
                "-e", "ZMP_QA_SCROLL_TARGET_ID=" + str(theme_fixtures["scroll_target"]),
                "-e", "ZMP_QA_EXIT_TARGET_ID=" + str(theme_fixtures["exit_target"]),
                "-e", "ZMP_QA_SCROLL_POPUP_ID=" +
                    str(theme_fixtures["documents"]["scroll_popup"]["id"]),
                "-e", "ZMP_QA_EXIT_POPUP_ID=" +
                    str(theme_fixtures["documents"]["exit_popup"]["id"]),
                "-v", str(browser_test) + ":/qa/theme_popup.js:ro",
                "--entrypoint", "timeout", args.frontend_playwright_image,
                "--signal=TERM", "--kill-after=5s", "65s",
                "node", "/qa/theme_popup.js",
            ]
            try:
                browser_run = docker(browser_cmd, timeout=85)
                result_line = next((
                    line[len("ZMP_THEME_POPUP_BROWSER_JSON="):]
                    for line in browser_run.stdout.splitlines()
                    if line.startswith("ZMP_THEME_POPUP_BROWSER_JSON=")
                ), None)
                try:
                    result_data = json.loads(result_line) if result_line else {}
                except ValueError:
                    result_data = {}
                record("Chromium Popup opens, renders, closes and respects conditions",
                       browser_run.returncode == 0
                       and all(result_data.get(key) is True for key in (
                           "loadedTarget", "loadedUnrelated", "headerVisible",
                           "popupApiReady", "popupDocumentRegistered",
                           "popupModalOpened", "popupHeadingVisible",
                           "popupModalClosed", "popupAutoOpened",
                           "popupAutoOpenedMobile", "unrelatedPopupAbsent",
                           "unrelatedHeaderAbsent",
                           "scrollPopupAbsentBeforeScroll", "scrollPopupOpenedByScroll",
                           "exitPopupAbsentBeforeIntent", "exitPopupOpenedByIntent",
                           "unrelatedScrollPopupAbsent", "unrelatedExitPopupAbsent",
                       ))
                       and result_data.get("pageErrors") == 0
                       and result_data.get("failedLocalRequests") == 0,
                       {"exit": browser_run.returncode, "checks": result_data})
            except subprocess.TimeoutExpired:
                record("Chromium Popup opens, renders, closes and respects conditions",
                       False, {"hard_timeout": True})
            finally:
                docker(["rm", "-f", browser_name], 20)

        # Send two synthetic form requests; no mail can leave this network.
        form_request = {
            "action": "elementor_pro_forms_send_form",
            "post_id": str(fixtures["page"]),
            "queried_id": str(fixtures["page"]),
            "form_id": str(fixtures["form"]),
            "form_fields[email]": "invalid",
        }
        status, body, error = request("wp-admin/admin-ajax.php", form_request)
        try:
            data = json.loads(body)
        except ValueError:
            data = None
        record("invalid email form submission rejected",
               status == 200 and isinstance(data, dict)
               and data.get("success") is False,
               {"status": status, "response": body[-350:], "error": error})

        form_request["form_fields[email]"] = "qa-recipient@example.invalid"
        status, body, error = request("wp-admin/admin-ajax.php", form_request)
        try:
            data = json.loads(body)
        except ValueError:
            data = None
        record("valid form submission accepted",
               status == 200 and isinstance(data, dict)
               and data.get("success") is True,
               {"status": status, "response": body[-350:], "error": error})

        # The same saved Elementor Form exists in all three restricted
        # documents. Guest POSTs must be refused before executing actions.
        for visibility, key in (
            ("draft", "form_draft_page"),
            ("private", "form_private_page"),
            ("password-protected", "form_password_page"),
        ):
            blocked_request = dict(form_request, post_id=str(fixtures[key]))
            blocked_status, blocked_body, blocked_error = request(
                "wp-admin/admin-ajax.php", blocked_request
            )
            try:
                blocked_data = json.loads(blocked_body)
            except ValueError:
                blocked_data = None
            record("anonymous Form rejects " + visibility + " document",
                   blocked_status == 200
                   and isinstance(blocked_data, dict)
                   and blocked_data.get("success") is False,
                   {"status": blocked_status,
                    "response": blocked_body[-350:],
                    "error": blocked_error})

        acf_status, acf_body, acf_error = request(
            "?page_id=" + str(fixtures["page"]) + "&zmp_qa_acf_tag=1"
        )
        try:
            acf_result = json.loads(acf_body)
        except ValueError:
            acf_result = {}
        record("ACF Pro dynamic tag renders synthetic text field",
               acf_status == 200
               and acf_result.get("acf_text_tag") is True
               and acf_result.get("tag_value") == "ZiloMentor Synthetic ACF Value",
               {"status": acf_status, "result": acf_result, "error": acf_error})

        if args.browser_image is not None:
            # Browser has access only to this disposable internal Docker network.
            for width, height in ((1366, 768), (390, 844)):
                command = [
                    "run", "--rm", "--network", network,
                    "--memory=1300m", "--cpus=2", "--shm-size=128m",
                    "--entrypoint", args.browser_bin, args.browser_image,
                    "--no-sandbox", "--headless=new", "--disable-gpu",
                    "--disable-dev-shm-usage", "--disable-background-networking",
                    "--disable-extensions", "--no-first-run", "--no-proxy-server",
                    "--virtual-time-budget=4000",
                    "--window-size=" + str(width) + "," + str(height),
                    "--dump-dom", "http://web:8080/?page_id=" + str(fixtures["page"]),
                ]
                browser = docker(command, timeout=95)
                markup = browser.stdout
                record(
                    "Chromium Elementor+ACF DOM " + str(width) + "x" + str(height),
                    browser.returncode == 0
                    and "ZiloMentor Synthetic Heading" in markup
                    and "ZiloMentor Synthetic ACF Value" in markup
                    and "elementor-form" in markup,
                    {
                        "browser_exit": browser.returncode,
                        "dom_bytes": len(markup),
                        "heading_present": "ZiloMentor Synthetic Heading" in markup,
                        "acf_value_present": "ZiloMentor Synthetic ACF Value" in markup,
                        "form_present": "elementor-form" in markup,
                        "browser_error_tail": browser.stderr[-280:] if browser.returncode else "",
                    },
                )

        if args.browser_image is not None or args.editor_playwright_image is not None:
            # An isolated synthetic WordPress user and ephemeral token only.
            editor_login_path = (
                "?zmp_qa_editor_login=" + editor_login_token
                + "&zmp_qa_page=" + str(fixtures["page"])
            )
            editor_http_status, editor_http, _ = request(
                editor_login_path, cookie_file_name="editor-cookies.txt"
            )
            editor_http_lower = editor_http.lower()
            editor_http_ok = (
                editor_http_status == 200
                and "elementor-editor" in editor_http_lower
                and "elementor-panel" in editor_http_lower
                and 'id="loginform"' not in editor_http_lower
            )
            record("Authenticated Elementor editor HTTP shell",
                   editor_http_ok,
                   {
                       "status": editor_http_status,
                       "html_bytes": len(editor_http),
                       "editor_marker_present": "elementor-editor" in editor_http_lower,
                       "panel_marker_present": "elementor-panel" in editor_http_lower,
                       "login_form_present": 'id="loginform"' in editor_http_lower,
                       "page_title": editor_http_lower.split("<title>", 1)[-1]
                           .split("</title>", 1)[0][:100] if "<title>" in editor_http_lower else "",
                   })

            if editor_http_ok and args.editor_playwright_image is not None:
                # Node's Playwright API navigates at commit, avoiding Chromium
                # --dump-dom hanging on asynchronous editor/background assets.
                editor_name = "zmp-qa-editor-" + tag
                js = plugins_path / plugin_folder / "tests/browser_editor_smoke.js"
                require(js.is_file(), "Editor smoke test script missing")
                editor_command = [
                    "run", "--rm", "--name", editor_name,
                    "--network", network, "--memory=1600m", "--cpus=2",
                    "--shm-size=128m",
                    "-e", "NODE_PATH=/usr/lib/node_modules",
                    "-e", "ZMP_QA_EDITOR_TOKEN=" + editor_login_token,
                    "-e", "ZMP_QA_PAGE_ID=" + str(fixtures["page"]),
                    "-v", str(js) + ":/qa/editor_smoke.js:ro",
                    "--entrypoint", "timeout", args.editor_playwright_image,
                    "--signal=TERM", "--kill-after=5s", "55s",
                    "node", "/qa/editor_smoke.js",
                ]
                editor_state = {}
                try:
                    editor_run = docker(editor_command, timeout=70)
                    result_line = next((
                        line[len("ZMP_EDITOR_JSON="):]
                        for line in editor_run.stdout.splitlines()
                        if line.startswith("ZMP_EDITOR_JSON=")
                    ), None)
                    if result_line:
                        try:
                            editor_state = json.loads(result_line)
                        except ValueError:
                            editor_state = {}
                    else:
                        editor_state = {}
                    editor_ok = (
                        editor_run.returncode == 0
                        and editor_state.get("navigationCommitted") is True
                        and editor_state.get("authenticatedEditorPage") is True
                        and editor_state.get("panelPresent") is True
                        and editor_state.get("previewPresent") is True
                    )
                    record("Authenticated Playwright Elementor editor shell",
                           editor_ok,
                           {
                               "exit_code": editor_run.returncode,
                               "state": editor_state,
                               "hard_timeout": editor_run.returncode in (124, 137),
                           })
                except subprocess.TimeoutExpired:
                    record("Authenticated Playwright Elementor editor shell", False,
                           {"hard_timeout": True, "reason": "QA browser exceeded 70s"})
                finally:
                    # Only clean up this run's randomly named transient browser.
                    docker(["rm", "-f", editor_name], 20)

                # Baseline on exactly the same synthetic WP/Fiore system,
                # with ZiloMentor Pro disabled. This helps distinguish a
                # slow/uninitialized free Elementor editor from our fork.
                inactive = wp("plugin", "deactivate", plugin_folder)
                if inactive.returncode == 0:
                    baseline_state = {}
                    try:
                        base_run = docker(editor_command, timeout=70)
                        baseline_line = next((
                            line[len("ZMP_EDITOR_JSON="):]
                            for line in base_run.stdout.splitlines()
                            if line.startswith("ZMP_EDITOR_JSON=")
                        ), None)
                        if baseline_line:
                            try:
                                baseline_state = json.loads(baseline_line)
                            except ValueError:
                                baseline_state = {}
                        record("Free Elementor editor baseline without ZiloMentor",
                               base_run.returncode == 0
                               and baseline_state.get("navigationCommitted") is True,
                               {
                                   "exit_code": base_run.returncode,
                                   "state": baseline_state,
                                   "test_scope": "Same disposable Fiore site, ZiloMentor disabled",
                               })
                        free_controls = baseline_state.get("panelControlCount", 0)
                        fork_controls = editor_state.get("panelControlCount", 0)
                        free_text = baseline_state.get("panelTextLength", 0)
                        fork_text = editor_state.get("panelTextLength", 0)
                        comparable = free_controls >= 30 and free_text >= 500
                        record("Free Elementor editor baseline sufficiently populated",
                               comparable,
                               {
                                   "baseline_controls": free_controls,
                                   "baseline_text_length": free_text,
                                   "panel_populated": baseline_state.get("panelPopulatedWaitPassed"),
                               })
                        if comparable:
                            # A fork must not lose most of the ordinary widget
                            # controls or content relative to the same-site free
                            # Elementor baseline. Earlier >0-only was too weak.
                            record("ZiloMentor editor panel matches baseline content",
                                   fork_controls >= free_controls * 0.5
                                   and fork_text >= free_text * 0.5
                                   and editor_state.get("panelPopulatedWaitPassed") is True,
                                   {
                                       "fork_controls": fork_controls,
                                       "baseline_controls": free_controls,
                                       "fork_panel_text": fork_text,
                                       "baseline_panel_text": free_text,
                                       "fork_populated": editor_state.get("panelPopulatedWaitPassed"),
                                   })
                        if baseline_state.get("titleControlMatchesSynthetic") is True:
                            record("ZiloMentor Heading title selection matches baseline",
                                   editor_state.get("titleControlMatchesSynthetic") is True,
                                   {
                                       "fork_heading_selected": editor_state.get("headingSelected"),
                                       "fork_title_control": editor_state.get("titleControlPresent"),
                                       "baseline_heading_selected": baseline_state.get("headingSelected"),
                                   })
                    except subprocess.TimeoutExpired:
                        record("Free Elementor editor baseline without ZiloMentor",
                               False, {"hard_timeout": True})
                    finally:
                        docker(["rm", "-f", editor_name], 20)
                        restore = wp("plugin", "activate", plugin_folder)
                        require(record("Restore ZiloMentor in isolated test",
                                       restore.returncode == 0),
                                "Failed to restore ZiloMentor in synthetic WP")
                else:
                    record("Free Elementor editor baseline without ZiloMentor",
                           False, {"deactivation_failed": True})
        if args.verify_editor_save:
            # Re-activate ZiloMentor after the free Elementor baseline first.
            # Then run an entirely separate browser on this disposable site.
            # No real pages, credentials or user data are involved.
            save_name = "zmp-qa-save-" + tag
            save_cmd = [
                "run", "--rm", "--name", save_name,
                "--network", network, "--memory=1600m", "--cpus=2",
                "--shm-size=128m",
                "-e", "NODE_PATH=/usr/lib/node_modules",
                "-e", "ZMP_QA_EDITOR_TOKEN=" + editor_login_token,
                "-e", "ZMP_QA_PAGE_ID=" + str(fixtures["page"]),
                "-e", "ZMP_QA_SAVE_TEST=yes",
                "-v", str(js) + ":/qa/editor_smoke.js:ro",
                "--entrypoint", "timeout", args.editor_playwright_image,
                "--signal=TERM", "--kill-after=5s", "65s",
                "node", "/qa/editor_smoke.js",
            ]
            save_state = {}
            try:
                run = docker(save_cmd, timeout=85)
                result_line = next((
                    line[len("ZMP_EDITOR_JSON="):]
                    for line in run.stdout.splitlines()
                    if line.startswith("ZMP_EDITOR_JSON=")
                ), None)
                if result_line:
                    try:
                        save_state = json.loads(result_line)
                    except ValueError:
                        save_state = {}
                record("Synthetic Elementor save action completed",
                       run.returncode == 0 and save_state.get("saveActionCompleted") is True,
                       {"exit_code": run.returncode,
                        "save_state": {k: v for k, v in save_state.items()
                                       if k.startswith("save") or k.startswith("edited")}})
            except subprocess.TimeoutExpired:
                record("Synthetic Elementor save action completed", False,
                       {"hard_timeout": True})
            finally:
                docker(["rm", "-f", save_name], 20)
            # Independent server-side verification of the stored post meta,
            # not merely the visible text in the browser.
            verify_code = (
                '$d=json_decode(get_post_meta(' + str(fixtures["page"]) +
                ', "_elementor_data", true), true);'
                '$found=false;$saved=false;'
                '$scan=function($n)use(&$scan,&$found,&$saved){'
                'foreach((array)$n as $item){if(!is_array($item))continue;'
                'if(($item["id"]??"")==="1a2b3c01"){$found=true;'
                '$saved=($item["settings"]["title"]??"")==="ZiloMentor QA Saved Heading";}'
                'if(!empty($item["elements"]))$scan($item["elements"]);}};'
                '$scan($d);echo wp_json_encode(["heading_exists"=>$found,"saved"=>$saved]);'
            )
            result = wp("eval", verify_code)
            try:
                verify_data = json.loads(result.stdout.strip())
            except ValueError:
                verify_data = {}
            record("Synthetic Heading title persisted to WordPress database",
                   result.returncode == 0 and verify_data.get("saved") is True,
                   {"wpcli_exit": result.returncode, "verification": verify_data})

        if args.verify_editor_history:
            history_js = plugins_path / plugin_folder / "tests/browser_editor_history.js"
            require(history_js.is_file(), "Missing private real Elementor History regression")
            history_name = "zmp-qa-history-" + tag
            history_cmd = [
                "run", "--rm", "--name", history_name,
                "--network", network, "--memory=1600m", "--cpus=2",
                "--shm-size=128m",
                "-e", "NODE_PATH=/usr/lib/node_modules",
                "-e", "ZMP_QA_EDITOR_TOKEN=" + editor_login_token,
                "-e", "ZMP_QA_PAGE_ID=" + str(fixtures["history_page"]),
                "-e", "ZMP_QA_HISTORY=yes",
                "-v", str(history_js) + ":/qa/history.js:ro",
                "--entrypoint", "timeout", args.editor_playwright_image,
                "--signal=TERM", "--kill-after=5s", "90s",
                "node", "/qa/history.js",
            ]
            history_state = {}
            try:
                history_run = docker(history_cmd, timeout=110)
                history_line = next((
                    line[len("ZMP_HISTORY_EDITOR_JSON="):]
                    for line in history_run.stdout.splitlines()
                    if line.startswith("ZMP_HISTORY_EDITOR_JSON=")
                ), None)
                if history_line:
                    try:
                        history_state = json.loads(history_line)
                    except ValueError:
                        history_state = {}
                record("Real Elementor History Undo and Redo before Publish",
                       history_run.returncode == 0
                       and all(history_state.get(k) is True for k in (
                           "authenticated", "headingVisible", "titleSelected",
                           "initialMatched", "editApplied", "undoCommand",
                           "undoReverted", "redoCommand", "redoReapplied",
                           "published",
                       ))
                       and all(history_state.get(k) == 0 for k in (
                           "pageErrors", "httpErrors", "localFailures",
                       )),
                       {"exit_code": history_run.returncode,
                        "state": history_state})
            except subprocess.TimeoutExpired:
                record("Real Elementor History Undo and Redo before Publish",
                       False, {"hard_timeout": True})
            finally:
                docker(["rm", "-f", history_name], 20)
            history_verify = (
                '$id=' + str(fixtures["history_page"]) + ';'
                '$d=json_decode(get_post_meta($id,"_elementor_data",true),true);'
                '$saved=false;'
                '$scan=function($n)use(&$scan,&$saved){'
                'foreach((array)$n as $item){if(!is_array($item))continue;'
                'if(($item["id"]??"")==="1a2b3c01"){'
                '$saved=(($item["widgetType"]??"")==="heading"&&'
                '($item["settings"]["title"]??"")==="ZiloMentor QA History Redo Heading");}'
                'if(!empty($item["elements"]))$scan($item["elements"]);}};'
                '$scan($d);echo wp_json_encode(["saved"=>$saved]);'
            )
            history_db_run = wp("eval", history_verify)
            try:
                history_db = json.loads(history_db_run.stdout.strip())
            except ValueError:
                history_db = {}
            record("Redone Heading title persisted in WordPress after History Publish",
                   history_db_run.returncode == 0
                   and history_db.get("saved") is True,
                   {"exit": history_db_run.returncode,
                    "verification": history_db})

        if args.verify_editor_form_save or args.verify_editor_form_fields:
            # Separate opt-in real editor interaction. It changes only the
            # hard-coded Form widget in this disposable WordPress database.
            form_js = plugins_path / plugin_folder / "tests/browser_editor_form_save.js"
            require(form_js.is_file(), "Missing isolated Pro Form editor QA")
            form_browser_name = "zmp-qa-form-save-" + tag
            form_cmd = [
                "run", "--rm", "--name", form_browser_name,
                "--network", network, "--memory=1600m", "--cpus=2",
                "--shm-size=128m",
                "-e", "NODE_PATH=/usr/lib/node_modules",
                "-e", "ZMP_QA_EDITOR_TOKEN=" + editor_login_token,
                "-e", "ZMP_QA_PAGE_ID=" + str(fixtures["page"]),
                "-e", "ZMP_QA_FORM_SAVE=yes",
                "-e", "ZMP_QA_FORM_FIELDS=" +
                      ("yes" if args.verify_editor_form_fields else "no"),
                "-v", str(form_js) + ":/qa/editor_form_save.js:ro",
                "--entrypoint", "timeout", args.editor_playwright_image,
                "--signal=TERM", "--kill-after=5s", "80s",
                "node", "/qa/editor_form_save.js",
            ]
            form_state = {}
            try:
                form_run = docker(form_cmd, timeout=100)
                form_line = next((
                    line[len("ZMP_FORM_SAVE_JSON="):]
                    for line in form_run.stdout.splitlines()
                    if line.startswith("ZMP_FORM_SAVE_JSON=")
                ), None)
                try:
                    form_state = json.loads(form_line) if form_line else {}
                except ValueError:
                    form_state = {}
                record("Synthetic Elementor Pro Form changed using editor Publish",
                       form_run.returncode == 0
                       and all(form_state.get(k) is True for k in (
                           "authenticated", "proFormFound", "proFormSelected",
                           "initialFormNameMatched", "editedFormNameMatched",
                           "actualSaveButtonClicked",
                       ))
                       and (not args.verify_editor_form_fields or
                            all(form_state.get(k) is True for k in (
                                "repeaterSectionFound", "repeaterRowOpened",
                                "repeaterLabelVisible", "repeaterLabelChanged",
                            )))
                       and form_state.get("pageErrors") == 0
                       and form_state.get("failedLocalRequests") == 0
                       and form_state.get("localHttpErrors") == 0,
                       {"exit_code": form_run.returncode, "state": form_state})
            except subprocess.TimeoutExpired:
                record("Synthetic Elementor Pro Form changed using editor Publish",
                       False, {"hard_timeout": True})
            finally:
                docker(["rm", "-f", form_browser_name], 20)

            # A separate WP-CLI process validates the actual serialized
            # Elementor model, widget type and unchanged synthetic submit text.
            form_verify = (
                '$d=json_decode(get_post_meta(' + str(fixtures["page"]) +
                ', "_elementor_data", true), true);'
                '$found=false;$saved=false;$unchanged=false;$field_label_saved=false;'
                '$scan=function($n)use(&$scan,&$found,&$saved,&$unchanged,&$field_label_saved){'
                'foreach((array)$n as $item){if(!is_array($item))continue;'
                'if(($item["id"]??"")==="1a2b3c4d"){$found=true;'
                '$saved=(($item["widgetType"]??"")==="form"&&'
                '($item["settings"]["form_name"]??"")==="ZiloMentor QA Saved Form");'
                '$unchanged=($item["settings"]["button_text"]??"")==="Submit";'
                '$fields=$item["settings"]["form_fields"]??[];'
                '$field_label_saved=(($fields[0]["field_label"]??"")==="ZiloMentor QA Saved Email Label");}'
                'if(!empty($item["elements"]))$scan($item["elements"]);}};'
                '$scan($d);echo wp_json_encode(["found"=>$found,'
                '"saved"=>$saved,"button_unchanged"=>$unchanged,'
                '"field_label_saved"=>$field_label_saved]);'
            )
            form_result = wp("eval", form_verify)
            try:
                form_db = json.loads(form_result.stdout.strip())
            except ValueError:
                form_db = {}
            record("Synthetic Pro Form editor value persisted in WordPress database",
                   form_result.returncode == 0
                   and form_db.get("found") is True
                   and form_db.get("saved") is True
                   and form_db.get("button_unchanged") is True
                   and (not args.verify_editor_form_fields or
                        form_db.get("field_label_saved") is True),
                   {"wpcli_exit": form_result.returncode, "verification": form_db})
            form_status, form_html, form_err = request(
                "?page_id=" + str(fixtures["page"])
            )
            record("Saved Pro Form name rendered on isolated frontend",
                   form_status == 200 and
                   'name="ZiloMentor QA Saved Form"' in form_html,
                   {"status": form_status, "error": form_err,
                    "rendered_name_present":
                        'name="ZiloMentor QA Saved Form"' in form_html})

            if args.verify_editor_form_fields:
                record("Saved Form repeater field label appears on synthetic frontend",
                       form_status == 200
                       and "ZiloMentor QA Saved Email Label" in form_html,
                       {"status": form_status,
                        "label_present": "ZiloMentor QA Saved Email Label" in form_html,
                        "error": form_err})

        if args.verify_theme_builder_save:
            # This login token works only on web:8080, for the fixture
            # named exactly ZMP Synthetic Header (elementor_library/header).
            header_id = theme_fixtures["documents"]["header"]["id"]
            theme_js = plugins_path / plugin_folder / "tests/browser_theme_editor_save.js"
            require(theme_js.is_file(), "Missing Theme Builder editor regression")
            theme_browser_name = "zmp-qa-theme-save-" + tag
            theme_cmd = [
                "run", "--rm", "--name", theme_browser_name,
                "--network", network, "--memory=1600m", "--cpus=2",
                "--shm-size=128m",
                "-e", "NODE_PATH=/usr/lib/node_modules",
                "-e", "ZMP_QA_EDITOR_TOKEN=" + editor_login_token,
                "-e", "ZMP_QA_HEADER_ID=" + str(header_id),
                "-e", "ZMP_QA_THEME_SAVE=yes",
                "-v", str(theme_js) + ":/qa/theme_save.js:ro",
                "--entrypoint", "timeout", args.editor_playwright_image,
                "--signal=TERM", "--kill-after=5s", "90s",
                "node", "/qa/theme_save.js",
            ]
            theme_state = {}
            try:
                theme_run = docker(theme_cmd, timeout=110)
                theme_line = next((
                    line[len("ZMP_THEME_SAVE_JSON="):]
                    for line in theme_run.stdout.splitlines()
                    if line.startswith("ZMP_THEME_SAVE_JSON=")
                ), None)
                try:
                    theme_state = json.loads(theme_line) if theme_line else {}
                except ValueError:
                    theme_state = {}
                record("Synthetic Theme Builder Header changed and published in editor",
                       theme_run.returncode == 0 and
                       all(theme_state.get(k) is True for k in (
                           "authenticated", "headerWidgetFound", "headingSelected",
                           "originalMatched", "editedMatched", "saveClicked",
                       )) and
                       all(theme_state.get(k) == 0 for k in (
                           "pageErrors", "httpErrors", "requestFailures",
                       )),
                       {"exit_code": theme_run.returncode, "state": theme_state})
            except subprocess.TimeoutExpired:
                record("Synthetic Theme Builder Header changed and published in editor",
                       False, {"hard_timeout": True})
            finally:
                docker(["rm", "-f", theme_browser_name], 20)

            header_verify = (
                '$id=' + str(header_id) + ';'
                '$type=get_post_meta($id,"_elementor_template_type",true);'
                '$d=json_decode(get_post_meta($id,"_elementor_data",true),true);'
                '$saved=false;'
                '$scan=function($n)use(&$scan,&$saved){'
                'foreach((array)$n as $item){if(!is_array($item))continue;'
                'if(($item["id"]??"")==="7a0b1c01"){'
                '$saved=(($item["widgetType"]??"")==="heading"&&'
                '($item["settings"]["title"]??"")==="ZiloMentor QA Saved Header");}'
                'if(!empty($item["elements"]))$scan($item["elements"]);}};'
                '$scan($d);echo wp_json_encode(["type"=>$type,"saved"=>$saved]);'
            )
            header_result = wp("eval", header_verify)
            try:
                header_db = json.loads(header_result.stdout.strip())
            except ValueError:
                header_db = {}
            record("Theme Builder Header title persisted to WordPress database",
                   header_result.returncode == 0
                   and header_db.get("type") == "header"
                   and header_db.get("saved") is True,
                   {"wpcli_exit": header_result.returncode,
                    "verification": header_db})
            target_status, target_body, target_err = request(
                "?page_id=" + str(theme_fixtures["target"])
                + "&zmp_qa_theme_popup=1"
            )
            unrelated_status, unrelated_body, unrelated_err = request(
                "?page_id=" + str(fixtures["plain"])
                + "&zmp_qa_theme_popup=1"
            )
            try:
                target_data = json.loads(target_body)
                unrelated_data = json.loads(unrelated_body)
            except ValueError:
                target_data = {}
                unrelated_data = {}
            record("Edited Header renders only on its intended synthetic page",
                   target_status == 200 and unrelated_status == 200
                   and target_data.get("header_saved_marker") is True
                   and target_data.get("header_marker") is False
                   and unrelated_data.get("header_saved_marker") is False,
                   {"target_status": target_status,
                    "unrelated_status": unrelated_status,
                    "target_saved": target_data.get("header_saved_marker"),
                    "unrelated_saved": unrelated_data.get("header_saved_marker"),
                    "errors": [target_err, unrelated_err]})

        if args.verify_popup_editor_save:
            # Reuse the same browser-driven edit/Publish path as the Header,
            # but open the real Elementor Popup template and check the
            # persisted Heading plus its original page-specific condition.
            popup_id = theme_fixtures["documents"]["popup"]["id"]
            popup_js = plugins_path / plugin_folder / "tests/browser_theme_editor_save.js"
            require(popup_js.is_file(), "Missing Popup editor publishing regression")
            popup_browser_name = "zmp-qa-popup-save-" + tag
            popup_cmd = [
                "run", "--rm", "--name", popup_browser_name,
                "--network", network, "--memory=1600m", "--cpus=2",
                "--shm-size=128m",
                "-e", "NODE_PATH=/usr/lib/node_modules",
                "-e", "ZMP_QA_EDITOR_TOKEN=" + editor_login_token,
                "-e", "ZMP_QA_TEMPLATE_ID=" + str(popup_id),
                "-e", "ZMP_QA_TEMPLATE_KIND=popup",
                "-e", "ZMP_QA_THEME_SAVE=yes",
                "-v", str(popup_js) + ":/qa/popup_save.js:ro",
                "--entrypoint", "timeout", args.editor_playwright_image,
                "--signal=TERM", "--kill-after=5s", "90s",
                "node", "/qa/popup_save.js",
            ]
            popup_state = {}
            try:
                popup_run = docker(popup_cmd, timeout=110)
                popup_line = next((
                    line[len("ZMP_THEME_SAVE_JSON="):]
                    for line in popup_run.stdout.splitlines()
                    if line.startswith("ZMP_THEME_SAVE_JSON=")
                ), None)
                if popup_line:
                    try:
                        popup_state = json.loads(popup_line)
                    except ValueError:
                        popup_state = {}
                record("Synthetic Popup template changed and published in editor",
                       popup_run.returncode == 0
                       and popup_state.get("templateKind") == "popup"
                       and all(popup_state.get(k) is True for k in (
                           "authenticated", "headerWidgetFound", "headingSelected",
                           "originalMatched", "editedMatched", "saveClicked",
                       ))
                       and all(popup_state.get(k) == 0 for k in (
                           "pageErrors", "httpErrors", "requestFailures",
                       )),
                       {"exit_code": popup_run.returncode, "state": popup_state})
            except subprocess.TimeoutExpired:
                record("Synthetic Popup template changed and published in editor",
                       False, {"hard_timeout": True})
            finally:
                docker(["rm", "-f", popup_browser_name], 20)

            popup_verify = (
                '$id=' + str(popup_id) + ';'
                '$type=get_post_meta($id,"_elementor_template_type",true);'
                '$d=json_decode(get_post_meta($id,"_elementor_data",true),true);'
                '$saved=false;'
                '$scan=function($n)use(&$scan,&$saved){'
                'foreach((array)$n as $item){if(!is_array($item))continue;'
                'if(($item["id"]??"")==="7a0b1c02"){'
                '$saved=(($item["widgetType"]??"")==="heading"&&'
                '($item["settings"]["title"]??"")==="ZiloMentor QA Saved Popup");}'
                'if(!empty($item["elements"]))$scan($item["elements"]);}};'
                '$scan($d);echo wp_json_encode(["type"=>$type,"saved"=>$saved]);'
            )
            popup_db_run = wp("eval", popup_verify)
            try:
                popup_db = json.loads(popup_db_run.stdout.strip())
            except ValueError:
                popup_db = {}
            record("Popup template title persisted to WordPress database",
                   popup_db_run.returncode == 0
                   and popup_db.get("type") == "popup"
                   and popup_db.get("saved") is True,
                   {"wpcli_exit": popup_db_run.returncode,
                    "verification": popup_db})

            popup_target_status, popup_target_body, popup_target_err = request(
                "?page_id=" + str(theme_fixtures["target"])
                + "&zmp_qa_theme_popup=1"
            )
            popup_other_status, popup_other_body, popup_other_err = request(
                "?page_id=" + str(fixtures["plain"])
                + "&zmp_qa_theme_popup=1"
            )
            try:
                popup_target = json.loads(popup_target_body)
                popup_other = json.loads(popup_other_body)
            except ValueError:
                popup_target = {}
                popup_other = {}
            record("Edited Popup renders only on its intended synthetic page",
                   popup_target_status == 200 and popup_other_status == 200
                   and popup_target.get("popup_saved_marker") is True
                   and popup_target.get("popup_marker") is False
                   and popup_id in popup_target.get("popup_doc_ids", [])
                   and popup_other.get("popup_saved_marker") is False
                   and popup_id not in popup_other.get("popup_doc_ids", []),
                   {"target_status": popup_target_status,
                    "unrelated_status": popup_other_status,
                    "target_saved": popup_target.get("popup_saved_marker"),
                    "unrelated_saved": popup_other.get("popup_saved_marker"),
                    "errors": [popup_target_err, popup_other_err]})

        if args.verify_posts_nav_editor:
            nav_js = plugins_path / plugin_folder / "tests/browser_posts_nav_editor.js"
            require(nav_js.is_file(), "Missing synthetic Posts/Nav editor QA")
            nav_browser_name = "zmp-qa-posts-nav-" + tag
            nav_cmd = [
                "run", "--rm", "--name", nav_browser_name,
                "--network", network, "--memory=1600m", "--cpus=2",
                "--shm-size=128m",
                "-e", "NODE_PATH=/usr/lib/node_modules",
                "-e", "ZMP_QA_EDITOR_TOKEN=" + editor_login_token,
                "-e", "ZMP_QA_PAGE_ID=" + str(nav_fixtures["page"]),
                "-e", "ZMP_QA_POSTS_NAV_EDITOR=yes",
                "-v", str(nav_js) + ":/qa/posts_nav.js:ro",
                "--entrypoint", "timeout", args.editor_playwright_image,
                "--signal=TERM", "--kill-after=5s", "90s",
                "node", "/qa/posts_nav.js",
            ]
            nav_state = {}
            try:
                nav_run = docker(nav_cmd, timeout=110)
                nav_line = next((
                    line[len("ZMP_POSTS_NAV_EDITOR_JSON="):]
                    for line in nav_run.stdout.splitlines()
                    if line.startswith("ZMP_POSTS_NAV_EDITOR_JSON=")
                ), None)
                if nav_line:
                    try:
                        nav_state = json.loads(nav_line)
                    except ValueError:
                        nav_state = {}
                record("Synthetic Pro Nav Menu editing and Posts widget selection",
                       nav_run.returncode == 0
                       and all(nav_state.get(key) is True for key in (
                           "authenticated", "navFound", "postsFound",
                           "navSelected", "oldMenuNameMatched",
                           "newMenuNameMatched", "postsSelected", "saveClicked",
                       ))
                       and all(nav_state.get(key) == 0 for key in (
                           "pageErrors", "httpErrors", "requestFailures",
                       )),
                       {"exit_code": nav_run.returncode, "state": nav_state})
            except subprocess.TimeoutExpired:
                record("Synthetic Pro Nav Menu editing and Posts widget selection",
                       False, {"hard_timeout": True})
            finally:
                docker(["rm", "-f", nav_browser_name], 20)

            nav_verify = (
                '$id=' + str(nav_fixtures["page"]) + ';'
                '$d=json_decode(get_post_meta($id,"_elementor_data",true),true);'
                '$saved=false;$posts_preserved=false;'
                '$scan=function($n)use(&$scan,&$saved,&$posts_preserved){'
                'foreach((array)$n as $item){if(!is_array($item))continue;'
                'if(($item["id"]??"")==="9a0c1d01"){'
                '$saved=(($item["widgetType"]??"")==="nav-menu"&&'
                '($item["settings"]["menu_name"]??"")==="ZiloMentor QA Saved Navigation Menu");}'
                'if(($item["id"]??"")==="9a0c1d02"){'
                '$posts_preserved=(($item["widgetType"]??"")==="posts");}'
                'if(!empty($item["elements"]))$scan($item["elements"]);}};'
                '$scan($d);echo wp_json_encode(["saved"=>$saved,'
                '"posts_preserved"=>$posts_preserved]);'
            )
            nav_db_run = wp("eval", nav_verify)
            try:
                nav_db = json.loads(nav_db_run.stdout.strip())
            except ValueError:
                nav_db = {}
            record("Nav Menu label persisted without losing Posts widget",
                   nav_db_run.returncode == 0
                   and nav_db.get("saved") is True
                   and nav_db.get("posts_preserved") is True,
                   {"exit": nav_db_run.returncode, "verification": nav_db})
            nav_http, nav_html, nav_err = request(
                "?page_id=" + str(nav_fixtures["page"])
            )
            record("Edited Nav Menu retains published link and Posts rendering",
                   nav_http == 200
                   and nav_fixtures["menu_label"] in nav_html
                   and nav_fixtures["posts_label"] in nav_html
                   and 'elementor-widget-nav-menu' in nav_html
                   and 'elementor-widget-posts' in nav_html,
                   {"status": nav_http,
                    "link_present": nav_fixtures["menu_label"] in nav_html,
                    "post_present": nav_fixtures["posts_label"] in nav_html,
                    "error": nav_err})

        if args.verify_editor_responsive:
            responsive_js = plugins_path / plugin_folder / "tests/browser_editor_responsive.js"
            require(responsive_js.is_file(), "Missing responsive Elementor editor QA")
            responsive_browser_name = "zmp-qa-responsive-" + tag
            responsive_cmd = [
                "run", "--rm", "--name", responsive_browser_name,
                "--network", network, "--memory=1600m", "--cpus=2",
                "--shm-size=128m",
                "-e", "NODE_PATH=/usr/lib/node_modules",
                "-e", "ZMP_QA_EDITOR_TOKEN=" + editor_login_token,
                "-e", "ZMP_QA_PAGE_ID=" + str(fixtures["page"]),
                "-e", "ZMP_QA_RESPONSIVE=yes",
                "-v", str(responsive_js) + ":/qa/responsive.js:ro",
                "--entrypoint", "timeout", args.editor_playwright_image,
                "--signal=TERM", "--kill-after=5s", "85s",
                "node", "/qa/responsive.js",
            ]
            responsive_state = {}
            try:
                responsive_run = docker(responsive_cmd, timeout=105)
                responsive_line = next((
                    line[len("ZMP_RESPONSIVE_JSON="):]
                    for line in responsive_run.stdout.splitlines()
                    if line.startswith("ZMP_RESPONSIVE_JSON=")
                ), None)
                try:
                    responsive_state = json.loads(responsive_line) if responsive_line else {}
                except ValueError:
                    responsive_state = {}
                record("Real Elementor editor responsive Desktop Tablet Mobile switching",
                       responsive_run.returncode == 0 and
                       all(responsive_state.get(k) is True for k in (
                           "authenticated", "controlsPresent", "desktopInitiallySelected",
                           "tabletSelected", "mobileSelected", "desktopRestored",
                           "tabletWidthValid", "mobileWidthValid",
                           "desktopWidthRestored", "headingStillPresent",
                           "formStillPresent",
                       )) and
                       all(responsive_state.get(k) == 0 for k in (
                           "pageErrors", "httpErrors", "failedLocalRequests",
                       )),
                       {"exit_code": responsive_run.returncode,
                        "state": responsive_state})
            except subprocess.TimeoutExpired:
                record("Real Elementor editor responsive Desktop Tablet Mobile switching",
                       False, {"hard_timeout": True})
            finally:
                docker(["rm", "-f", responsive_browser_name], 20)

        if args.focus == "editor":
            print("QA_RESULTS_JSON=" + json.dumps(observations), flush=True)
            return 0 if all(item["passed"] for item in observations) else 1

        product_url = fixtures["product_url"]
        require(product_url.startswith("http://web:8080/"),
                "Synthetic product URL escaped isolated test domain")
        path = product_url.split("http://web:8080/", 1)[1]
        status, html, error = request(path)
        record("WooCommerce product HTTP render",
               status == 200 and "ZiloMentor Synthetic Test Product" in html,
               {"status": status, "error": error})
        status, html, error = request("?add-to-cart=" + str(fixtures["product"]))
        record("WooCommerce add-to-cart HTTP response", status == 200,
               {"status": status, "error": error,
                "notices_added": "added to your cart" in html.lower(),
                "has_product": "ZiloMentor Synthetic Test Product" in html})
        cookie_jar = cookie_dir / "cookies.txt"
        if cookie_jar.is_file():
            # Report cookie *names* only, never cookie tokens or values.
            cookie_lines = cookie_jar.read_text().splitlines()
            cookie_names = []
            for line in cookie_lines:
                if line.startswith("#HttpOnly_"):
                    line = line[len("#HttpOnly_"):]
                elif line.startswith("#"):
                    continue
                fields = line.split("\t")
                if len(fields) >= 7:
                    cookie_names.append(fields[5])
        else:
            cookie_names = []
        record("WooCommerce session cookie issued",
               any("woocommerce_session_" in name for name in cookie_names),
               {"cookie_names": cookie_names})
        record("Guest cart cookie jar is separate from admin editor cookies",
               not any(name.startswith(("wordpress_logged_in_", "wordpress_sec_"))
                       for name in cookie_names),
               {"cookie_names": cookie_names})
        cart_page_debug = (
            '$id=' + str(fixtures["cart"]) + ';'
            '$p=get_post($id);'
            '$raw=$p ? $p->post_content : "";'
            '$rendered=do_shortcode($raw);'
            'echo wp_json_encode(["raw"=>$raw,"has_shortcode"=>has_shortcode($raw,"woocommerce_cart"),'
            '"shortcode_length"=>strlen($rendered),'
            '"shortcode_has_product"=>str_contains($rendered,"ZiloMentor Synthetic Test Product"),'
            '"shortcode_has_cart_form"=>str_contains($rendered,"woocommerce-cart-form"),'
            '"shortcode_has_cart_markup"=>str_contains($rendered,"woocommerce-cart")]);'
        )
        shortcode_result = wp("eval", cart_page_debug)
        try:
            shortcode_info = json.loads(shortcode_result.stdout.strip())
        except ValueError:
            shortcode_info = {}
        record("WooCommerce cart shortcode works in WP-CLI",
               shortcode_result.returncode == 0 and
               shortcode_info.get("has_shortcode") is True,
               shortcode_info)

        control_status, control_html, control_error = request(
            "?page_id=" + str(fixtures["cart_control"])
        )
        record("Ordinary page with WooCommerce cart shortcode displays item",
               control_status == 200
               and "ZiloMentor Cart Control Before" in control_html
               and "ZiloMentor Cart Control After" in control_html
               and "ZiloMentor Synthetic Test Product" in control_html
               and "woocommerce-cart-form" in control_html,
               {
                   "status": control_status,
                   "preamble": "ZiloMentor Cart Control Before" in control_html,
                   "postamble": "ZiloMentor Cart Control After" in control_html,
                   "item": "ZiloMentor Synthetic Test Product" in control_html,
                   "cart_form": "woocommerce-cart-form" in control_html,
                   "html_bytes": len(control_html),
                   "transport": control_error,
               })
        for page_type, page_id in (
            ("cart", fixtures["cart"]),
            ("control", fixtures["cart_control"]),
        ):
            trace_status, trace_html, trace_err = request(
                "?page_id=" + str(page_id) + "&zmp_qa_trace=1"
            )
            marker = "<!--ZMP_QA_TRACE:"
            trace = {}
            if marker in trace_html:
                raw_trace = trace_html.rsplit(marker, 1)[1].split("-->", 1)[0]
                try:
                    trace = json.loads(raw_trace)
                except ValueError:
                    pass
            record("WordPress full-page content hook trace: " + page_type,
                   trace_status == 200 and "calls" in trace,
                   {
                       "status": trace_status,
                       "trace": trace,
                       "has_product_in_final_html":
                           "ZiloMentor Synthetic Test Product" in trace_html,
                       "error": trace_err,
                   })

        filter_status, filter_body, filter_err = request(
            "?page_id=" + str(fixtures["cart"]) + "&zmp_qa_content_filter=1"
        )
        try:
            filter_data = json.loads(filter_body)
        except ValueError:
            filter_data = {}
        record("WooCommerce content filter executed in Cart page request",
               filter_status == 200 and filter_data.get("raw_has_shortcode") is True,
               {"status": filter_status, "filter": filter_data,
                "transport": filter_err})
        status, html, error = request("?page_id=" + str(fixtures["cart"]))
        record("WooCommerce cart retains synthetic product",
               status == 200 and "ZiloMentor Synthetic Test Product" in html,
               {"status": status, "error": error, "bytes": len(html),
                "product_name_present": "ZiloMentor Synthetic Test Product" in html,
                "empty_cart_notice": "cart is currently empty" in html.lower(),
                "cart_form_present": "woocommerce-cart-form" in html,
                "woocommerce_cart_details": html.find("woocommerce-cart"),
                "synthetic_cart_page_title_present": "ZiloMentor Synthetic Cart" in html,
                "synthetic_checkout_page_title_present": "ZiloMentor Synthetic Checkout" in html,
                "contains_shortcode_literal": "[woocommerce_cart]" in html,
                "contains_woocommerce_info": "woocommerce-info" in html})
        state_status, state_body, state_err = request("?zmp_qa_cart_state=1")
        try:
            cart_state = json.loads(state_body)
        except ValueError:
            cart_state = {}
        shortcode_status, shortcode_body, shortcode_error = request(
            "?page_id=" + str(fixtures["cart"]) + "&zmp_qa_cart_render=1"
        )
        try:
            cart_render = json.loads(shortcode_body)
        except ValueError:
            cart_render = {}
        record("WooCommerce shortcode with real HTTP cart session",
               shortcode_status == 200
               and cart_render.get("session_count") == 1
               and cart_render.get("is_cart") is True
               and cart_render.get("shortcode_has_item") is True
               and cart_render.get("shortcode_has_form") is True,
               {"status": shortcode_status, "render": cart_render,
                "error": shortcode_error})
        record("WooCommerce session cart retains product ID",
               state_status == 200 and
               fixtures["product"] in cart_state.get("product_ids", []),
               {"status": state_status, "cart_state": cart_state,
                "error": state_err})
        status_ajax, fragments, err_ajax = request("?wc-ajax=get_refreshed_fragments")
        try:
            fragment_data = json.loads(fragments)
        except ValueError:
            fragment_data = {}
        record("WooCommerce cart fragments respond",
               status_ajax == 200 and isinstance(fragment_data, dict)
               and "cart_hash" in fragment_data,
               {"status": status_ajax,
                "cart_hash_present": bool(fragment_data.get("cart_hash")),
                "fragment_count": len(fragment_data.get("fragments", {})),
                "error": err_ajax})
        ajax_status, ajax_body, ajax_error = request(
            "?wc-ajax=add_to_cart",
            {"product_id": str(fixtures["product"]), "quantity": "1"},
        )
        try:
            ajax_json = json.loads(ajax_body)
        except ValueError:
            ajax_json = {}
        record("WooCommerce AJAX add-to-cart accepted",
               ajax_status == 200 and "fragments" in ajax_json
               and not ajax_json.get("error"),
               {"status": ajax_status, "has_fragments": "fragments" in ajax_json,
                "error_field": ajax_json.get("error"),
                "response_start": ajax_body[:160],
                "item_in_fragments": "ZiloMentor Synthetic Test Product" in ajax_body,
                "cart_hash_present": bool(ajax_json.get("cart_hash")),
                "transport": ajax_error})
        ajax_cookie_names = []
        if cookie_jar.is_file():
            for line in cookie_jar.read_text().splitlines():
                if line.startswith("#HttpOnly_"):
                    line = line[len("#HttpOnly_"):]
                elif line.startswith("#"):
                    continue
                fields = line.split("\t")
                if len(fields) >= 7:
                    ajax_cookie_names.append(fields[5])
        record("WooCommerce session cookie after AJAX",
               any("woocommerce_session_" in name for name in ajax_cookie_names),
               {"cookie_names": ajax_cookie_names})
        status_after_ajax, cart_after_ajax, err_after_ajax = request(
            "?page_id=" + str(fixtures["cart"])
        )
        record("WooCommerce cart after AJAX add",
               status_after_ajax == 200
               and "ZiloMentor Synthetic Test Product" in cart_after_ajax,
               {"status": status_after_ajax, "bytes": len(cart_after_ajax),
                "has_product": "ZiloMentor Synthetic Test Product" in cart_after_ajax,
                "transport": err_after_ajax})
        # Baseline without ZiloMentor: preserve all other synthetic site dependencies.
        p = wp("plugin", "deactivate", plugin_folder)
        if p.returncode == 0:
            cookie_file = cookie_dir / "cookies.txt"
            if cookie_file.exists():
                cookie_file.unlink()
            baseline_status, baseline_body, baseline_error = request(
                "?wc-ajax=add_to_cart",
                {"product_id": str(fixtures["product"]), "quantity": "1"},
            )
            try:
                baseline_json = json.loads(baseline_body)
            except ValueError:
                baseline_json = {}
            record("WooCommerce AJAX baseline without ZiloMentor",
                   baseline_status == 200 and "fragments" in baseline_json,
                   {"status": baseline_status,
                    "has_fragments": "fragments" in baseline_json,
                    "cart_hash_present": bool(baseline_json.get("cart_hash")),
                    "item_in_fragments": "ZiloMentor Synthetic Test Product" in baseline_body,
                    "error_field": baseline_json.get("error"),
                    "response_start": baseline_body[:160],
                    "transport": baseline_error})
            baseline_cart_status, baseline_cart, baseline_cart_error = request(
                "?page_id=" + str(fixtures["cart"])
            )
            record("WooCommerce baseline cart without ZiloMentor",
                   baseline_cart_status == 200 and
                   "ZiloMentor Synthetic Test Product" in baseline_cart,
                   {"status": baseline_cart_status,
                    "product_present": "ZiloMentor Synthetic Test Product" in baseline_cart,
                    "bytes": len(baseline_cart),
                    "transport": baseline_cart_error})
            baseline_state_status, baseline_state_body, baseline_state_err = request(
                "?zmp_qa_cart_state=1"
            )
            try:
                baseline_state = json.loads(baseline_state_body)
            except ValueError:
                baseline_state = {}
            record("WooCommerce baseline session cart without ZiloMentor",
                   baseline_state_status == 200
                   and fixtures["product"] in baseline_state.get("product_ids", []),
                   {"status": baseline_state_status,
                    "state": baseline_state, "error": baseline_state_err})
            wp("plugin", "activate", plugin_folder)
            if has_default_theme:
                default_activation = wp("theme", "activate", "twentytwentyfive")
                if default_activation.returncode == 0:
                    default_cart_status, default_cart_html, default_cart_error = request(
                        "?page_id=" + str(fixtures["cart"])
                    )
                    record("Default WordPress theme cart renders product",
                           default_cart_status == 200 and
                           "ZiloMentor Synthetic Test Product" in default_cart_html,
                           {"status": default_cart_status,
                            "product_present": "ZiloMentor Synthetic Test Product" in default_cart_html,
                            "synthetic_page_title_present": "ZiloMentor Synthetic Cart" in default_cart_html,
                            "bytes": len(default_cart_html),
                            "transport": default_cart_error})
                    wp("theme", "activate", THEME)
        # Isolate the WordPress/WooCommerce designated Cart page mapping.
        # All options and pages here belong to this disposable database only.
        swap = wp("option", "update", "woocommerce_cart_page_id",
                  str(fixtures["cart_control"]))
        if swap.returncode == 0:
            old_status, old_html, old_error = request(
                "?page_id=" + str(fixtures["cart"])
            )
            new_status, new_html, new_error = request(
                "?page_id=" + str(fixtures["cart_control"])
            )
            record("Disposable Woo Cart page reassignment diagnostic",
                   old_status == 200 and new_status == 200,
                   {
                       "former_cart_product_visible":
                           "ZiloMentor Synthetic Test Product" in old_html,
                       "new_registered_cart_product_visible":
                           "ZiloMentor Synthetic Test Product" in new_html,
                       "former_cart_form_visible":
                           "woocommerce-cart-form" in old_html,
                       "new_cart_form_visible":
                           "woocommerce-cart-form" in new_html,
                       "error": old_error or new_error,
                   })
            wp("option", "update", "woocommerce_cart_page_id",
               str(fixtures["cart"]))

        if has_default_theme:
            # WooCommerce-only baseline: remove Elementor and Vamtam bridge
            # in this throwaway site to distinguish template selection from
            # any Elementor/Fiore integration. No production plugins touched.
            a = wp("theme", "activate", "twentytwentyfive")
            b = wp("plugin", "deactivate", "vamtam-elementor-integration-fiore")
            c = wp("plugin", "deactivate", plugin_folder)
            d = wp("plugin", "deactivate", "elementor")
            if all(x.returncode == 0 for x in (a, b, c, d)):
                pure_status, pure_html, pure_error = request(
                    "?page_id=" + str(fixtures["cart"])
                )
                record("Pure WooCommerce default-theme Cart page diagnostic",
                       pure_status == 200,
                       {
                           "status": pure_status,
                           "product_visible":
                               "ZiloMentor Synthetic Test Product" in pure_html,
                           "cart_form_visible":
                               "woocommerce-cart-form" in pure_html,
                           "error": pure_error,
                       })
            else:
                record("Pure WooCommerce default-theme Cart page diagnostic",
                       False,
                       {"dependency_deactivation_failed": True,
                        "return_codes": [x.returncode for x in (a, b, c, d)]})

        if has_default_theme:
            # A/B confirmation for WooCommerce 9.3+ store Coming Soon handler.
            # Still WooCommerce-only, default WP theme, disposable DB/network.
            only_store = wp("option", "update", "woocommerce_store_pages_only", "yes")
            enable_soon = wp("option", "update", "woocommerce_coming_soon", "yes")
            soon_status, soon_html, soon_err = request(
                "?page_id=" + str(fixtures["cart"])
            )
            record("WooCommerce Coming Soon ON intercepts designated Cart",
                   only_store.returncode == 0 and enable_soon.returncode == 0
                   and soon_status == 200
                   and "ZiloMentor Synthetic Test Product" not in soon_html
                   and "woocommerce-cart-form" not in soon_html,
                   {"status": soon_status,
                    "product_visible": "ZiloMentor Synthetic Test Product" in soon_html,
                    "cart_form_visible": "woocommerce-cart-form" in soon_html,
                    "transport": soon_err})
            disable_soon = wp("option", "update", "woocommerce_coming_soon", "no")
            live_status, live_html, live_err = request(
                "?page_id=" + str(fixtures["cart"])
            )
            record("WooCommerce Coming Soon OFF restores designated Cart",
                   disable_soon.returncode == 0 and live_status == 200
                   and "ZiloMentor Synthetic Test Product" in live_html
                   and "woocommerce-cart-form" in live_html,
                   {"status": live_status,
                    "product_visible": "ZiloMentor Synthetic Test Product" in live_html,
                    "cart_form_visible": "woocommerce-cart-form" in live_html,
                    "transport": live_err})

        body_debug = {
            "cart_html_length": len(html),
            "contains_checkout_title": "ZiloMentor Synthetic Checkout" in html,
            "has_cart_form": "woocommerce-cart-form" in html,
            "woocommerce_cart_section": html.find("woocommerce-cart"),
            "raw_shortcode_present": "[woocommerce_cart]" in html,
            "is_cart_widget_markup": "wc-block-cart" in html,
        }
        record("Synthetic WooCommerce cart page markup diagnostics", True, body_debug)
        status, html, error = request("?page_id=" + str(fixtures["checkout"]))
        record("WooCommerce checkout with synthetic cart",
               status == 200 and "checkout" in html.lower(),
               {"status": status, "error": error, "bytes": len(html)})
        # End-to-end anonymous WooCommerce checkout via its real AJAX
        # handler, with a *new guest cookie jar* and a synthetic virtual
        # product. Only offline BACS is enabled for this order. No card,
        # payment processor, real customer or outbound email is involved.
        checkout_cookie = "checkout-cookies.txt"
        checkout_product_id = fixtures["checkout_product"]
        guest_add_status, guest_add_html, guest_add_err = request(
            "?add-to-cart=" + str(checkout_product_id),
            cookie_file_name=checkout_cookie,
        )
        record("synthetic guest checkout product added to isolated cart",
               guest_add_status == 200 and not guest_add_err,
               {"status": guest_add_status, "error": guest_add_err})
        checkout_status, checkout_html, checkout_error = request(
            "?page_id=" + str(fixtures["checkout"]),
            cookie_file_name=checkout_cookie,
        )
        checkout_nonce_match = re.search(
            r'<input[^>]*name=["\\\']woocommerce-process-checkout-nonce["\\\'][^>]*value=["\\\']([^"\\\']+)',
            checkout_html, re.IGNORECASE,
        )
        if checkout_nonce_match is None:
            checkout_nonce_match = re.search(
                r'<input[^>]*value=["\\\']([^"\\\']+)["\\\'][^>]*name=["\\\']woocommerce-process-checkout-nonce',
                checkout_html, re.IGNORECASE,
            )
        checkout_nonce = checkout_nonce_match.group(1) if checkout_nonce_match else None
        record("WooCommerce guest checkout exposes offline form nonce",
               checkout_status == 200
               and checkout_nonce is not None
               and "woocommerce-checkout" in checkout_html,
               {"status": checkout_status, "form_present": "woocommerce-checkout" in checkout_html,
                "nonce_present": checkout_nonce is not None,
                "offline_payment_visible": "QA offline bank transfer" in checkout_html,
                "error": checkout_error})
        checkout_response = {}
        checkout_post_status = 0
        checkout_post_error = ""
        if checkout_nonce is not None:
            checkout_post_status, checkout_body, checkout_post_error = request(
                "?wc-ajax=checkout",
                {
                    "woocommerce-process-checkout-nonce": checkout_nonce,
                    "_wp_http_referer": "/?page_id=" + str(fixtures["checkout"]),
                    "billing_first_name": "Synthetic",
                    "billing_last_name": "QA",
                    "billing_company": "",
                    "billing_country": "GB",
                    "billing_address_1": "1 Test Street",
                    "billing_address_2": "",
                    "billing_city": "London",
                    "billing_state": "",
                    "billing_postcode": "SW1A 1AA",
                    "billing_phone": "02000000000",
                    "billing_email": "qa-checkout@example.invalid",
                    "payment_method": "bacs",
                    "terms": "1",
                },
                cookie_file_name=checkout_cookie,
            )
            try:
                checkout_response = json.loads(checkout_body)
            except ValueError:
                checkout_response = {}
        record("WooCommerce AJAX offline guest checkout completes",
               checkout_post_status == 200
               and checkout_response.get("result") == "success"
               and "order-received" in checkout_response.get("redirect", ""),
               {"status": checkout_post_status,
                "result": checkout_response.get("result"),
                "has_confirmation_redirect": "order-received" in checkout_response.get("redirect", ""),
                "error_type": "checkout_validation" if checkout_response.get("result") == "failure" else None,
                "checkout_error": checkout_post_error,
                "message_excerpt": re.sub(r"<[^>]+>", " ", str(checkout_response.get("messages", "")))[:450],
               })
        # Independent server-side assertion: a real order exists in the
        # disposable DB, contains the separate virtual product and records
        # only the offline payment method and synthetic customer email.
        order_check_code = (
            '$orders=wc_get_orders(["limit"=>15,"orderby"=>"date","order"=>"DESC"]);'
            '$out=["count"=>0,"matched"=>false,"item"=>false,"total"=>false,'
            '"payment"=>"","status"=>"","transaction_blank"=>true];'
            'foreach($orders as $o){'
            'if($o->get_billing_email()!=="qa-checkout@example.invalid")continue;'
            '$out["count"]++;$out["payment"]=$o->get_payment_method();'
            '$out["status"]=$o->get_status();'
            '$out["transaction_blank"]=$o->get_transaction_id()==="";'
            '$out["total"]=(float)$o->get_total()===7.49;'
            'foreach($o->get_items() as $i){'
            'if((int)$i->get_product_id()===' + str(checkout_product_id) + ')'
            '$out["item"]=(int)$i->get_quantity()===1;}'
            '$out["matched"]=$out["item"]&&$out["total"]&&'
            '$out["payment"]==="bacs"&&$out["transaction_blank"];break;}'
            'echo wp_json_encode($out);'
        )
        order_result = wp("eval", order_check_code)
        try:
            order_data = json.loads(order_result.stdout.strip())
        except ValueError:
            order_data = {}
        record("offline guest order persisted with synthetic item and no payment transaction",
               order_result.returncode == 0
               and order_data.get("matched") is True
               and order_data.get("count") == 1
               and order_data.get("status") in ("on-hold", "pending", "processing"),
               {"wpcli_exit": order_result.returncode, "order": order_data})
        print("QA_RESULTS_JSON=" + json.dumps(observations), flush=True)
        return 0 if all(item["passed"] for item in observations) else 1

    finally:
        # Never remove or modify anything outside names and temp files created
        # by this script; never touch source WordPress directories.
        for kind, name in reversed(active):
            command = ["rm", "-f", name] if kind == "container" else [
                "network", "rm", name,
            ]
            docker(command, 40)
        cleanup = docker([
            "run", "--rm", "--network", "none",
            "-v", str(temp) + ":/cleanup",
            "--entrypoint", "sh", args.clean_image,
            "-c", "find /cleanup -mindepth 1 -delete",
        ], 110)
        if cleanup.returncode == 0:
            temp.rmdir()
            print("Disposable WordPress, database and network cleaned.", flush=True)
        else:
            print("WARNING: test-only cleanup failed: " + str(temp), flush=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        print("QA HARNESS ERROR: " + str(error), file=sys.stderr)
        raise SystemExit(2) from error
