"""Command-line application."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from .core import ManifestError, compare, read_manifest, snapshot


def show_changes(changes: dict[str, list[str]]) -> bool:
    found = False
    for category in ('added', 'removed', 'changed'):
        for path in changes[category]:
            print(f'{category.upper():8} {path}')
            found = True
    if not found:
        print('OK: no differences')
    return found


def save_atomic(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                         prefix='.dirproof-', suffix='.tmp', delete=False) as f:
            temporary = f.name
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='dirproof', description='Offline SHA-256 directory snapshot and verification tool')
    sub = parser.add_subparsers(dest='cmd', required=True)
    snap = sub.add_parser('snapshot', help='Create a reproducible JSON inventory')
    snap.add_argument('directory', type=Path)
    snap.add_argument('--out', type=Path, default=Path('dirproof-manifest.json'))
    snap.add_argument('--exclude', action='append', default=[], metavar='GLOB', help='Repeatable relative-path glob')
    verify = sub.add_parser('verify', help='Verify current files against a saved inventory')
    verify.add_argument('directory', type=Path)
    verify.add_argument('--manifest', required=True, type=Path)
    diff = sub.add_parser('diff', help='Compare two saved inventories')
    diff.add_argument('before', type=Path)
    diff.add_argument('after', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.cmd == 'snapshot':
            root, output = args.directory.expanduser().resolve(), args.out.expanduser().resolve()
            excludes = list(args.exclude)
            if output.is_relative_to(root):
                own_path = output.relative_to(root).as_posix()
                if own_path not in excludes:
                    excludes.append(own_path)
            data = snapshot(root, excludes)
            save_atomic(output, data)
            print(f'Saved {len(data["files"])} files to {output}')
            return 0
        if args.cmd == 'verify':
            baseline = read_manifest(args.manifest)
            return int(show_changes(compare(baseline, snapshot(args.directory, baseline['exclude']))))
        return int(show_changes(compare(read_manifest(args.before), read_manifest(args.after))))
    except (OSError, ValueError, ManifestError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
