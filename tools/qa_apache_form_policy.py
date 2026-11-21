#!/usr/bin/env python3
"""Check the REAL generated Form .htaccess under disposable loopback Apache.

This runs solely against a synthetic /tmp document root, never production
Apache, WordPress data, customer uploads or live ports. No Apache restart.
Requires an installed Apache httpd and the system's installed module .so's.
"""
import argparse
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--htaccess", required=True, type=Path)
    parser.add_argument("--httpd", type=Path, default=Path("/usr/sbin/httpd"))
    parser.add_argument("--module-dir", type=Path,
                        default=Path("/usr/lib64/apache2/modules"))
    args = parser.parse_args()

    source = args.htaccess.resolve(strict=True)
    # Deny accidental tests against live customer .htaccess files. The
    # independent WordPress QA harness always names this disposable tree.
    if not source.is_file() or source.name != ".htaccess" or not any(
        part.startswith("zmp-isolated-qa-") for part in source.parts
    ) or source.parts[-4:] != ("uploads", "elementor", "forms", ".htaccess"):
        raise ValueError("Only a disposable ZMP Form-upload policy can be tested")
    if source.stat().st_size > 16384:
        raise ValueError("Unexpectedly large Form .htaccess fixture")

    modules = ("mpm_event", "authz_core", "authz_host", "unixd", "mime",
               "alias", "headers", "dir", "log_config", "autoindex",
               "access_compat")
    missing = [name for name in modules if not
               (args.module_dir / ("mod_" + name + ".so")).is_file()]
    if missing:
        raise RuntimeError("Installed Apache modules missing: " + ", ".join(missing))

    tmp = Path(tempfile.mkdtemp(prefix="zmp-apache-form-qa-"))
    process = None
    try:
        root = tmp / "public"
        upload_path = root / "uploads" / "elementor" / "forms"
        upload_path.mkdir(parents=True)
        shutil.copy2(source, upload_path / ".htaccess")
        files = {
            "ordinary.txt": 200,
            "blocked.php": 403,
            "blocked.php8": 403,
            "blocked.php.jpg": 403,
            "blocked.phtml.png": 403,
            "blocked.phar.webp": 403,
            "blocked.py.txt": 403,
            "blocked.shtml.txt": 403,
        }
        for filename in files:
            (upload_path / filename).write_text("Synthetic ZiloMentor test fixture\n")

        # Apache only listens on loopback, on a temporary unprivileged port.
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        config_lines = [
            f'LoadModule {name}_module {args.module_dir / ("mod_" + name + ".so")}'
            for name in modules
        ]
        config_lines += [
            f'ServerRoot "{tmp}"',
            "ServerName localhost",
            f"Listen 127.0.0.1:{port}",
            f'PidFile "{tmp / "httpd.pid"}"',
            f'ErrorLog "{tmp / "error.log"}"',
            "LogLevel warn",
            f'DocumentRoot "{root}"',
            "TypesConfig /etc/mime.types",
            f'<Directory "{root}">',
            "Require all granted",
            "AllowOverride All",
            "Options FollowSymLinks",
            "</Directory>",
        ]
        config = tmp / "httpd.conf"
        config.write_text("\n".join(config_lines) + "\n")
        syntax = subprocess.run(
            [str(args.httpd), "-t", "-f", str(config)],
            text=True, capture_output=True, timeout=10
        )
        if syntax.returncode:
            raise RuntimeError("Apache syntax validation failed: " +
                               (syntax.stderr + syntax.stdout)[-500:])

        process = subprocess.Popen(
            [str(args.httpd), "-X", "-f", str(config)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        started = False
        for attempt in range(15):
            if process.poll() is not None:
                raise RuntimeError("Disposable Apache exited before readiness")
            try:
                with urlopen(
                    f"http://127.0.0.1:{port}/uploads/elementor/forms/ordinary.txt",
                    timeout=1,
                ) as response:
                    started = response.status == 200
                if started:
                    break
            except (URLError, TimeoutError):
                time.sleep(0.15)
        if not started:
            raise RuntimeError("Disposable loopback Apache was not ready")

        checks = {}
        for filename, expected in files.items():
            url = f"http://127.0.0.1:{port}/uploads/elementor/forms/{filename}"
            try:
                with urlopen(url, timeout=3) as response:
                    status, headers = response.status, response.headers
            except HTTPError as response:
                status, headers = response.code, response.headers

            accepted = status == expected
            if filename == "ordinary.txt":
                accepted = accepted and (
                    "attachment" in headers.get("Content-Disposition", "")
                    and headers.get("X-Content-Type-Options") == "nosniff"
                    and "no-store" in headers.get("Cache-Control", "")
                )
            checks[filename] = accepted
            print(("PASS" if accepted else "FAIL") +
                  f" Apache {filename}: HTTP {status}", flush=True)

        print("QA_APACHE_JSON=" +
              json.dumps({"passed": all(checks.values()), "checks": checks}),
              flush=True)
        if not all(checks.values()):
            raise SystemExit(4)
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
