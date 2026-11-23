<p align="center">
  <img src="assets/hero.svg" alt="Job Harvester — local job search for backend, applied AI and distributed systems" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&amp;logoColor=white" alt="Python 3.10 or later">
  <img src="https://img.shields.io/badge/Dependencies-zero-166534" alt="Zero runtime dependencies">
  <img src="https://img.shields.io/badge/Storage-SQLite%20%2B%20JSON-334155" alt="SQLite and JSON storage">
</p>

Collect backend, applied-AI and distributed-systems jobs into a **searchable, local HTML report**. Public sources, Python’s standard library, no API keys.

## Start in three commands

```sh
git clone https://github.com/nerdynaman/job-harvester.git
cd job-harvester
python3 jobs.py collect
```

Open `data/report.html` in your browser (`open data/report.html` on macOS). Collection needs internet; browsing the generated report does not need a server.

## Find the roles that fit

- **Search your way:** match any keyword, quote phrases, and search multi-select company, source and location filters.
- **Screen with evidence:** select experience groups together and view disclosed compensation on each card. Full descriptions stay expandable.
- **Keep your history:** SQLite + JSON, URL deduplication, source-health reporting and preserved data when a source fails.

```mermaid
flowchart LR
    A[Public APIs & feeds] --> B[Collect & deduplicate]
    B --> C[(SQLite + JSON)]
    C --> D[Screen roles & experience]
    D --> E[Searchable HTML report]
```

## Where jobs come from

**41 configured sources:** 33 employer boards and eight discovery sources.

| Employer boards | Discovery sources |
| --- | --- |
| Greenhouse · Lever · Ashby | Remote OK · Remotive · We Work Remotely · Arbeitnow · Jobicy · HN Who is hiring · HN Jobs · Y Combinator |

Coverage is a watchlist and rolling feeds, not every opening on each platform. YC uses selected public pages; HN hiring threads and HN Jobs are separate sources. See [source details](docs/USAGE.md#source-contracts) and the [company registry](sources.json).

## Tune your search

```sh
# Rebuild from stored jobs with a different experience target.
python3 jobs.py report --years 1

# Refresh selected sources only.
python3 jobs.py collect --source ycombinator --source hackernews-jobs
```

Defaults show detected requirements of **≤2 years** plus explicit **any experience / new grads welcome**. Unclear and above-target experience are optional. Current role rules exclude frontend, full-stack, ML, DevOps, QA, internships and senior/lead titles; [review the screening rules](docs/USAGE.md#matching-your-search).

Experience is a screening hint, compensation is not estimated, and remote does not imply worldwide eligibility. Check the original listing before applying.

## Develop & sync

```sh
python3 -m unittest -q
node test_report.js       # Node is only needed for UI checks.
python3 snapshot_data.py # Export compressed data + HTML into snapshots/.
```

[Full usage & configuration](docs/USAGE.md) · [Source contracts](docs/USAGE.md#source-contracts) · [Snapshot backup & restore](docs/USAGE.md#github-data-snapshots)

Collected listings belong to their original sources; check provider terms before redistributing them. Local caches and working data stay out of Git.
