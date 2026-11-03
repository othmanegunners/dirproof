# Publishing dirproof-cli

## GitHub release

The `.github/workflows/release-github.yml` workflow runs on a new version on `main`,
builds both a wheel and source archive, runs tests and metadata checks, and publishes
a public GitHub release. The workflow skips an already released version.

## Publish to PyPI — one-time setup

1. Sign in or register at https://pypi.org/ and verify your email.
2. Open https://pypi.org/manage/account/publishing/ to add a *pending* Trusted Publisher:

   | Field | Value |
   |---|---|
   | PyPI project name | `dirproof-cli` |
   | GitHub owner | `othmanegunners` |
   | Repository | `dirproof` |
   | Workflow filename | `publish-pypi.yml` |
   | Environment name | `pypi` |

   Pending publishers do not reserve a package name. Confirm the name is unclaimed.
   If it is taken, choose a different package name, update `pyproject.toml` and the
   workflow, and register the new name.
3. In GitHub, open **Settings → Environments** and configure environment `pypi`.
   Require reviewer approval if available; this is recommended by packaging guidance.
4. Open **Actions → Publish to PyPI → Run workflow** and select `main`.
   Approve the environment if prompted.
5. Verify the distribution at https://pypi.org/project/dirproof-cli/
   and install with `python -m pip install dirproof-cli`.

## Later releases

Increase `version` in `pyproject.toml` before publishing another release; PyPI
does not allow a file/version to be overwritten. Verify CI and the GitHub release
before running the PyPI workflow again.

**Security:** Never disclose your PyPI password or API token. Trusted Publishing
uses GitHub's short-lived OIDC identity instead.
