# Reproducible real document / media upload compatibility QA

**21 November 2026.** The previous Office/ODF/audio checks used
deliberately tiny synthetic signatures. The 0.1.2 development branch now
also supports testing genuine formats generated and reopened with independent
open-source document/codec libraries. All content is self-authored with
no real person, email address, order, uploaded customer file or payment.

## File generation and independent structure checks

`tools/generate_real_upload_fixtures.py` makes:

| Valid filename | Independent producer / verification |
| --- | --- |
| `word.docx` | python-docx, reopened with python-docx; contains headings, text and a table |
| `spreadsheet.xlsx` | openpyxl, reopened with openpyxl; contains rows and a formula |
| `text.odt` | odfpy, parsed again as an ODF document |
| `sheet.ods` | odfpy, parsed again as an ODF spreadsheet |
| `slides.odp` | odfpy with an actual master page and page layout; reparsed |
| `letter.pdf` | ReportLab, genuine PDF header and cross-reference |
| `image.jpg`, `image.png` | Pillow, re-opened and verified |
| `silence.wav` | Python's standard WAV PCM writer |
| `video.mp4` | FFmpeg, real MPEG-4 video stream and MP4 container |

Three additional files are **expected to be rejected**:
`forged.pdf` (PHP bytes), `script.txt` (script content), and
`image-zip-polyglot.png` (valid PNG with an appended PHP-carrying ZIP).

A versioned `manifest.json` contains exact byte sizes and SHA-256 hashes
for all 13 files. Disposable WordPress test
`tests/runtime_real_file_uploads.php` verifies that manifest and feeds
each file into the actual ZiloMentor shared Form content validator.
The native Apache and Nginx upload-policy tests remain separate checks.

The generator intentionally creates only within a private
`/tmp/zmp-realfiles-*` directory, or the isolated Docker `/out`
bind mount. On the cPanel server `/tmp` is mounted `noexec`:
a temporary Python virtualenv could not load the `lxml` binary extension.
Rather than weakening mount permissions, all generator dependencies now
run inside a **disposable Docker image** with no runtime network.

## Manual execution on the existing QA server

From a *disposable Git checkout*, never a live WordPress plugin directory:

```bash
docker build -f tools/docker/Dockerfile.qa-real-files -t zmp-real-file-qa:local .

FILES=$(mktemp -d /tmp/zmp-realfiles-XXXXXXXX)
docker run --rm --network none \
  --mount "type=bind,src=$(pwd),dst=/src,readonly" \
  --mount "type=bind,src=$FILES,dst=/out" \
  --entrypoint python zmp-real-file-qa:local \
  /src/tools/generate_real_upload_fixtures.py --out /out

python3 tools/run_manual_checks.py \
  --source-wordpress /path/to/read-only-wordpress-source \
  --plugin-folder zilomentor-pro \
  --web-server nginx-fpm \
  --frontend-playwright-image haven-browser-qa:1.62.1 \
  --verify-apache-uploads \
  --real-file-fixtures-dir "$FILES"

# This directory is 100% generated QA input; do not use a real uploads path.
rm -rf "$FILES"
```

The dedicated Docker image and script require no subscription, no
GitHub Actions, no WordPress database backup, and no third-party customer
sample archive. The full test still uses a private disposable WordPress
network and blocks all outgoing form emails.

## Limitations

- No conclusion about obscure Office/ODF exports, macros, encrypted docs,
  embedded media, unusual MIME aliases or actual end-user uploads.
- Content validator acceptance is not equal to a complete **multipart
  HTTP Form-upload submit-to-email** compatibility test. Such a test
  should be added before releasing file-upload features generally.
- The owner must separately approve the final production web-server
  upload policy; no production upload directory or customer file is
  modified by these commands.
