"""Create staging-only GPL source ZIP without .git and test tooling."""
from pathlib import Path
import hashlib
import zipfile
import sys
import re

root = Path(__file__).resolve().parents[1]
header = (root / "elementor-pro.php").read_text(encoding="utf-8")
match = re.search(r"^\\s*\\*\\s*Version:\\s*(\\d+\\.\\d+\\.\\d+)\\s*$", header, re.M)
if not match:
    raise SystemExit("Invalid ZiloMentor Pro release version")
version = match.group(1)
dest = root / "dist" / f"zilomentor-pro-compat-{version}-staging-only.zip"
dest.parent.mkdir(exist_ok=True)
if not (root / "elementor-pro.php").is_file():
    raise SystemExit("Missing ZiloMentor Pro entrypoint")
if (root / "pro-elements.php").exists():
    raise SystemExit("Unexpected original plugin bootstrap")
excluded = {".git",".github","dist","tools","tests","__pycache__"}
files = sorted(p for p in root.rglob("*") if p.is_file()
               and not p.is_symlink()
               and not any(x in excluded for x in p.relative_to(root).parts)
               # cPanel EA-PHP may create short-lived CLI cache files next to
               # parsed sources; never include those in installable packages.
               and not p.name.startswith(".ea-php-cli"))
with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:
        archive_path="elementor-pro/"+p.relative_to(root).as_posix()
        z.write(p,arcname=archive_path)
with zipfile.ZipFile(dest) as z:
    bad = z.testzip()
    assert bad is None, bad
    assert "elementor-pro/elementor-pro.php" in z.namelist()
    assert "elementor-pro/license.txt" in z.namelist()
print("PATH",dest)
print("FILES",len(files))
print("SIZE_BYTES",dest.stat().st_size)
print("SHA256",hashlib.sha256(dest.read_bytes()).hexdigest())
