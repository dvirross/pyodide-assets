#!/usr/bin/env python3
"""Add one pure-Python wheel from PyPI to a hosted Pyodide folder and register it in the lock file.

Usage: add-pypi-wheel.py <folder, for example v314.0.7> <distribution name> <version> <import name> [<import name> ...]
Example: add-pypi-wheel.py v314.0.7 pony 0.7.20 pony

The wheel is downloaded from PyPI, checked against the SHA-256 that PyPI publishes, and copied unchanged. It must be a
`py3-none-any` wheel with no dependencies (a wheel with native code cannot run in Pyodide). The lock file gets an entry
for it, so `pyodide.loadPackagesFromImports` loads it when a program writes `import <import name>`.
"""
import hashlib, json, sys, urllib.request
from pathlib import Path

folder, name, version, imports = Path(__file__).resolve().parent.parent / sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
if not imports:
    sys.exit(__doc__)
with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=60) as response:
    release = json.load(response)
if release["info"].get("requires_dist"):
    sys.exit(f"{name} {version} has dependencies {release['info']['requires_dist']}: add them first or use another method")
wheels = [f for f in release["urls"] if f["packagetype"] == "bdist_wheel" and f["filename"].endswith("-py3-none-any.whl")]
if not wheels:
    sys.exit(f"{name} {version} has no py3-none-any wheel")
wheel = wheels[0]
with urllib.request.urlopen(wheel["url"], timeout=120) as response:
    data = response.read()
digest = hashlib.sha256(data).hexdigest()
if digest != wheel["digests"]["sha256"]:
    sys.exit(f"SHA-256 mismatch for {wheel['filename']}: {digest} != {wheel['digests']['sha256']}")
(folder / wheel["filename"]).write_bytes(data)

lock_path = folder / "pyodide-lock.json"
lock = json.loads(lock_path.read_text())
lock["packages"][name] = {
    "depends": [], "file_name": wheel["filename"], "imports": imports, "install_dir": "site", "name": name,
    "package_type": "package", "sha256": digest, "tool": {}, "unvendored_tests": False, "version": version,
}
lock["packages"] = dict(sorted(lock["packages"].items()))
lock_path.write_text(json.dumps(lock, separators=(",", ":")))
print(f"{folder.name}: added {wheel['filename']} ({len(data)} bytes, sha256 {digest}), license {release['info'].get('license_expression') or release['info'].get('license')}")
