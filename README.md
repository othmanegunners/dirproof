# dirproof

**Check whether the files in a directory have changed — offline and without runtime dependencies.**

`dirproof` is a small open-source command-line tool that creates portable JSON snapshots of file paths, sizes, and SHA-256 hashes. Use it to compare a project folder against a saved snapshot, or to compare two saved snapshots. No API keys, cloud uploads, or accounts required.

## Features

- **`snapshot`** — create a stable, sorted JSON inventory of a directory.
- **`verify`** — list added, removed, or changed files compared with a snapshot.
- **`diff`** — compare two previously saved snapshots without rescanning a folder.
- **`--exclude` / `--exclude-from`** — ignore matching paths using command-line glob patterns or reusable UTF-8 pattern files.
- **`--format json`** — emit machine-readable results for CI, scripts, and dashboards.
- **Portable** — Python 3.10+ on macOS, Linux, and Windows.
- **Non-destructive** — scans do not edit files or follow symlinks.

## Install

Once the package is published on PyPI, install it with:

```bash
python -m pip install dirproof-cli
```

You can also install directly from GitHub:

```bash
git clone https://github.com/othmanegunners/dirproof.git
cd dirproof
python -m pip install -e .
```

## Quick start

```bash
# Save an inventory outside the folder being scanned
dirproof snapshot ./my-project --out ./snapshot.json

# Later, check the same folder for changes
dirproof verify ./my-project --manifest ./snapshot.json

# Exclude Git metadata and compiled Python files
dirproof snapshot ./my-project --out ./snapshot.json --exclude '.git/**' --exclude '*.pyc'

# Load exclusions from a file (blank lines and # comments are ignored)
dirproof snapshot ./my-project --out ./snapshot.json --exclude-from .dirproofignore

# Export a change report suitable for CI parsing
dirproof verify ./my-project --manifest ./snapshot.json --format json
```

To compare two snapshots:

```bash
dirproof snapshot ./my-project --out ./before.json
# Change something in ./my-project
dirproof snapshot ./my-project --out ./after.json
dirproof diff ./before.json ./after.json
```

Example report:

```text
ADDED    docs/new.md
REMOVED  old.txt
CHANGED  src/main.py
```

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success; no differences for `verify` or `diff`. |
| `1` | Differences found by `verify` or `diff`. |
| `2` | Invalid input or I/O error. |

## Manifest format

```json
{
  "version": 1,
  "algorithm": "sha256",
  "exclude": [".git/**"],
  "files": [
    {
      "path": "hello.txt",
      "size": 5,
      "sha256": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    }
  ]
}
```

Paths are relative to the scanned folder, without machine-specific absolute paths. Exclusion rules are saved with the manifest and reused during verification. If you save the manifest *inside* the scanned folder, it is automatically excluded so it doesn't invalidate itself.

## Tests

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [docs/usage.md](docs/usage.md), [docs/design.md](docs/design.md), [SECURITY.md](SECURITY.md), and [LICENSE](LICENSE).

## Important security note

SHA-256 detects accidental changes, but this tool does **not** cryptographically authenticate a manifest. An attacker who can modify both the files and the JSON snapshot may conceal changes. Store trusted snapshots separately or sign them in workflows that need tamper-evidence.
