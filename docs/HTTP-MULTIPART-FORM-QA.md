# Classic Form actual HTTP multipart and attach-only mail acceptance

**21 November 2026.** This is reproducible, author-created evidence from
the independent ZiloMentor Pro 0.1.2 **unreleased** development candidate.

## Why an HTTP test matters

A direct call to `is_form_upload_content_safe()` establishes only
content-validator behaviour. It cannot prove that Apache/Nginx, PHP's
multipart parser, Elementor's `$_FILES` index normalisation,
`Form_Record`, action dispatch, saved filenames and attachment cleanup
all agree. In particular,
[CVE-2026-32475](https://wpscan.com/vulnerability/0e3b703e-c2f5-406a-af9a-d50587d04706/)
was a critical earlier vendor Elementor Pro file upload flaw triggered
by an **empty first file slot** preceding a second executable upload.
Do not certify immunity from the source version number alone.

## Test fixture design

The disposable WordPress seed
`tests/fixtures/seed_synthetic.php` creates two **published test-only
Elementor Form widgets**:

1. Link mode (`upload_form_link`), preserving uploaded files under
   `wp-content/uploads/elementor/forms/`.
2. Attach-only mode (`upload_form_attach`), running the real Form Email
   action and removing only its own temporary attachment after sending.

Both permit up to three allowed PDF, DOCX, TXT or PNG attachments. Each
request includes synthetic `.invalid` addresses. The generated,
disposable must-use plugin intercepts `pre_wp_mail` before transport and
records **only** attachment count, file presence, validated directory
scope and SHA-256 digests, never message body/recipient or real mail.

The test launches `curl` inside the private WordPress Docker network
to POST actual `multipart/form-data` directly to
`/wp-admin/admin-ajax.php`. File bytes come only from the independent,
self-authored fixtures created in `/tmp/zmp-realfiles-*`. Nothing is
sent to the public shop or an external server. The test additionally
inspects the disposable filesystem for unexpected retained files.

## Assertions and observed results

| End-to-end request | Required behaviour |
| --- | --- |
| Real PDF in **link mode** | HTTP 200 / JSON success, exactly one newly retained copy, random 32-hex-character basename, bytes match original |
| Real DOCX in **attach-only mode** | HTTP 200 / JSON success, exactly one safe attachment observed at `wp_mail` interception, SHA-256 matches original, file removed after email action |
| Fake PDF containing PHP | JSON failure; no file stored |
| Script content with allowed `.txt` extension | JSON failure; no file stored |
| Valid PNG with appended PHP-bearing ZIP archive | JSON failure; no file stored |
| Empty-name first slot followed by a `.php` part | JSON failure; no executable or any other file stored |
| Four valid files against `max_files=3` | JSON failure; no file stored |
| Two genuine files in one request | JSON success, two distinct retained files, cryptographically random basenames, both expected formats present |

The eight HTTP regressions passed in the disposable QA run at source
`f35b7cb982f66c5d5c0cb878206d748d2cf426ac` (the HTTP harness
subsequently received an equivalent explicit hashlib import). They
were **not** executed on production.

## Limitations

This confirms representative genuine HTTP Form submission and its
intercepted email action, not delivery to a real mailbox, SMTP
connectivity, spam filtering, every third-party Form action or every
MIME/media alias. A true recipient-delivery test is inappropriate
without the owner's permission; provider, abuse/rate-limit,
accessibility and independent security audit remain separate gates.

The dedicated synthetic file store and entire WordPress+MariaDB
database are cleaned when the test finishes. Never stage live customer
files in this harness.

Run with `--source-wordpress`,
`--web-server nginx-fpm`, `--plugin-folder zilomentor-pro`,
`--real-file-fixtures-dir /tmp/zmp-realfiles-<disposable>` and
`--verify-apache-uploads`. See
[REAL-FORMAT-UPLOAD-QA.md](REAL-FORMAT-UPLOAD-QA.md) for the
no-subscription Docker file generator.
