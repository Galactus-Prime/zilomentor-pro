# Classic Form email attachment scoping and Apache enforcement

**Scope:** Unreleased ZiloMentor Pro 0.1.2 only. Verified 21 November
2026 on the disposable Itzy Bitzy Workshop source-code replica;
**not installed on the production shop**.

## Attachment path safety

The inherited Form Email action assembled attachment paths from
`Form_Record::get('files')` and passed them to `wp_mail`; it subsequently
used `@unlink( $file )` for Attach-only upload mode. Those paths are
normally produced by the Form Upload field, but WordPress form callbacks
and integrations can modify the record, so the mail action must avoid
trusting arbitrary local paths.

`ElementorPro\Core\Utils::is_safe_form_attachment_path()` now validates
each candidate using the configured Form upload root
(`elementor_pro/forms/upload_path` filter, or WordPress
`wp-content/uploads/elementor/forms`). It accepts only regular files
whose resolved parent directory equals the resolved configured root,
and rejects symlinks, missing paths, directories, nested paths, objects,
arrays and unrelated files. The Email action uses the validator *before*
attaching files and *before* Attach-only cleanup. The owner-configured
path filter continues to work when it points to a legitimate folder.

`tests/runtime_form_mail_attachment_safety.php` asserts the positive
normal/custom-folder paths and negative forged-file, symlink and
malformed-record cases. It does not send real email. The initial test
fixture mistakenly assumed Elementor's `Collection::values()` returned
a Collection object; the disposable runner identified the error and the
fixture was corrected without weakening source security.

## Actual Apache parser / generated .htaccess

`tools/qa_apache_form_policy.py` reads **the exact .htaccess emitted by
a disposable WordPress Form upload storage initializer**, copies it into
a separate randomly named temporary document root and boots an
installed Apache 2.4 server bound **only to 127.0.0.1** and a random
unprivileged port. It never restarts production Apache, adds vhosts to
the host, or creates scripts under production webroot.

It verifies real HTTP responses:

| Synthetic URL filename | Expected response |
| --- | --- |
| `ordinary.txt` | HTTP 200, `Content-Disposition: attachment`, `nosniff`, `no-store` |
| `blocked.php` | HTTP 403 |
| `blocked.php8` | HTTP 403 |
| `blocked.php.jpg` | HTTP 403 |
| `blocked.phtml.png` | HTTP 403 |
| `blocked.phar.webp` | HTTP 403 |
| `blocked.py.txt` | HTTP 403 |
| `blocked.shtml.txt` | HTTP 403 |

The Apache test returns a failure unless all cases match. It is
opt-in via `--verify-apache-uploads` on
`tools/qa_isolated_site.py` or `tools/run_manual_checks.py` and does
not need any external QA service or paid subscription. A focused
disposable WordPress runtime at source SHA
`ca9126808a5b020ed642b3ea39d8609c352905d1` passed
`runtime_form_mail_attachment_safety.php` and the new real Apache
check. That exact source revision also ran all the other focused
security fixtures.

Production-specific tests **remain unperformed**: no actual Form
upload folder exists yet on the live site, and the effective cPanel
site vhost, PHP-FPM handler, nested per-directory policy, reverse proxy
and server inheritance can differ from the standalone Apache test.
The Nginx test is a separate disposable container, not a claim of
Nginx protection on live cPanel Apache.

Sources:
- WordPress `wp_handle_upload` API:
  https://developer.wordpress.org/reference/functions/wp_handle_upload/
- WordPress server hardening:
  https://developer.wordpress.org/advanced-administration/security/hardening/
- Vendor changelog:
  https://elementor.com/pro/changelog/
