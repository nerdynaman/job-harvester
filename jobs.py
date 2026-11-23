#!/usr/bin/env python3
"""Personal, read-only job aggregation from public APIs and RSS. Python 3.10+."""
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit, quote, urljoin
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ATS = {"greenhouse", "lever", "ashby"}
KINDS = ATS | {"hn", "wwr", "remotive", "remoteok", "hn_jobs", "arbeitnow", "jobicy", "yc"}
INCLUDE = re.compile(r"back[ -]?end|distributed systems|\b(api|ai|llm|agentic|database)\b", re.I)
ENGINEER = re.compile(r"\b(engineer|developer|programmer)\b", re.I)
BACKEND = re.compile(r"back[ -]?end|server[ -]side|distributed systems|microservices|\b(grpc|fastapi|spring boot)\b|rest(?:ful)? apis?|llm (applications|agents)|agent (workflows|orchestration)", re.I)
EXCLUDE = re.compile(r"front[ -]?end|full[ -]?stack|\b(ui|ux|ml|sre|devops|staff|principal|lead|manager|director|intern|senior|sr\.?|qa|android|ios|mobile)\b|machine learning|data scien|test engineer|site reliability|platform operations|release engineer|research engineer|sales engineer|solutions engineer", re.I)
YEARS = re.compile(r"\b(\d{1,2})(?:\s*(?:-|–|—|to)\s*(\d{1,2}))?\s*\+?\s*years?(?:\s+of)?\s+(?:(?:relevant|professional|hands-on|industry|commercial|related|software|engineering|development|backend|work|practical)\s+){0,5}experience\b", re.I)
OPEN_EXPERIENCE = re.compile(
    r"\b(?:new|recent|fresh)\s+grad(?:uate)?s?\s+(?:are\s+)?(?:welcome|ok(?:ay)?|accepted|encouraged|eligible|considered)\b"
    r"|\b(?:open to|welcom(?:e|ing))\s+(?:new|recent|fresh)\s+grad(?:uate)?s?\b"
    r"|\b(?:all|any)\s+(?:experience|seniority)\s+levels?\b"
    r"|\bany experience(?=\s*(?:[().,;:]|$|welcome\b|accepted\b|ok\b))"
    r"|\bno\s+(?:(?:prior|previous|professional|work)\s+)*experience\s+(?:is\s+)?(?:required|necessary|needed)\b"
    r"|\bexperience\s+(?:is\s+)?not\s+required\b", re.I)

MONEY = re.compile(r"(?:₹|\bINR\b|\bUSD\b|\bEUR\b|\bGBP\b|\bKRW\b|\$|€|£|₩)\s*\d[\d,.]*(?:\s*[kKmM])?|\b\d+(?:\.\d+)?\s*(?:-|–|to)?\s*\d*(?:\.\d+)?\s*(?:LPA|lakhs?|lacs?)\b", re.I)


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(value):
    parser = PlainText()
    parser.feed(html.unescape(str(value or "")))
    parser.close()
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def safe_url(value):
    url = urlsplit(str(value or ""))
    if url.scheme not in {"http", "https"} or not url.hostname or url.username:
        raise ValueError("Job URL must be an absolute HTTP(S) URL")
    return str(value)


def canonical_url(value):
    url = urlsplit(safe_url(value))
    query = [(k, v) for k, v in parse_qsl(url.query) if not k.lower().startswith("utm_") and k.lower() not in {"source", "ref", "referrer"}]
    return urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path.rstrip("/"), urlencode(sorted(query)), ""))


