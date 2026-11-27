"""Lint distributed PHP files using the interpreter under test. No plugins are executed."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
php=shutil.which("php")
if not php:
    print("ERROR: PHP executable not found on PATH", file=sys.stderr)
    sys.exit(2)
files=sorted(p for p in ROOT.rglob("*.php")
             if not any(part in {".git", "dist", "tests", "tools"} for part in p.relative_to(ROOT).parts))
def lint(path):
    try:
        result=subprocess.run([php,"-n","-l",str(path)],text=True,capture_output=True,timeout=20)
        return path, result.returncode, (result.stdout+result.stderr)[-800:]
    except Exception as e:
        return path, 1, str(e)
failures=[]
with ThreadPoolExecutor(max_workers=min(4, os.cpu_count() or 2)) as pool:
    for future in as_completed([pool.submit(lint, p) for p in files]):
        path,code,details=future.result()
        if code:
            failures.append((path,details))
print("Linted",len(files),"PHP files")
for path,details in sorted(failures):
    print("FAIL:", path.relative_to(ROOT),details)
print("RESULT:", "PASS" if not failures else "FAIL", len(failures), "failed")
sys.exit(0 if not failures else 1)
