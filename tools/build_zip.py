"""Create staging-only GPL source ZIP without .git and test tooling."""
from pathlib import Path
import hashlib
import os
import subprocess
import zipfile
import sys
import re
from argparse import ArgumentParser

ap = ArgumentParser(description="Build isolated, tracked-source ZiloMentor release ZIP.")
ap.add_argument("--folder", choices=("zilomentor-pro", "elementor-pro"),
                default="zilomentor-pro",
                help="Default to the independent release folder; legacy only for compatibility tests.")
folder = ap.parse_args().folder

root = Path(__file__).resolve().parents[1]
header = (root / "elementor-pro.php").read_text(encoding="utf-8")
match = re.search(r"^\s*\*\s*Version:\s*(\d+\.\d+\.\d+)\s*$", header, re.M)
if not match:
    raise SystemExit("Invalid ZiloMentor Pro release version")
version = match.group(1)
layout = "independent" if folder == "zilomentor-pro" else "compat"
dest = root / "dist" / f"zilomentor-pro-{layout}-{version}-staging-only.zip"
dest.parent.mkdir(exist_ok=True)
if not (root / "elementor-pro.php").is_file():
    raise SystemExit("Missing ZiloMentor Pro entrypoint")
if (root / "pro-elements.php").exists():
    raise SystemExit("Unexpected original plugin bootstrap")
excluded = {".git",".github","dist","tools","tests","__pycache__"}
unsafe_names = {
    "error_log", "debug.log", "wp-config.php", ".env", ".env.local",
    "id_rsa", "id_ed25519", "credentials.json",
}
unsafe_suffixes = {".log", ".sql", ".sqlite", ".db", ".pem", ".key", ".bak", ".old"}
# Packaging MUST use Git-tracked source only, not rglob(): cPanel can create
# untracked error_log files and .ea-php-cli caches inside a checkout. A local
# runtime file must never be distributed in an installable WordPress ZIP.
tracked = subprocess.run(
    ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True,
).stdout.split(b"\0")
files = []
for item in tracked:
    if not item:
        continue
    rel = Path(os.fsdecode(item))
    if (
        any(x in excluded for x in rel.parts)
        or any(x.startswith(".ea-php-cli") for x in rel.parts)
        or rel.name.lower() in unsafe_names
        or rel.suffix.lower() in unsafe_suffixes
        or any(x.startswith(".") for x in rel.parts)
    ):
        continue
    candidate = root / rel
    if not candidate.is_file() or candidate.is_symlink():
        raise SystemExit("Tracked release file missing or symlinked: " + str(rel))
    if candidate.stat().st_size > 15 * 1024 * 1024:
        raise SystemExit("Tracked file exceeds plugin packaging cap: " + str(rel))
    files.append(candidate)
files.sort()
if len(files) < 1000:
    raise SystemExit("Release packaging source unexpectedly incomplete")
with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:
        archive_path=folder+"/"+p.relative_to(root).as_posix()
        z.write(p,arcname=archive_path)
with zipfile.ZipFile(dest) as z:
    bad = z.testzip()
    assert bad is None, bad
    assert folder + "/elementor-pro.php" in z.namelist()
    assert folder + "/license.txt" in z.namelist()
print("PATH",dest)
print("FILES",len(files))
print("SIZE_BYTES",dest.stat().st_size)
print("SHA256",hashlib.sha256(dest.read_bytes()).hexdigest())