def validate_sources(sources):
    if not isinstance(sources, list) or not sources:
        raise ValueError("Sources must be a nonempty list")
    names = set()
    for s in sources:
        if not isinstance(s, dict):
            raise ValueError("Each source must be an object")
        if s.get("type") not in KINDS or not re.fullmatch(r"[\w-]+", s.get("name", ""), re.ASCII):
            raise ValueError(f"Invalid source: {s}")
        if s['name'] in names:
            raise ValueError(f"Duplicate source name: {s['name']}")
        names.add(s['name'])
        if s['type'] in ATS and not re.fullmatch(r"[\w.-]+", s.get("board", ""), re.ASCII):
            raise ValueError("ATS source requires a board slug")
        if s['type'] in ATS and not isinstance(s.get('company'), str):
            raise ValueError("ATS source requires a company name")
    return sources


class Fetcher:
    def __init__(self, directory):
        self.cache = Path(directory) / "cache"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.last_request = {}

    def get(self, url, accept="application/json, application/rss+xml, text/xml"):
        cache = self.cache / (hashlib.sha256(url.encode()).hexdigest() + ".bin")
        # shortcut: six-hour URL cache, add conditional requests if fresh feeds become necessary.
        if cache.exists() and time.time() - cache.stat().st_mtime < 21600:
            return cache.read_bytes()
        host = urlsplit(url).netloc
        time.sleep(max(0, 1 - (time.monotonic() - self.last_request.get(host, 0))))
        for attempt in range(2):
            self.last_request[host] = time.monotonic()
            try:
                req = Request(url, headers={"User-Agent": "PersonalJobHarvester/0.1", "Accept": accept})
                with urlopen(req, timeout=30) as response:
                    data = response.read(25_000_001)
                if len(data) > 25_000_000:
                    raise ValueError("Response exceeds 25 MB")
                atomic_write(cache, data)
                return data
            except HTTPError as exc:
                if attempt or exc.code not in {429, 500, 502, 503, 504}:
                    raise
                retry = exc.headers.get("Retry-After", "3")
                try:
                    delay = max(1, float(retry))
                except ValueError:
                    delay = max(1, parsedate_to_datetime(retry).timestamp() - time.time())
                if delay > 30:
                    raise
                time.sleep(delay)

    def json(self, url):
        return json.loads(self.get(url))


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
            temporary = f.name
            f.write(data if isinstance(data, bytes) else data.encode())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def job(source, identifier, company, title, location, description, url, published=None, compensation=None):
    if not identifier or not plain(title):
        raise ValueError("Job has no identifier or title")
    return {"source": source['name'], "source_type": source['type'], "source_id": str(identifier),
            "company": plain(company), "title": plain(title), "location": plain(location),
            "description": plain(description), "url": safe_url(url), "published": published,
            "compensation": compensation or {}, "collected_at": datetime.now(timezone.utc).isoformat()}


def parse_ats(source, data):
    kind = source['type']
    rows = data if kind == "lever" else data['jobs']
    if not isinstance(rows, list):
        raise ValueError("Expected job list")
    result = []
    for row in rows:
        if kind == "greenhouse":
            result.append(job(source, row['id'], source['company'], row['title'], row.get('location', {}).get('name'), row.get('content'), row['absolute_url'], row.get('first_published'), row.get('pay_input_ranges')))
        elif kind == "lever":
            desc = " ".join([row.get('openingPlain') or '', row.get('descriptionPlain') or '', row.get('descriptionBodyPlain') or '', *[str(x.get('text', '')) + ' ' + str(x.get('content', '')) for x in row.get('lists', [])], row.get('additionalPlain') or ''])
            result.append(job(source, row['id'], source['company'], row['text'], row.get('categories', {}).get('location'), desc, row['hostedUrl'], row.get('createdAt'), row.get('salaryRange')))
        elif row.get('isListed', True):
            locations = [row.get('location') or '', *[x.get('location') or '' for x in row.get('secondaryLocations', [])]]
            location = " / ".join(dict.fromkeys(x for x in locations if x))
            if row.get('workplaceType'):
                location += " · " + row['workplaceType']
            result.append(job(source, row.get('id') or row['jobUrl'], source['company'], row['title'], location, row.get('descriptionPlain') or row.get('descriptionHtml'), row['jobUrl'], row.get('publishedAt'), row.get('compensation')))
    return result


class YCPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.props = None

    def handle_starttag(self, tag, attrs):
        value = dict(attrs).get('data-page')
        if value:
            data = json.loads(value)
            if data.get('component') in {'WaasLandingPage', 'WaasJobListingsPage', 'WaasShowJobPage'}:
                self.props = data['props']


def yc_page(fetch, url):
    parser = YCPage()
    parser.feed(fetch.get(url, accept='text/html').decode())
    parser.close()
    if not isinstance(parser.props, dict):
        raise ValueError('YC public job data missing; page format may have changed')
    return parser.props


def yc_job(source, row):
    url = urljoin('https://www.ycombinator.com', row['url'])
    parts = urlsplit(safe_url(url))
    if parts.scheme != 'https' or parts.netloc != 'www.ycombinator.com' or not re.fullmatch(r'/companies/[\w-]+/jobs/[\w-]+', parts.path):
        raise ValueError('Expected a public YC job URL')
    experience = plain(row.get('minExperience'))
    if re.fullmatch(r'\d+\+? years?', experience):
        experience += ' of experience'
    description = '\n'.join([
        'Role: ' + plain(row.get('roleSpecificType')),
        'Minimum experience: ' + experience,
        'Visa: ' + plain(row.get('visa')),
        'Skills: ' + str(row.get('skills') or ''),
        row.get('description') or 'Full description: open original listing.',
    ])
    item = job(source, row['id'], row.get('companyName'), row['title'], row.get('location'),
               description, url, compensation={'text': row.get('salaryRange') or ''})
    item['role_category'] = plain(row.get('roleSpecificType'))
    return item


