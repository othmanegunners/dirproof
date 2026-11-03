"""Offline directory snapshots with reproducible JSON manifests."""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable

VERSION = 1
CHUNK_SIZE = 1024 * 1024


class ManifestError(ValueError):
    """Unsupported or malformed manifest."""


def excluded(relative: str, patterns: Iterable[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatchcase(relative, pattern):
            return True
        if pattern.endswith('/**'):
            prefix = pattern[:-3].rstrip('/')
            if relative == prefix or relative.startswith(prefix + '/'):
                return True
    return False


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b''):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(directory: str | Path, excludes: Iterable[str] = ()) -> dict[str, Any]:
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f'Not a directory: {directory}')
    patterns = sorted(set(excludes))
    if any(not isinstance(x, str) or not x for x in patterns):
        raise ValueError('Exclude patterns must be nonempty strings')
    files = []

    def onerror(error: OSError) -> None:
        raise error

    for current, folders, names in os.walk(root, topdown=True, followlinks=False, onerror=onerror):
        base = Path(current)
        folders[:] = [name for name in sorted(folders)
                      if not (base / name).is_symlink()
                      and not excluded((base / name).relative_to(root).as_posix(), patterns)]
        for name in sorted(names):
            path = base / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink() or not path.is_file() or excluded(rel, patterns):
                continue
            files.append({'path': rel, 'size': path.stat().st_size, 'sha256': sha256(path)})
    files.sort(key=lambda item: item['path'])
    return {'version': VERSION, 'algorithm': 'sha256', 'exclude': patterns, 'files': files}


def validate(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict) or manifest.get('version') != VERSION or manifest.get('algorithm') != 'sha256':
        raise ManifestError('Unsupported manifest format')
    patterns, files = manifest.get('exclude'), manifest.get('files')
    if not isinstance(patterns, list) or any(not isinstance(x, str) or not x for x in patterns):
        raise ManifestError('Invalid exclude patterns')
    if not isinstance(files, list):
        raise ManifestError('Invalid file list')
    seen = set()
    for item in files:
        if not isinstance(item, dict):
            raise ManifestError('Invalid file entry')
        path, size, digest = item.get('path'), item.get('size'), item.get('sha256')
        if (not isinstance(path, str) or not path or path.startswith('/') or '\\' in path
                or any(part in ('', '.', '..') for part in path.split('/')) or path in seen):
            raise ManifestError(f'Invalid or duplicate path: {path!r}')
        seen.add(path)
        if type(size) is not int or size < 0 or not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest):
            raise ManifestError(f'Invalid file metadata: {path}')
    return manifest


def read_manifest(path: str | Path) -> dict[str, Any]:
    try:
        with Path(path).expanduser().open(encoding='utf-8') as stream:
            return validate(json.load(stream))
    except json.JSONDecodeError as exc:
        raise ManifestError(f'Invalid JSON: {exc.msg}') from exc


def compare(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[str]]:
    validate(before)
    validate(after)
    a = {x['path']: x for x in before['files']}
    b = {x['path']: x for x in after['files']}
    return {
        'added': sorted(b.keys() - a.keys()),
        'removed': sorted(a.keys() - b.keys()),
        'changed': sorted(path for path in a.keys() & b.keys()
                          if (a[path]['size'], a[path]['sha256']) != (b[path]['size'], b[path]['sha256']))
    }
