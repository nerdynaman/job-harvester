# Job Harvester · Usage & source details

A local Python command and searchable HTML report. No dependencies, paid APIs,
Treg, browser automation, or language-model calls. Python 3.10 or later.

## Run

```sh
cd /path/to/job-harvester
python3 -m unittest -v
python3 jobs.py collect
open data/report.html
```

The configuration covers 33 employer boards and eight discovery sources (41 sources),
using eleven source types. The complete employer list is in `sources.json`; these are
explicit watchlists, not a search of every employer using those ATS platforms.

Discovery feeds: Remote OK, Remotive, We Work Remotely, Arbeitnow, Jobicy,
HN Who is hiring, HN Jobs, and Y Combinator. Arbeitnow is primarily European; remote labels
still require checking country and work-rights restrictions. Jobicy uses its
free, unauthenticated public API and preserves its listing links.

```sh
# Collect only a few configured sources.
python3 jobs.py collect --source superapp --source secfix --source hackernews

# Rebuild the report without making network requests.
python3 jobs.py report --years 1
```

An exit status of 1 means at least one source failed. Other sources still finish;
previous records remain available and source errors are visible in the report.

Outputs are local, under `data/`:

- `jobs.sqlite3`: persistent listings, first/last collection time, listing state,
  and source health. Repeated runs update source IDs instead of inserting copies.
- `jobs.json`: every stored listing, including excluded and unlisted entries,
  original compensation fields, source links, and screening evidence.
- `report.html`: compact job cards with expandable evidence and descriptions.
  Filter by search, location, experience, company, source, work arrangement and
  pay information. Experience checkboxes can be combined; defaults include a
  numeric minimum at/below the target and explicit open-experience roles.
  Unclear and above-target roles are opt-in. Reset restores these defaults.
  Company, source and location menus have searchable checkbox lists; multiple choices
  match any selected value within that filter. These filters
  combine with each other. No selections means all values. Searching the menu
  keeps current selections; clear selections or reset to remove them.
  Location choices are complete location labels from listings, matched exactly
  once selected; the menu search uses case-insensitive substring matching.
  Remote is not automatically treated as worldwide, and labels are not
  geocoded or expanded into countries/cities.
  Main search matches any comma/space-separated keyword in job details,
  case-insensitively. Double quotes keep a phrase together, for example
  `backend, Python, "distributed systems"`. Other filters still narrow matches. Results show 25 per
  page. Open directly; no server is required.
- `cache/`: six-hour response cache. Running the command repeatedly does not
  continually hit the upstream service. Remotive's own data is delayed 24 hours.

The standalone report UI checks run with `node test_report.js` (Node is only
needed for these checks, not collection or the report).

## Matching your search

- Target 2 years by default; `--years 1` changes the screening target.
- Backend, distributed systems, APIs, databases and applied AI are candidates.
- Frontend, fullstack, ML, DevOps/SRE, QA, internships and senior/lead titles are
  excluded from the report. Raw listings remain in JSON/SQLite.
- `possible` means a numeric experience requirement was found at/below the
  target; it does **not** prove eligibility. `open` means the text explicitly
  welcomes all experience levels/new graduates or requires no experience. A
  numeric requirement takes precedence if both occur. `unknown` and
  `above_target` can be included with the experience checkboxes.
  Preferred requirements, degrees, technology-specific experience and job posts
  advertising several levels require manual review.
- Money snippets are **not salary estimates**: funding and unrelated figures can
  match too. Original structured compensation is preserved when supplied.
- There is deliberately no automatic ₹20L rejection yet. Unknown salary is not
  below ₹20L, USD is not INR, hourly is not annual, and total compensation is not
  base salary. Confirm these before adding a strict numeric salary filter.
- Geography and sponsorship are not inferred. Search locations and read the
  listing. A `Remote` label never means globally eligible by itself.
- `hackernews`: top-level employer comments from the latest monthly Who is hiring
  thread via Algolia. Replies and other discussion threads are not collected.
- `hackernews-jobs`: current posts from HN's separate Jobs section via the official
  Firebase `jobstories` and `item` endpoints. Titles, available body text and
  outgoing job links are collected; external application pages are not crawled.
  Generic titles with no backend hints can therefore be missed.
- `ycombinator`: public YC landing, software-engineering, India and remote pages.
  Repeated jobs across pages are deduplicated by YC ID. Matching roles are
  enriched from their public detail pages with salary, role category, visa notes,
  minimum experience and descriptions. No login or signed-in search is used;
  public category pages are a sample, not the complete YC job catalogue.
  Public HTML is parsed from embedded page data; format changes produce an error
  and preserve previously stored jobs.
- Both HN sources are screening leads marked `review`; comments can advertise
  multiple roles and are not independently confirmed open.

The report removes exact canonical-URL duplicates. Different source URLs for the
same job may remain; automatically merging on company/title would incorrectly
collapse separate requisitions. Canonicalization preserves job ID query fields.

