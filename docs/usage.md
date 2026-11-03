# Recipes and usage

Requires Python 3.10+ and no runtime dependencies.

## 1. Back up a baseline

\`\`\`sh
dirproof snapshot ./my-project --out ./baseline.json
\`\`\`

The SHA-256 manifest contains *relative* paths and does not record absolute paths, timestamps, ownership, or file content. Keep your baseline outside the folder being scanned when possible.

## 2. Verify folder changes

\`\`\`sh
dirproof verify ./my-project --manifest ./baseline.json
\`\`\`

On changes, the command prints \`ADDED\`, \`REMOVED\`, and \`CHANGED\` lines and returns exit code 1. Exit code 2 indicates an error.

## 3. Machine-readable reports

\`\`\`sh
dirproof verify ./my-project --manifest ./baseline.json --format json
dirproof diff ./baseline.json ./new.json --format json
\`\`\`

Example:

\`\`\`json
{
  "added": ["docs/new.md"],
  "changed": ["src/main.py"],
  "removed": []
}
\`\`\`

The report is written to standard output. Scripts can read it even when exit code 1 indicates differences.

## 4. Reuse exclusions

Create a UTF-8 text file named \`.dirproofignore\`:

\`\`\`text
# generated and temporary paths
.git/**
__pycache__/**
*.pyc
dist/**
build/**
\`\`\`

Run:

\`\`\`sh
dirproof snapshot ./my-project --out ./baseline.json --exclude-from .dirproofignore
\`\`\`

Use \`--exclude-from\` more than once to combine files, and combine it with \`--exclude\`.

**Pattern syntax is not identical to .gitignore.** Patterns use Python \`fnmatch\` against relative POSIX-style paths; \`*\` may match slashes. Negated patterns such as \`!important.txt\` are *not* supported.

## 5. Integrate into CI

Store a trusted baseline alongside your build artifacts or in a protected branch. Run \`dirproof verify\` and fail the job when exit code is 1 or 2. To collect the JSON report regardless of changes, capture the command's exit status and upload the report as an artifact.

## 6. Troubleshooting

- Changes to the manifest itself? Save it outside the directory or use \`snapshot --out\` within the directory, which automatically excludes the manifest file.
- Missing files? Check exclusions. Symlinked files are skipped intentionally.
- Unexpected differences? Files may have changed while scanning; rerun on an idle directory.
- Bad manifest? Version 1 requires SHA-256 digests, valid relative paths, and nonnegative file sizes.
