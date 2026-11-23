#!/usr/bin/env python3
"""Export local job data into compact, Git-friendly snapshots (no network calls)."""
import gzip
from pathlib import Path
import sqlite3
import tempfile

from jobs import atomic_write


def export(root):
    root = Path(root)
    data, snapshots = root / 'data', root / 'snapshots'
    for name in ('jobs.sqlite3', 'jobs.json', 'report.html'):
        if not (data / name).is_file():
            raise FileNotFoundError(f'Missing {data / name}; run jobs.py collect first')
    with tempfile.TemporaryDirectory() as directory:
        backup = Path(directory) / 'jobs.sqlite3'
        with sqlite3.connect(f'{(data / "jobs.sqlite3").resolve().as_uri()}?mode=ro', uri=True) as source:
            with sqlite3.connect(backup) as target:
                source.backup(target)
        atomic_write(snapshots / 'jobs.sqlite3.gz', gzip.compress(backup.read_bytes(), mtime=0))
    atomic_write(snapshots / 'jobs.json.gz', gzip.compress((data / 'jobs.json').read_bytes(), mtime=0))
    atomic_write(snapshots / 'report.html', (data / 'report.html').read_bytes())
    print(f'Exported database, JSON and HTML report to {snapshots}')


if __name__ == '__main__':
    export(Path(__file__).resolve().parent)
