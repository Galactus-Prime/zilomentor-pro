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
    args = parser.parse_args()
    if args.source_wordpress is not None and args.skip_php:
        parser.error("Full isolated QA requires PHP Docker tests; remove --skip-php.")
    execute([sys.executable, "tests/static_compatibility.py"])
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
        execute([
            sys.executable, "tools/qa_isolated_site.py", "--source-wordpress",
            str(args.source_wordpress),
        ])
    print("PASS all requested manual checks; no GitHub Actions used.")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error
