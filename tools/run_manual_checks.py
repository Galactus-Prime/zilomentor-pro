#!/usr/bin/env python3
"""Run ZiloMentor Pro checks manually on existing infrastructure (not GitHub Actions).

Usage:
    python3 tools/run_manual_checks.py
    python3 tools/run_manual_checks.py --skip-php
Runs static checks, creates a staging-only ZIP, and (unless explicitly skipped)
lints PHP using existing local Docker images for PHP 8.4 and 8.5.
This does not interact with any production WordPress site.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PHP_IMAGES = (
    ("PHP 8.4", "php:8.4.27-cli-bookworm"),
    ("PHP 8.5", "zc0140-php85-fpm-redis63-mysqli:local"),
)

def execute(args):
    print("+", " ".join(str(a) for a in args), flush=True)
    subprocess.run(args, check=True, cwd=ROOT)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-php", action="store_true",
        help="Explicitly skip PHP Docker matrix on the dev VM without Docker.",
    )
    parser.add_argument(
        "--source-wordpress", type=Path, default=None,
        help="Also run isolated HTTP/form/WooCommerce regression using only source files copied from this WordPress path.",
    )
    parser.add_argument(
        "--web-server", choices=("php", "nginx-fpm"), default="php",
        help="Run synthetic WordPress with the original PHP development server, or private Nginx/PHP-FPM workers.",
    )
    parser.add_argument(
        "--focus", choices=("all", "editor", "runtime"), default="all",
        help="Run complete HTTP, authenticated editor, or focused synthetic runtime-only security checks.",
    )
    parser.add_argument(
        "--plugin-folder", choices=("elementor-pro", "zilomentor-pro"),
        default="elementor-pro",
        help="Test legacy or independent plugin directory in disposable WordPress.",
    )
    parser.add_argument(
        "--browser-image", default=None,
        help="Optional pre-cached Chromium image for isolated browser DOM smoke tests; requires --source-wordpress.",
    )
    parser.add_argument(
        "--frontend-playwright-image", default=None,
        help="Optional cached Playwright image for isolated Header/Popup frontend open-close and trigger checks.",
    )
    parser.add_argument(
        "--editor-playwright-image", default=None,
        help="Optional pre-cached Playwright image for authenticated synthetic Elementor editor baseline checks.",
    )
    parser.add_argument(
        "--verify-editor-save", action="store_true",
        help="Opt-in synthetic Heading change and database-persistence check; requires editor-only Nginx/FPM + Playwright.",
    )
    parser.add_argument(
        "--verify-editor-form-save", action="store_true",
        help="Opt-in Pro Form name edit, real editor Publish/Update click and independent DB/HTTP verification in disposable WordPress.",
    )
    parser.add_argument(
        "--verify-editor-form-fields", action="store_true",
        help="Opt-in Pro Form field repeater edit/Publish with saved WordPress data and frontend verification.",
    )
    parser.add_argument(
        "--verify-theme-builder-save", action="store_true",
        help="Opt-in Theme Builder Header edit, Publish and independent database + scoped render verification in disposable WordPress.",
    )
    parser.add_argument(
        "--verify-popup-editor-save", action="store_true",
        help="Opt-in real Popup template edit/Publish and scoped frontend/WordPress verification.",
    )
    parser.add_argument(
        "--verify-posts-nav-editor", action="store_true",
        help="Opt-in real Nav Menu editing/Publish and Posts widget selection.",
    )
    parser.add_argument(
        "--verify-editor-responsive", action="store_true",
        help="Opt-in real Elementor editor Desktop Tablet Mobile breakpoint switching on a disposable page.",
    )
    args = parser.parse_args()
    if args.source_wordpress is not None and args.skip_php:
        parser.error("Full isolated QA requires PHP Docker tests; remove --skip-php.")
    if (args.browser_image or args.editor_playwright_image
            or args.frontend_playwright_image) and args.source_wordpress is None:
        parser.error("Browser QA requires --source-wordpress.")
    if args.focus == "editor" and not args.editor_playwright_image:
        parser.error("--focus editor requires --editor-playwright-image.")
    if args.web_server == "nginx-fpm" and args.source_wordpress is None:
        parser.error("--web-server nginx-fpm requires --source-wordpress.")
    if (args.verify_editor_save or args.verify_editor_form_save or args.verify_editor_form_fields or args.verify_theme_builder_save or args.verify_popup_editor_save or args.verify_posts_nav_editor or args.verify_editor_responsive) and not (
        args.focus == "editor" and args.web_server == "nginx-fpm"
        and args.editor_playwright_image and args.source_wordpress
    ):
        parser.error("Editor save verification requires --focus editor, --web-server nginx-fpm, --editor-playwright-image and --source-wordpress.")
    execute([sys.executable, "tests/static_compatibility.py"])
    # Always prove our release-switch and rollback logic against synthetic
    # files before building an installable ZIP. This never opens production WP.
    execute([sys.executable, "tests/test_manual_live_swap.py"])
    execute([sys.executable, "tests/test_migrate_independent_identity.py"])
    execute([sys.executable, "tests/test_build_zip.py"])
    execute([sys.executable, "tests/test_create_release_manifest.py"])
    # Offline synthetic HTTPS-feed checks use temporary Ed25519 keys, never a
    # real publishing key. No GitHub releases or CI network calls are made.
    execute([sys.executable, "tests/test_stage_signed_github_release.py"])
    execute([sys.executable, "tools/build_zip.py"])
    if args.skip_php:
        print("PHP matrix SKIPPED (explicit --skip-php); not a full QA pass.")
        return
    if not shutil.which("docker"):
        parser.error("Docker required for PHP 8.4/8.5 matrix; run --skip-php only where PHP Docker images are unavailable.")
    for label, image in PHP_IMAGES:
        # All PHP files must parse successfully; no WordPress is loaded.
        script = (
            "set -eu; "
            "find /src -type f -name '*.php' -not -path '*/.git/*' "
            "-not -path '*/dist/*' -print0 "
            "| xargs -0 -r -n 1 -P 4 php -n -l > /tmp/php-lint.txt 2>&1; "
            "grep -c 'No syntax errors detected' /tmp/php-lint.txt"
        )
        cmd = [
            "docker", "run", "--rm", "--network", "none",
            "--memory", "640m", "--cpus", "2",
            "--mount", f"type=bind,src={ROOT},dst=/src,readonly",
            "--entrypoint", "sh", image, "-c", script,
        ]
        execute(cmd)
        print(f"PASS {label} PHP syntax matrix.")
    if args.source_wordpress is not None:
        qa_cmd = [
            sys.executable, "tools/qa_isolated_site.py", "--source-wordpress",
            str(args.source_wordpress),
            "--web-server", args.web_server,
            "--focus", args.focus,
            "--plugin-folder", args.plugin_folder,
        ]
        if args.browser_image:
            qa_cmd.extend(["--browser-image", args.browser_image])
        if args.editor_playwright_image:
            qa_cmd.extend(["--editor-playwright-image", args.editor_playwright_image])
        if args.frontend_playwright_image:
            qa_cmd.extend(["--frontend-playwright-image", args.frontend_playwright_image])
        if args.verify_editor_save:
            qa_cmd.append("--verify-editor-save")
        if args.verify_editor_form_save:
            qa_cmd.append("--verify-editor-form-save")
        if args.verify_editor_form_fields:
            qa_cmd.append("--verify-editor-form-fields")
        if args.verify_theme_builder_save:
            qa_cmd.append("--verify-theme-builder-save")
        if args.verify_popup_editor_save:
            qa_cmd.append("--verify-popup-editor-save")
        if args.verify_posts_nav_editor:
            qa_cmd.append("--verify-posts-nav-editor")
        if args.verify_editor_responsive:
            qa_cmd.append("--verify-editor-responsive")
        execute(qa_cmd)
    print("PASS all requested manual checks; no GitHub Actions used.")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error
