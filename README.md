# pyodide-assets

Self-hosted runtime files for the Python code widgets on [dvirross.com](https://dvirross.com) (course pages that let students run Python in the browser).

- Served by a separate Cloudflare Pages project at `pyodide.dvirross.com`, so the main site repository stays small.
- Contents are the [Pyodide](https://pyodide.org) core and only the packages the courses need (planned: `numpy`, `pandas`, later `matplotlib` and `scipy`), in a folder named after the pinned Pyodide version, for example `v0.27.0/`.
- Pyodide is distributed under the Mozilla Public License 2.0; the bundled packages keep their own licenses.
- Nothing here is edited by hand: files are copied unchanged from an official Pyodide release, except pure-Python wheels that are downloaded from PyPI by `scripts/add-pypi-wheel.py`, which checks the SHA-256 that PyPI publishes and registers the wheel in `pyodide-lock.json`.

The widget on dvirross.com loads `pyodide.dvirross.com/<version>/...` only when a student presses "Run".

## Contents and how it was built

`v314.0.7/` is Pyodide 314.0.7 (Python 3.14, official release) with only these packages and their dependencies: `numpy`, `pandas`, `matplotlib`, `scipy`, `sympy`. It was produced with:

```
python3 scripts/build-subset.py <extracted pyodide-314.0.7 release>/pyodide 314.0.7 numpy pandas matplotlib scipy sympy
```

The script copies the core files and the wheels unchanged and prunes `pyodide-lock.json` to the chosen packages. To upgrade, run it for the new version into a new `v<version>/` folder and point the site at it; old versions can stay so cached pages keep working.

Load it with `loadPyodide({ indexURL: "https://pyodide.dvirross.com/v314.0.7/" })`.

## Extra pure-Python packages

`pony` 0.7.20 (Pony ORM, Apache-2.0, no dependencies, supports Python 3.14) was added for the database lessons. It was produced with:

```
python3 scripts/add-pypi-wheel.py v314.0.7 pony 0.7.20 pony
```

Checked in Pyodide 314.0.7 itself (Node, `loadPackagesFromImports`): `from pony.orm import *` loads the wheel, and a `Database` with an entity class, `select(d for d in Day if ...)`, `.sum()` and `max(...)` run on the in-memory `sqlite3` of Pyodide. Python code in a page loads it automatically when it contains `from pony.orm import *` or `import pony`.