def collect_source(source, fetch):
    kind = source['type']
    board = quote(source.get('board', ''), safe='')
    if kind == "greenhouse":
        return parse_ats(source, fetch.json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"))
    if kind == "ashby":
        return parse_ats(source, fetch.json(f"https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true"))
    if kind == "lever":
        result = []
        offset = 0
        while True:
            page = fetch.json(f"https://api.lever.co/v0/postings/{board}?mode=json&skip={offset}&limit=100")
            result.extend(parse_ats(source, page))
            if len(page) < 100:
                return result
            offset += 100
            if offset >= 10000:
                raise ValueError("Lever pagination exceeded 10,000 jobs; snapshot incomplete")
    if kind == "remoteok":
        data = fetch.json("https://remoteok.com/api")
        if not isinstance(data, list):
            raise ValueError("Expected Remote OK list")
        return [job(source, x['id'], x.get('company'), x['position'], x.get('location'), x.get('description'), x['url'], x.get('date')) for x in data if 'id' in x]
    if kind == "remotive":
        data = fetch.json("https://remotive.com/api/remote-jobs?category=software-dev")
        return [job(source, x['id'], x.get('company_name'), x['title'], x.get('candidate_required_location'), x.get('description'), x['url'], x.get('publication_date'), {"text": x.get('salary') or ''}) for x in data['jobs']]
    if kind == "wwr":
        root = ET.fromstring(fetch.get("https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss"))
        if root.tag != 'rss' or root.find('channel') is None:
            raise ValueError("Expected WWR RSS channel")
        result = []
        for x in root.findall('./channel/item'):
            title = x.findtext('title') or ''
            company, separator, role = title.partition(': ')
            url = x.findtext('link')
            result.append(job(source, x.findtext('guid') or url, company if separator else '', role if separator else title, x.findtext('region') or '', x.findtext('description'), url, x.findtext('pubDate')))
        return result
    if kind == "yc":
        rows = {}
        # shortcut: public category pages only; signed-in YC search is outside this collector.
        for path in ('/jobs', '/jobs/role/software-engineer', '/jobs/role/software-engineer/india', '/jobs/role/software-engineer/remote'):
            data = yc_page(fetch, 'https://www.ycombinator.com' + path)
            if not isinstance(data.get('jobPostings'), list):
                raise ValueError('Expected YC public job listings')
            for row in data['jobPostings']:
                rows[str(row['id'])] = row
        result = []
        for row in rows.values():
            item = yc_job(source, row)
            if evaluate(item)['role_match'] == 'relevant':
                try:
                    detail = yc_page(fetch, item['url'])['job']
                except HTTPError as exc:
                    if exc.code in {404, 410}:
                        continue
                    raise
                if str(detail['id']) != item['source_id']:
                    raise ValueError('YC job detail ID does not match listing')
                item = yc_job(source, detail)
            result.append(item)
        return result
    if kind == "hn_jobs":
        identifiers = fetch.json("https://hacker-news.firebaseio.com/v0/jobstories.json")
        if not isinstance(identifiers, list) or len(identifiers) > 200:
            raise ValueError("Expected at most 200 current HN job IDs")
        result = []
        for identifier in identifiers:
            if not isinstance(identifier, int) or isinstance(identifier, bool) or identifier <= 0:
                raise ValueError("Invalid HN job ID")
            row = fetch.json(f"https://hacker-news.firebaseio.com/v0/item/{identifier}.json")
            if not row or row.get('deleted') or row.get('dead') or row.get('type') != 'job':
                continue
            result.append(job(source, row['id'], '', row['title'], '', row.get('text'),
                              row.get('url') or f"https://news.ycombinator.com/item?id={row['id']}", row.get('time')))
        return result
    if kind == "arbeitnow":
        # shortcut: latest-results page only; add pagination when a higher request allowance is available.
        data = fetch.json('https://www.arbeitnow.com/api/job-board-api')
        if not isinstance(data.get('data'), list):
            raise ValueError("Expected Arbeitnow job list")
        result = []
        for row in data['data']:
            location = row.get('location') or ''
            if row.get('remote') is True:
                location += ' · Remote'
            result.append(job(source, row['slug'], row.get('company_name'), row['title'], location,
                              row.get('description'), row['url'], row.get('created_at')))
        return result
    if kind == "jobicy":
        result, cursors = [], set()
        cursor = None
        for _ in range(20):
            params = {'count': 100, 'industry': 'engineering'}
            if cursor:
                params['cursor'] = cursor
            data = fetch.json('https://jobicy.com/api/jobs?' + urlencode(params))
            if data.get('success') is False or not isinstance(data.get('jobs'), list):
                raise ValueError("Expected Jobicy job list")
            for row in data['jobs']:
                compensation = {'currency': row.get('salaryCurrency'), 'min': row.get('salaryMin'),
                                'max': row.get('salaryMax'), 'interval': row.get('salaryPeriod')}
                result.append(job(source, row['id'], row.get('companyName'), row['jobTitle'],
                                  (row.get('jobGeo') or '') + ' · Remote', row.get('jobDescription'),
                                  row['url'], row.get('pubDate'), compensation))
            cursor = data.get('nextCursor')
            if not cursor:
                if data.get('hasMore'):
                    raise ValueError("Jobicy has more results without a cursor")
                return result
            if not isinstance(cursor, str) or cursor in cursors:
                raise ValueError("Invalid or repeated Jobicy cursor")
            cursors.add(cursor)
        raise ValueError("Jobicy exceeds 20 pages; collection incomplete")
    stories = fetch.json("https://hn.algolia.com/api/v1/search_by_date?" + urlencode({'tags': 'story,author_whoishiring', 'query': 'Who is hiring', 'hitsPerPage': 10}))['hits']
    stories = [x for x in stories if re.match(r'^Ask HN: Who is hiring\?', x.get('title') or '', re.I)]
    if not stories:
        raise ValueError("No Who is hiring thread found")
    story = stories[0]
    thread = story['objectID']
    result = []
    page = 0
    while True:
        data = fetch.json("https://hn.algolia.com/api/v1/search?" + urlencode({'tags': f'comment,story_{thread}', 'hitsPerPage': 100, 'page': page}))
        for x in data['hits']:
            if str(x.get('parent_id')) != str(thread) or not x.get('comment_text'):
                continue
            description = plain(x['comment_text'])
            header = description[:300].split('|')
            result.append(job(source, x['objectID'], header[0], ' | '.join(header[1:]) if len(header) > 1 else 'Hiring post', '', description, f"https://news.ycombinator.com/item?id={x['objectID']}", x.get('created_at')))
        page += 1
        if page >= data['nbPages']:
            return result
        if page >= 10:
            raise ValueError("HN search exceeds 1,000 comments; snapshot incomplete")


def evaluate(item, years=2):
    title, desc = item['title'], item['description']
    mixed = item['source_type'] in {'hn', 'hn_jobs'}
    if mixed:
        role = 'review' if BACKEND.search(f'{title} {desc}') else 'unrelated'
    elif EXCLUDE.search(title) or (item['source_type'] == 'yc' and EXCLUDE.search(item.get('role_category', ''))):
        role = 'excluded'
    elif ENGINEER.search(title) and (INCLUDE.search(title) or BACKEND.search(desc)):
        role = 'relevant'
    else:
        role = 'unrelated'
    evidence = []
    for match in YEARS.finditer(desc):
        evidence.append({'minimum': int(match[1]), 'maximum': int(match[2]) if match[2] else None, 'text': desc[max(0, match.start()-55):match.end()+100]})
    # shortcut: regex evidence is a screening hint, not a determination of applicant eligibility.
    minimum = min((x['minimum'] for x in evidence), default=None)
    open_evidence = []
    for match in OPEN_EXPERIENCE.finditer(desc):
        prefix = desc[max(0, match.start()-45):match.start()]
        if not re.search(r"\b(?:not|never|no|cannot|can't|don't|aren't)\b[^.;:!?]{0,35}$", prefix, re.I):
            open_evidence.append(desc[max(0, match.start()-35):match.end()+70])
    # Numeric requirements take precedence when an otherwise welcoming post asks for more experience.
    experience = ('possible' if minimum <= years else 'above_target') if minimum is not None else ('open' if open_evidence else 'unknown')
    snippets = list(dict.fromkeys(desc[max(0, m.start()-45):m.end()+100] for m in MONEY.finditer(desc)))[:8]
    comp = item['compensation']
    structured = any(comp.values()) if isinstance(comp, dict) else bool(comp)
    return {'role_match': role, 'experience': experience, 'experience_evidence': evidence, 'open_experience_evidence': open_evidence,
            'salary_evidence': snippets, 'salary_status': 'compensation_review' if structured else ('money_mentions_review' if snippets else 'unknown'),
            'location_status': 'review country/work-rights restrictions; remote does not imply worldwide'}


def database(path):
    conn = sqlite3.connect(path)
    conn.execute('CREATE TABLE IF NOT EXISTS jobs (source TEXT, source_id TEXT, payload TEXT NOT NULL, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, listed INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(source, source_id))')
    conn.execute('CREATE TABLE IF NOT EXISTS health (source TEXT PRIMARY KEY, checked TEXT, status TEXT, detail TEXT)')
    return conn


def save_source(conn, source, items):
    now = datetime.now(timezone.utc).isoformat()
    if not items and conn.execute('SELECT 1 FROM jobs WHERE source=? AND listed=1 LIMIT 1', (source['name'],)).fetchone():
        raise ValueError('Empty snapshot after prior listings; refusing to mark jobs unlisted')
    with conn:
        if source['type'] in ATS:
            conn.execute('UPDATE jobs SET listed=0 WHERE source=?', (source['name'],))
        for item in items:
            conn.execute('INSERT INTO jobs VALUES (?,?,?,?,?,1) ON CONFLICT(source,source_id) DO UPDATE SET payload=excluded.payload,last_seen=excluded.last_seen,listed=1', (item['source'], item['source_id'], json.dumps(item), now, now))
        conn.execute('INSERT OR REPLACE INTO health VALUES (?,?,?,?)', (source['name'], now, 'ok', f'{len(items)} listings; responses may be cached for six hours'))


def compensation_summary(compensation):
    if not isinstance(compensation, dict):
        return ''
    for key in ('compensationTierSummary', 'scrapeableCompensationSalarySummary', 'text'):
        if compensation.get(key):
            return str(compensation[key])
    components = compensation.get('summaryComponents') or [compensation]
    amounts = []
    for component in components:
        low = component.get('minValue', component.get('min'))
        high = component.get('maxValue', component.get('max'))
        if low is None and high is None:
            continue
        currency = component.get('currencyCode') or component.get('currency') or ''
        period = component.get('interval') or ''
        value = f'{low:,}–{high:,}' if isinstance(low, (int, float)) and isinstance(high, (int, float)) else str(low if low is not None else high)
        amounts.append(' '.join(str(part) for part in (currency, value, period) if part))
    return ' · '.join(amounts)


def report(conn, directory, years=2):
    output = []
    for payload, first, last, listed in conn.execute('SELECT payload,first_seen,last_seen,listed FROM jobs ORDER BY first_seen DESC'):
        item = json.loads(payload)
        item.update(first_seen=first, last_seen=last, listed=bool(listed))
        item.update(evaluate(item, years))
        item['canonical_url'] = canonical_url(item['url'])
        output.append(item)
    health = [dict(zip(('source', 'checked', 'status', 'detail'), row)) for row in conn.execute('SELECT * FROM health ORDER BY source')]
    atomic_write(Path(directory) / 'jobs.json', json.dumps({'generated_at': datetime.now(timezone.utc).isoformat(), 'target_years': years, 'sources': health, 'jobs': output}, ensure_ascii=False, indent=2))
    cards, seen = [], set()
    for item in output:
        if not item['listed'] or item['role_match'] in {'excluded', 'unrelated'}:
            continue
        key = item['canonical_url']
        if key in seen:
            continue
        seen.add(key)
        esc = lambda value: html.escape(str(value), quote=True)
        compensation = item['compensation']
        structured = compensation_summary(compensation)
        salary = structured or ' | '.join(item['salary_evidence']) or 'Pay not disclosed; no estimate made'
        experience = ' | '.join([*[x['text'] for x in item['experience_evidence']], *item['open_experience_evidence']]) or 'Experience requirement not identified'
        attribution = {'remoteok': 'Remote OK', 'remotive': 'Remotive', 'wwr': 'We Work Remotely', 'hn': 'HN · Who is hiring?', 'hn_jobs': 'HN · Jobs', 'arbeitnow': 'Arbeitnow', 'jobicy': 'Jobicy', 'yc': 'Y Combinator'}.get(item['source_type'], item['source'])
        location = item['location'] or 'Location not specified'
        # shortcut: work mode uses location/feed hints; verify eligibility on the listing.
        mode = ('hybrid' if re.search(r'\bhybrid\b', location, re.I) else
                'remote' if re.search(r'\bremote\b', location, re.I) or item['source_type'] in {'remoteok', 'remotive', 'wwr'} else
                'onsite' if re.search(r'on[ -]?site|in[ -]office', location, re.I) else 'unknown')
        experience_label = {'possible': f'Minimum ≤ {years} years', 'open': 'Open experience / new grads welcome', 'unknown': 'Experience unclear', 'above_target': f'Above {years}y target'}[item['experience']]
        pay_label = {'compensation_review': 'Compensation supplied', 'money_mentions_review': 'Money mention · verify', 'unknown': 'Pay undisclosed'}[item['salary_status']]
        if structured:
            pay_label = structured
        elif item['salary_evidence']:
            # Keep unstructured amounts explicitly unverified: money can refer to funding.
            snippet = next((text for text in item['salary_evidence'] if re.search(r'salary|compensation|\bpay\b|LPA', text, re.I)), item['salary_evidence'][0])
            pay_label = 'Money mention · verify: ' + snippet
        attrs = {'company': item['company'], 'source': attribution, 'experience': item['experience'], 'mode': mode, 'pay': item['salary_status'], 'location': location}
        attributes = ' '.join(f'data-{key}="{esc(value)}"' for key, value in attrs.items())
        cards.append(f'''<article {attributes}><div class="job-heading"><div><p class="company">{esc(item['company'])}</p><h2><a href="{esc(item['url'])}" target="_blank" rel="noopener noreferrer">{esc(item['title'])}</a></h2></div><span class="source">{esc(attribution)}</span></div><p class="location" title="{esc(location)}">{esc(location)}</p><div class="tags"><span class="tag {esc(item['experience'])}">{esc(experience_label)}</span><span class="tag compensation" title="{esc(pay_label)}">{esc(pay_label)}</span></div><details><summary>View details</summary><div class="detail-content"><h3>Experience evidence</h3><p>{esc(experience)}</p><h3>Compensation evidence</h3><p>{esc(salary)}</p><h3>Full description</h3><p>{esc(item['description'])}</p><p class="muted">First seen: {esc(item['first_seen'])}<br>Last collected (may be cached): {esc(item['last_seen'])}<br>Published: {esc(item['published'])}</p><a href="{esc(item['url'])}" target="_blank" rel="noopener noreferrer">Open original listing ↗</a></div></details></article>''')
    warnings = ''.join(f"<li>{html.escape(x['source'])}: {html.escape(x['status'])} — {html.escape(x['detail'])}</li>" for x in health)
    page = Path(__file__).with_name('report_template.html').read_text()
    replacements = {'TARGET': str(years), 'ERRORS': str(sum(x['status'] == 'error' for x in health)),
                    'HEALTH': warnings, 'CARDS': '\n'.join(cards)}
    page = re.sub(r'@@(TARGET|ERRORS|HEALTH|CARDS)@@', lambda match: replacements[match[1]], page)
    atomic_write(Path(directory) / 'report.html', page)
    return len(output), len(cards)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['collect', 'report'])
    parser.add_argument('--sources', type=Path, default=Path(__file__).with_name('sources.json'))
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('data'))
    parser.add_argument('--source', action='append', help='Configured source name; repeat to select several')
    parser.add_argument('--years', type=int, default=2)
    args = parser.parse_args()
    if not 0 <= args.years <= 50:
        parser.error('--years must be between 0 and 50')
    sources = validate_sources(json.loads(args.sources.read_text()))
    if args.source:
        unknown = set(args.source) - {x['name'] for x in sources}
        if unknown:
            parser.error(f'Unknown source names: {sorted(unknown)}')
        sources = [x for x in sources if x['name'] in args.source]
    args.output.mkdir(parents=True, exist_ok=True)
    conn = database(args.output / 'jobs.sqlite3')
    errors = 0
    try:
        if args.command == 'collect':
            fetch = Fetcher(args.output)
            for source in sources:
                try:
                    items = collect_source(source, fetch)
                    save_source(conn, source, items)
                    print(f"{source['name']}: {len(items)} listings")
                except (HTTPError, OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
                    errors += 1
                    detail = f'{type(exc).__name__}: {exc}'
                    with conn:
                        conn.execute('INSERT OR REPLACE INTO health VALUES (?,?,?,?)', (source['name'], datetime.now(timezone.utc).isoformat(), 'error', detail))
                    print(f"{source['name']}: {detail}; previous jobs preserved", file=sys.stderr)
        total, candidates = report(conn, args.output, args.years)
        print(f'{total} stored jobs; {candidates} role candidates before experience filtering. Report: {args.output / "report.html"}')
    finally:
        conn.close()
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
