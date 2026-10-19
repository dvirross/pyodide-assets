# pyodide-assets

Self-hosted runtime files for the Python code widgets on [dvirross.com](https://dvirross.com) (course pages that let students run Python in the browser).

- Served by a separate Cloudflare Pages project at `pyodide.dvirross.com`, so the main site repository stays small.
- Contents are the [Pyodide](https://pyodide.org) core and only the packages the courses need (planned: `numpy`, `pandas`, later `matplotlib` and `scipy`), in a folder named after the pinned Pyodide version, for example `v0.27.0/`.
- Pyodide is distributed under the Mozilla Public License 2.0; the bundled packages keep their own licenses.
- Nothing here is edited by hand: files are copied unchanged from an official Pyodide release.

The widget on dvirross.com loads `pyodide.dvirross.com/<version>/...` only when a student presses "Run".
