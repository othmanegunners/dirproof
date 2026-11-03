import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from dirproof.cli import main
from dirproof.core import ManifestError, compare, read_manifest, snapshot, validate
from dirproof.ignore import read_exclusion_patterns


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

    def test_exclusion_file(self):
        (self.root / 'ignore.txt').write_text('# comment\n\n*.log\ncache/**\n')
        self.assertEqual(read_exclusion_patterns(self.root / 'ignore.txt'), ['*.log', 'cache/**'])
        (self.root / 'keep.txt').write_text('keep')
        (self.root / 'skip.log').write_text('log')
        (self.root / 'cache').mkdir()
        (self.root / 'cache' / 'generated.txt').write_text('hidden')
        out = self.root / 'snapshot.json'
        self.assertEqual(main(['snapshot', str(self.root), '--out', str(out),
                               '--exclude-from', str(self.root / 'ignore.txt')]), 0)
        paths = [entry['path'] for entry in read_manifest(out)['files']]
        self.assertIn('keep.txt', paths)
        self.assertNotIn('skip.log', paths)
        self.assertNotIn('cache/generated.txt', paths)

    def test_json_report_when_no_change(self):
        (self.root / 'a.txt').write_text('hi')
        output = self.root / 'manifest.json'
        self.assertEqual(main(['snapshot', str(self.root), '--out', str(output)]), 0)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(['verify', str(self.root), '--manifest', str(output), '--format', 'json'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buffer.getvalue()), {'added': [], 'removed': [], 'changed': []})

    def test_json_report_when_changed(self):
        f = self.root / 'f.txt'
        f.write_text('old')
        out = self.root / 'manifest.json'
        self.assertEqual(main(['snapshot', str(self.root), '--out', str(out)]), 0)
        f.write_text('new')
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(['verify', str(self.root), '--manifest', str(out), '--format', 'json'])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(buffer.getvalue())['changed'], ['f.txt'])

    def test_json_diff(self):
        (self.root / 'f').write_text('a')
        a = self.root / 'a.json'
        b = self.root / 'b.json'
        self.assertEqual(main(['snapshot', str(self.root), '--out', str(a)]), 0)
        (self.root / 'f').write_text('b')
        self.assertEqual(main(['snapshot', str(self.root), '--out', str(b),
                               '--exclude', 'a.json']), 0)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(['diff', str(a), str(b), '--format', 'json'])
        self.assertEqual(code, 1)
        self.assertIn('f', json.loads(buffer.getvalue())['changed'])

    def test_bad_exclusion_file_reports_error(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(['snapshot', str(self.root), '--exclude-from',
                         str(self.root / 'missing.txt')])
        self.assertEqual(code, 2)
        self.assertIn('Error:', stderr.getvalue())

    def test_empty_directory(self):
        self.assertEqual(snapshot(self.root)['files'], [])

    def test_same_size_different_bytes(self):
        f = self.root / 'data'
        f.write_bytes(b'abcd')
        first = snapshot(self.root)
        f.write_bytes(b'efgh')
        self.assertEqual(compare(first, snapshot(self.root))['changed'], ['data'])

    def test_rejects_duplicate_manifest_paths(self):
        entry = {'path': 'same', 'size': 0, 'sha256': '0' * 64}
        bad = {'version': 1, 'algorithm': 'sha256', 'exclude': [], 'files': [entry, dict(entry)]}
        with self.assertRaises(ManifestError):
            validate(bad)

    def test_filename_unicode_and_spaces(self):
        (self.root / 'résumé file.txt').write_text('été', encoding='utf-8')
        self.assertEqual(snapshot(self.root)['files'][0]['path'], 'résumé file.txt')

    def test_empty_file_checksum(self):
        (self.root / 'empty').touch()
        self.assertEqual(snapshot(self.root)['files'][0]['sha256'],
                         hashlib.sha256(b'').hexdigest())


if __name__ == '__main__':
    unittest.main()
