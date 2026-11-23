import gzip
from pathlib import Path
import sqlite3
import tempfile
import unittest

from snapshot_data import export


class SnapshotTests(unittest.TestCase):
    def test_exported_database_can_be_restored_with_jobs_intact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / 'data'
            data.mkdir()
            with sqlite3.connect(data / 'jobs.sqlite3') as conn:
                conn.execute('CREATE TABLE jobs (id INTEGER PRIMARY KEY, title TEXT)')
                conn.execute('INSERT INTO jobs VALUES (?, ?)', (1, 'Backend Engineer'))
            (data / 'jobs.json').write_text('{"jobs": [{"title": "Backend Engineer"}]}')
            (data / 'report.html').write_text('<html>Backend Engineer</html>')
            export(root)
            snapshots = root / 'snapshots'
            restored = root / 'restored.sqlite3'
            restored.write_bytes(gzip.decompress((snapshots / 'jobs.sqlite3.gz').read_bytes()))
            with sqlite3.connect(restored) as conn:
                self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(conn.execute('SELECT title FROM jobs').fetchone()[0], 'Backend Engineer')
            self.assertEqual(gzip.decompress((snapshots / 'jobs.json.gz').read_bytes()), (data / 'jobs.json').read_bytes())
            self.assertEqual((snapshots / 'report.html').read_bytes(), (data / 'report.html').read_bytes())

    def test_missing_inputs_do_not_replace_existing_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'snapshots').mkdir()
            target = root / 'snapshots' / 'jobs.sqlite3.gz'
            target.write_bytes(b'previous snapshot')
            with self.assertRaises(FileNotFoundError):
                export(root)
            self.assertEqual(target.read_bytes(), b'previous snapshot')
