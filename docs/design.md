# Design notes and limitations

**Why JSON?** A portable, reviewable manifest format that doesn't require a database.

**Why SHA-256?** Strong checksums to detect changes to file content, computed in streaming chunks to avoid loading whole large files in memory.

**What is stored?** Relative POSIX-format paths, file sizes, and SHA-256 checksums. No absolute local paths or timestamps are stored. File lists are sorted for deterministic output.

**What is not included?** File permissions, ownership, modification timestamps, directory entries, or symbolic links. Hard-linked files are listed under each path.

**Symlink behavior:** File and directory symlinks are skipped, so scans do not traverse outside the selected directory.

**Glob behavior:** Python `fnmatch` patterns match relative paths; `*` can match `/`. A pattern ending in `/**` excludes a directory and everything underneath it.

**Known limitations:** Concurrent file changes may yield inconsistent snapshots, unreadable files stop scanning with an error, and manifests are not authenticated or signed.

**Possible future work:** Machine-readable diff output for CI, snapshot signing, clearer progress reporting, and more detailed filesystem metadata.