## Add more employers

Append an entry to `sources.json` using the slug in the company's careers URL:

```json
{"name":"example","type":"greenhouse","board":"example","company":"Example"}
```

Use `type: "ashby"` for `jobs.ashbyhq.com/<board>` or `type: "lever"` for
`jobs.lever.co/<board>`. EU Lever/Greenhouse endpoints need a separate adapter.
Unknown/private boards report errors instead of silently returning zero jobs.

## Source contracts

| Type | Public interface | Notes |
| --- | --- | --- |
| Greenhouse | [Job Board API](https://docs.greenhouse.io/job-board.html) | Full job descriptions; no authentication for reading. |
| Lever | [Postings API](https://github.com/lever/postings-api) | All pages collected before replacing the board snapshot. |
| Ashby | [Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api) | Requests compensation; omits unlisted postings; preserves hybrid vs remote. |
| HN Who is hiring | [Algolia HN search](https://hn.algolia.com/api) | Latest monthly thread; top-level comments only. |
| Y Combinator | [Public startup jobs](https://www.ycombinator.com/jobs) | Public engineering/India/remote pages plus matching job details; HTML page data, no authenticated search. |
| HN Jobs | [Official HN API](https://github.com/HackerNews/API) | Current Jobs section via jobstories and individual job items. |
| Arbeitnow | [Free API](https://www.arbeitnow.com/blog/job-board-api) | Latest-results page only (currently up to 300 jobs); European focus; preserves remote metadata. |
| Jobicy | [Public Jobs API](https://jobicy.com/jobs-rss-feed) | Software engineering category, cursor pagination, seven-day feed; no auth or commercial direct-link API. |
| Remote OK | [Public API](https://remoteok.com/api) | Keep Remote OK source name and backlink; no logo reuse. |
| Remotive | [Public API terms](https://remotive.com/remote-jobs/api) | Attribution/backlink required; 24-hour delay; no redistribution to third-party job boards. |
| We Work Remotely | [Public RSS](https://weworkremotely.com/remote-job-rss-feed) | Backend category; retain WWR attribution/backlinks. |

One request per second per host, 30-second timeout, 25 MB response limit, and one
bounded retry for throttling/transient server errors. Requests do not bypass
login, CAPTCHAs or access controls. Third-party descriptions are rendered as
escaped text, and application links must be HTTP(S).

An ATS job missing from a successful complete nonempty board snapshot becomes
`listed=false`; that means absent from this board, not independently confirmed
closed. A failed or unexpectedly empty snapshot never marks old jobs unlisted.
Feed disappearance never marks jobs unlisted; feeds are rolling windows.

## Expand in this order

1. Grow the employer registry to the companies you care about. Three ATS adapters
   cover many employer websites without a separate scraper for each website.
2. Add SmartRecruiters, Teamtailor, Workable and BambooHR after verifying their
   public contracts and per-source access requirements.
3. Add schema.org `JobPosting` extraction for company sites not covered by an ATS.
4. Add Workday/Oracle/iCIMS company-specific collectors only when needed; their
   tenants vary and deserve fixtures and source-health checks.
5. Add daily scheduling and change notifications once the sources are stable.

LinkedIn, Indeed, Naukri, Wellfound, Glassdoor and salary sites are not automated
in this starter. Use supported interfaces where available; don't couple core
collection to session cookies, proxy rotation, or anti-bot workarounds. Keep
salary-site benchmarks separate from employer-published compensation.

No scheduler, hosted service, automatic company discovery, applications or
outreach is installed. Review each source's current terms before publishing a
public aggregator or reusing its data outside this personal report.


## GitHub data snapshots

This repository includes public snapshots of collected listings and collection
timestamps. Keep credentials, private notes and personal application data out of
tracked snapshots; upstream response caches remain local.
The working `data/` folder and upstream response cache stay ignored. To export
portable data for GitHub after collecting jobs:

```sh
python3 jobs.py collect
python3 snapshot_data.py
# Review what changed before committing.
git add -- snapshots/jobs.sqlite3.gz snapshots/jobs.json.gz snapshots/report.html
git commit -m "Update collected job data and report"
git push
```

`snapshot_data.py` uses a consistent SQLite backup and exports the database and
JSON as gzip files plus a directly readable `snapshots/report.html`. It makes no
network calls. The uncompressed working files are kept locally. Each commit
stores that collection state; this is manual sync, not a scheduled service.

After cloning onto a new machine, restore into a new, empty data directory:

```sh
mkdir data
gzip -dc snapshots/jobs.sqlite3.gz > data/jobs.sqlite3
gzip -dc snapshots/jobs.json.gz > data/jobs.json
python3 jobs.py report
open data/report.html
```

Restore only into a fresh directory; the shell redirections replace existing
files. No credentials or cached upstream responses belong in these snapshots.
