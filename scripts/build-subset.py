#!/usr/bin/env python3
"""Copy the Pyodide core and a chosen set of packages (with dependencies) from an official release into a versioned folder.

Usage: build-subset.py <extracted pyodide release dir> <version> <package> [<package> ...]
Example: build-subset.py /tmp/x/pyodide 314.0.7 numpy pandas matplotlib scipy

Files are copied unchanged. The lock file is pruned to the chosen packages so a browser never lists packages that are not hosted here.
"""
import json, shutil, sys
from pathlib import Path

src, version, wanted = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
out = Path(__file__).resolve().parent.parent / f"v{version}"
lock = json.loads((src / "pyodide-lock.json").read_text())
packages = lock["packages"]

keep, stack = set(), list(wanted)
while stack:
    name = stack.pop()
    if name in keep:
        continue
    keep.add(name)
    stack += packages[name]["depends"]

core = ["pyodide.js", "pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip", "package.json"]
out.mkdir(exist_ok=True)
for name in core:
    shutil.copy2(src / name, out / name)
for name in sorted(keep):
    shutil.copy2(src / packages[name]["file_name"], out / packages[name]["file_name"])
lock["packages"] = {name: packages[name] for name in sorted(keep)}
(out / "pyodide-lock.json").write_text(json.dumps(lock, separators=(",", ":")))
print(f"{out.name}: core + {len(keep)} packages: {', '.join(sorted(keep))}")
