#!/usr/bin/env python3
"""Add a pure-Python wheel from PyPI, and the pure-Python wheels it depends on, to a hosted Pyodide folder and register them in the lock file.

Usage: add-pypi-wheel.py <folder, for example v314.0.7> <distribution name> [<version>] [<import name> ...]
Examples:
    add-pypi-wheel.py v314.0.7 pony 0.7.20 pony
    add-pypi-wheel.py v314.0.7 beautifulsoup4 4.14.3 bs4       (also adds soupsieve and typing-extensions)
    add-pypi-wheel.py v314.0.7 requests                          (latest version; also adds urllib3, idna, certifi, charset-normalizer)

Every wheel is downloaded from PyPI, checked against the SHA-256 that PyPI publishes, and copied unchanged (so its license files stay inside it).
It must be a pure-Python wheel (`...-none-any.whl`): a wheel with native code cannot run in Pyodide. The lock file gets an entry for it with its
`depends`, so `pyodide.loadPackagesFromImports` loads the package and its dependencies when a program writes `import <import name>`.

Dependencies (`Requires-Dist` without an `extra ==` marker whose environment markers hold for Pyodide's Python) are resolved like this: a package that
is already in the lock file is reused when its version satisfies the requirement (otherwise the script stops); a new one gets the newest release that
satisfies the requirement and has a pure-Python wheel. Import names that are not given on the command line are read from the wheel itself (its
`top_level.txt`, or the top-level folders and modules of its RECORD).
"""
import hashlib, io, json, re, sys, urllib.request, zipfile
from pathlib import Path
from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

if len(sys.argv) < 3:
    sys.exit(__doc__)
folder = Path(__file__).resolve().parent.parent / sys.argv[1]
lock_path = folder / "pyodide-lock.json"
lock = json.loads(lock_path.read_text())
python_version = lock["info"]["python"]          # for example 3.14.2
environment = {"python_version": ".".join(python_version.split(".")[:2]), "python_full_version": python_version,
               "sys_platform": "emscripten", "platform_system": "Emscripten", "os_name": "posix", "implementation_name": "cpython",
               "platform_python_implementation": "CPython"}


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def pure_wheel(release_files):
    wheels = [f for f in release_files if f["packagetype"] == "bdist_wheel" and f["filename"].endswith("-none-any.whl") and not f.get("yanked")]
    return wheels[0] if wheels else None


def pick_version(name, requirement):
    """The newest release of `name` that satisfies `requirement` (a specifier set) and has a pure-Python wheel."""
    project = json.loads(fetch(f"https://pypi.org/pypi/{name}/json"))
    for version in sorted(project["releases"], key=Version, reverse=True):
        parsed = Version(version)
        if parsed.is_prerelease or parsed.is_devrelease or not requirement.contains(parsed):
            continue
        if pure_wheel(project["releases"][version]):
            return version
    sys.exit(f"{name}: no release satisfies {requirement or 'any version'} with a pure-Python wheel")


def import_names(data):
    with zipfile.ZipFile(io.BytesIO(data)) as wheel:
        names = wheel.namelist()
        top = [n for n in names if n.endswith(".dist-info/top_level.txt")]
        if top:
            found = [line.strip() for line in wheel.read(top[0]).decode().splitlines() if line.strip()]
        else:
            found = sorted({n.split("/")[0] if "/" in n else n[:-3] for n in names if not n.split("/")[0].endswith((".dist-info", ".data")) and (("/" in n) or n.endswith(".py"))})
    return [n for n in found if not n.startswith("_") and n != "tests"] or found


def add(name, version, imports, added):
    key = canonicalize_name(name)
    if key in added:
        return
    release = json.loads(fetch(f"https://pypi.org/pypi/{name}/{version}/json"))
    wheel = pure_wheel(release["urls"])
    if not wheel:
        sys.exit(f"{name} {version} has no pure-Python (-none-any) wheel")
    data = fetch(wheel["url"])
    digest = hashlib.sha256(data).hexdigest()
    if digest != wheel["digests"]["sha256"]:
        sys.exit(f"SHA-256 mismatch for {wheel['filename']}: {digest} != {wheel['digests']['sha256']}")
    added[key] = None                                  # guards against a dependency cycle
    depends = []
    for text in release["info"].get("requires_dist") or []:
        requirement = Requirement(text)
        if requirement.marker is not None and not requirement.marker.evaluate({**environment, "extra": ""}):
            continue                                   # an extra, or a marker that does not hold here
        dependency = canonicalize_name(requirement.name)
        if dependency in lock["packages"]:
            hosted = lock["packages"][dependency]["version"]
            if not requirement.specifier.contains(Version(hosted), prereleases=True):
                sys.exit(f"{name} {version} needs {text} but {dependency} {hosted} is hosted")
        else:
            add(requirement.name, pick_version(requirement.name, requirement.specifier), None, added)
        depends.append(dependency)
    (folder / wheel["filename"]).write_bytes(data)
    lock["packages"][key] = {
        "depends": sorted(depends), "file_name": wheel["filename"], "imports": imports or import_names(data), "install_dir": "site", "name": key,
        "package_type": "package", "sha256": digest, "tool": {}, "unvendored_tests": False, "version": version,
    }
    added[key] = wheel["filename"]
    print(f"{folder.name}: added {wheel['filename']} ({len(data)} bytes, sha256 {digest}), license {release['info'].get('license_expression') or release['info'].get('license')}, depends {sorted(depends)}, imports {lock['packages'][key]['imports']}")


name = sys.argv[2]
version = (sys.argv[3] if len(sys.argv) > 3 else "") or None
imports = sys.argv[4:] or None
if version is None:
    version = pick_version(name, Requirement(name).specifier)
add(name, version, imports, {})
lock["packages"] = dict(sorted(lock["packages"].items()))
lock_path.write_text(json.dumps(lock, separators=(",", ":")))
