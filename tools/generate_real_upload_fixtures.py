#!/usr/bin/env python3
"""Make genuine, self-authored Office/ODF/PDF/media QA files in /tmp only.

Uses free open-source python-docx, openpyxl, odfpy, reportlab, Pillow and
an existing ffmpeg executable. No proprietary/vendor sample, real PII,
customer content, external email, network or production directory is needed.
All output is solely disposable synthetic WordPress security test input.

Install these QA-only development dependencies in a disposable virtualenv:
  python -m pip install -r tools/requirements-qa-real-files.txt
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave
import zipfile

from docx import Document
from openpyxl import Workbook, load_workbook
from odf import draw, table, text
from odf.opendocument import OpenDocumentPresentation, OpenDocumentSpreadsheet, OpenDocumentText, load
from PIL import Image
from reportlab.pdfgen import canvas


def generate(out: Path):
    out = out.resolve(strict=True)
    if not out.is_dir() or out.is_symlink():
        raise ValueError("Fixture destination must be a genuine empty directory")
    if (not str(out).startswith(str(Path(tempfile.gettempdir()).resolve()) + "/")
            and str(out) != "/out"):
        raise ValueError("Only /tmp or the dedicated disposable Docker /out mount is permitted")
    if any(out.iterdir()):
        raise ValueError("Fixture directory must be empty; refusing to overwrite")

    # Genuine Office Open XML documents via established Office libraries.
    doc = Document()
    doc.add_heading("ZiloMentor authorised upload-format verification", level=1)
    doc.add_paragraph("Self-authored synthetic document, no customer data.")
    t = doc.add_table(rows=2, cols=2)
    t.cell(0, 0).text, t.cell(0, 1).text = "Format", "DOCX"
    t.cell(1, 0).text, t.cell(1, 1).text = "Expected", "Allowed"
    doc.save(str(out / "word.docx"))
    check_doc = Document(str(out / "word.docx"))
    assert len(check_doc.paragraphs) >= 2 and len(check_doc.tables) == 1

    wb = Workbook()
    ws = wb.active
    ws.title = "Safe fixture"
    ws.append(("Product", "Units", "Price", "Line total"))
    ws.append(("Synthetic item", 2, 7.49, "=B2*C2"))
    wb.save(out / "spreadsheet.xlsx")
    check_wb = load_workbook(out / "spreadsheet.xlsx", read_only=True)
    assert check_wb.active["A2"].value == "Synthetic item"
    check_wb.close()

    # Full ODF packages with mimetype, content, styles and manifest.
    odt = OpenDocumentText()
    odt.text.addElement(text.P(text="ZiloMentor synthetic ODT paragraph with a real ODF package."))
    odt.save(str(out / "text.odt"), addsuffix=False)
    assert load(str(out / "text.odt")).text is not None

    ods = OpenDocumentSpreadsheet()
    sheet = table.Table(name="Synthetic QA")
    row = table.TableRow()
    cell = table.TableCell(valuetype="string")
    cell.addElement(text.P(text="Verified ODS"))
    row.addElement(cell)
    sheet.addElement(row)
    ods.spreadsheet.addElement(sheet)
    ods.save(str(out / "sheet.ods"), addsuffix=False)
    assert load(str(out / "sheet.ods")).spreadsheet is not None

    odp = OpenDocumentPresentation()
    page = draw.Page(name="Synthetic slide")
    frame = draw.Frame(x="2cm", y="2cm", width="15cm", height="3cm")
    text_box = draw.TextBox()
    text_box.addElement(text.P(text="Valid sample ODP presentation"))
    frame.addElement(text_box)
    page.addElement(frame)
    odp.presentation.addElement(page)
    odp.save(str(out / "slides.odp"), addsuffix=False)
    assert load(str(out / "slides.odp")).presentation is not None

    # Genuine PDF generated with a PDF library and a complete xref table.
    pdf = canvas.Canvas(str(out / "letter.pdf"), pagesize=(595, 842))
    pdf.setTitle("Authorised synthetic PDF for ZiloMentor upload testing")
    pdf.drawString(40, 790, "ZiloMentor self-authored PDF format fixture")
    pdf.drawString(40, 755, "No customer or real personal data.")
    pdf.showPage()
    pdf.save()
    assert (out / "letter.pdf").read_bytes().startswith(b"%PDF-")

    # Valid compact JPEG and PNG produced by a real image encoder.
    img = Image.new("RGB", (16, 16), (220, 234, 244))
    img.save(out / "image.jpg", "JPEG", quality=80)
    img.save(out / "image.png", "PNG")
    for name in ("image.jpg", "image.png"):
        with Image.open(out / name) as im:
            im.verify()

    # Uncompressed PCM WAV. WordPress and PHP finfo can inspect it.
    with wave.open(str(out / "silence.wav"), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"\0\0" * 1600)

    # A real codec and MP4 container rather than a forged 'ftyp' prefix.
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg required for real MP4 QA fixture")
    subprocess.run([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "color=c=black:s=16x16:r=5:d=1",
        "-an", "-c:v", "mpeg4", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-y", str(out / "video.mp4"),
    ], check=True, timeout=30)
    assert (out / "video.mp4").stat().st_size > 500

    # Malicious/suspicious payload fixtures must be denied even when their
    # extensions or leading bytes superficially resemble permitted content.
    (out / "forged.pdf").write_bytes(b"<?php echo 'Do not execute';")
    (out / "script.txt").write_text("<?php echo 'Do not execute';", encoding="utf-8")
    shutil.copy2(out / "image.png", out / "image-zip-polyglot.png")
    with zipfile.ZipFile(out / "image-zip-polyglot.png", "a") as archive:
        archive.writestr("arbitrary.php", "<?php echo 'disallowed';")

    # Checked, fixed fixture names only. A signed release is never built from
    # these files; this manifest is test-only.
    expected = {
        "word.docx": True,
        "spreadsheet.xlsx": True,
        "text.odt": True,
        "sheet.ods": True,
        "slides.odp": True,
        "letter.pdf": True,
        "image.jpg": True,
        "image.png": True,
        "silence.wav": True,
        "video.mp4": True,
        "forged.pdf": False,
        "script.txt": False,
        "image-zip-polyglot.png": False,
    }
    results = {}
    for name, accepted in expected.items():
        data = (out / name).read_bytes()
        results[name] = {
            "accepted": accepted,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    (out / "manifest.json").write_text(
        json.dumps({"format": 1, "generated": "self-authored",
                    "source": "ZiloMentor QA", "files": results},
                   sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"created": len(results), "types": sorted(results),
                      "all_self_authored": True, "bytes": sum(x["size"] for x in results.values())}))


if __name__ == "__main__":
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--out", required=True, type=Path)
    args = argp.parse_args()
    generate(args.out)
