import hashlib
import tempfile
import unittest
from pathlib import Path

from dirproof.cli import main
from dirproof.core import ManifestError, compare, read_manifest, snapshot, validate


class DirproofTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_order_and_hash(self):
        (self.root / 'z.txt').write_text('hello')
        (self.root / 'a.txt').write_text('world')
        manifest = snapshot(self.root)
        self.assertEqual([entry['path'] for entry in manifest['files']], ['a.txt', 'z.txt'])
        self.assertEqual(manifest['files'][1]['sha256'], hashlib.sha256(b'hello').hexdigest())
        self.assertEqual(snapshot(self.root), manifest)

    def test_detect_added_removed_changed(self):
        (self.root / 'removed.txt').write_text('old')
        (self.root / 'changed.txt').write_text('before')
        baseline = snapshot(self.root)
        (self.root / 'removed.txt').unlink()
        (self.root / 'changed.txt').write_text('after')
        (self.root / 'added.txt').write_text('new')
        self.assertEqual(compare(baseline, snapshot(self.root)), {
            'added': ['added.txt'], 'removed': ['removed.txt'], 'changed': ['changed.txt']})

    def test_exclusions_and_subdirectories(self):
        (self.root / '.git').mkdir()
        (self.root / '.git' / 'config').write_text('x')
        (self.root / 'folder').mkdir()
        (self.root / 'folder' / 'app.py').write_text('code')
        (self.root / 'folder' / 'temp.log').write_text('log')
        result = snapshot(self.root, ['.git/**', '*.log'])
        self.assertEqual([e['path'] for e in result['files']], ['folder/app.py'])

    def test_skips_symlinks(self):
        target = self.root / 'file'
        target.write_text('x')
        try:
            (self.root / 'link').symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unavailable')
        self.assertEqual([e['path'] for e in snapshot(self.root)['files']], ['file'])

    def test_rejects_unsafe_paths(self):
        bad = {'version': 1, 'algorithm': 'sha256', 'exclude': [], 'files': [
            {'path': '../secret', 'size': 1, 'sha256': 'a' * 64}]}
        with self.assertRaises(ManifestError):
            validate(bad)

    def test_cli_snapshot_verify_and_change(self):
        (self.root / 'hello.txt').write_text('hello')
        manifest_file = self.root / 'manifest.json'
        self.assertEqual(main(['snapshot', str(self.root), '--out', str(manifest_file)]), 0)
        self.assertIn('manifest.json', read_manifest(manifest_file)['exclude'])
        self.assertEqual(main(['verify', str(self.root), '--manifest', str(manifest_file)]), 0)
        (self.root / 'hello.txt').write_text('changed')
        self.assertEqual(main(['verify', str(self.root), '--manifest', str(manifest_file)]), 1)

    def test_cli_diff(self):
        f = self.root / 'f'
        f.write_text('a')
        first, second = self.root / 'first.json', self.root / 'second.json'
        self.assertEqual(main(['snapshot', str(self.root), '--out', str(first)]), 0)
        f.write_text('b')
        self.assertEqual(main(['snapshot', str(self.root), '--out', str(second), '--exclude', 'first.json']), 0)
        self.assertEqual(main(['diff', str(first), str(second)]), 1)

    def test_invalid_json(self):
        f = self.root / 'bad.json'
        f.write_text('{not json')
        with self.assertRaises(ManifestError):
            read_manifest(f)


if __name__ == '__main__':
    unittest.main()
