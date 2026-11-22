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

## Beautiful Soup and requests (2026-11-13)

`beautifulsoup4` 4.15.0 (MIT), `soupsieve` 4.1 (MIT), `typing_extensions` 4.16.0 (PSF-2.0), `requests` 2.34.2 (Apache-2.0), `urllib3` 2.8.0 (MIT), `idna` 3.20 (BSD-3-Clause), `certifi` 2026.10.23 (MPL-2.0) and `charset-normalizer` 3.5.2 (MIT) were added for the data-collection lessons (together about 690 KB, loaded only when a lesson box imports them). All are pure-Python `py3-none-any` wheels, copied unchanged with their license files. They were produced with:

```
python3 scripts/add-pypi-wheel.py v314.0.7 beautifulsoup4 "" bs4
python3 scripts/add-pypi-wheel.py v314.0.7 requests
```

`scripts/add-pypi-wheel.py` now also accepts a wheel that has dependencies: it reads `Requires-Dist` (skipping extras and markers that do not hold for Pyodide's Python), reuses a hosted package whose version satisfies the requirement, otherwise adds the newest release with a pure-Python wheel, writes `depends` into the lock file and takes the import names from the wheel (`top_level.txt`) unless given. With `loadPackagesFromImports`, `from bs4 import BeautifulSoup` loads `beautifulsoup4`, `soupsieve` and `typing_extensions`; `import requests` loads `requests`, `urllib3`, `idna`, `certifi` and `charset-normalizer`.

Checked in the real worker of dvirross.com (Chromium, the site's Content-Security-Policy): `requests.get` of a same-origin page works without `pyodide-http` (urllib3 2.x talks to the browser's XMLHttpRequest from the worker), `BeautifulSoup(html, "html.parser")`, `find_all`, `class_`, `get` and `select` work. The pages of other origins are blocked by the site's `connect-src`, by design. The 17 packages hosted before are byte-for-byte unchanged (the lock-file entries are identical).

## wikipedia-api (added 2026-11-22)

`wikipedia-api` 0.16.0 (MIT) and its pure-Python dependencies `httpx` 0.28.1 (BSD-3-Clause), `httpcore` 1.0.9 (BSD-3-Clause), `h11` 0.16.0 (MIT), `anyio` 4.16.0 (MIT), `click` 8.5.0 (BSD-3-Clause) and `tenacity` 9.1.4 (Apache-2.0) were added for the data-collection API lesson (about 594 KB, loaded only when a box imports `wikipediaapi`). `idna`, `certifi` and `typing_extensions` were already hosted. Produced with:

```
python3 scripts/add-pypi-wheel.py v314.0.7 wikipedia-api 0.16.0 wikipediaapi
```

The site answers the library's requests from saved Wikipedia answers (the page's `connect-src` blocks other origins); the wheels themselves are unchanged copies from PyPI.
