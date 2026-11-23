import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import jobs


def sample(identifier='1', title='Backend Engineer', description='2–3 years of professional software development experience'):
    return jobs.job({'name': 'test', 'type': 'greenhouse'}, identifier, 'Example', title, 'India', description, f'https://example.com/jobs/{identifier}')


class JobTests(unittest.TestCase):
    def test_filters_use_role_title_and_retain_uncertainty(self):
        for title in ['Frontend Engineer', 'Machine Learning Engineer', 'DevOps Engineer', 'Senior Backend Engineer', 'Full Stack Engineer', 'Software Engineer Android']:
            self.assertEqual(jobs.evaluate(sample(title=title))['role_match'], 'excluded')
        self.assertEqual(jobs.evaluate(sample(description='Work with frontend and ML teams.'))['role_match'], 'relevant')
        self.assertEqual(jobs.evaluate(sample())['experience'], 'possible')
        self.assertEqual(jobs.evaluate(sample(description='3+ years of professional experience'))['experience'], 'above_target')
        self.assertEqual(jobs.evaluate(sample(description='Strong Python skills'))['experience'], 'unknown')
        self.assertEqual(jobs.evaluate(sample(title='Strategic Account Executive - AI'))['role_match'], 'unrelated')
        self.assertEqual(jobs.evaluate(sample(title='Software Engineer', description='Build distributed systems'))['role_match'], 'relevant')
        self.assertEqual(jobs.evaluate(sample(description='1–2 years of experience'), years=1)['experience'], 'possible')
        self.assertEqual(jobs.evaluate(sample(description='1–2 years of experience'), years=0)['experience'], 'above_target')

    def test_open_experience_detects_welcoming_phrases_without_overriding_minimums(self):
        for text in ['Minimum experience: Any (new grads ok)', 'New graduates welcome.',
                     'Any experience.', 'All experience levels welcome.', 'Open to recent graduates.',
                     'No prior work experience required.', 'Experience is not required.']:
            with self.subTest(text=text):
                result = jobs.evaluate(sample(description=text))
                self.assertEqual(result['experience'], 'open')
                self.assertTrue(result['open_experience_evidence'])
        for text in ['We are not open to new grads.', 'New grads are not welcome.',
                     'Any experience with Python is useful.', 'We mentor new graduates on the team.']:
            with self.subTest(text=text):
                self.assertEqual(jobs.evaluate(sample(description=text))['experience'], 'unknown')
        self.assertEqual(jobs.evaluate(sample(description='New grads welcome. 5+ years of professional experience required.'))['experience'], 'above_target')
        self.assertEqual(jobs.evaluate(sample(description='All experience levels welcome. 2 years of experience required.'))['experience'], 'possible')

    def test_salary_mentions_are_not_a_salary_verdict(self):
        self.assertEqual(jobs.evaluate(sample())['salary_status'], 'unknown')
        self.assertEqual(jobs.evaluate(sample(description='We raised $20 million.'))['salary_status'], 'money_mentions_review')
        self.assertEqual(jobs.evaluate(sample(description='Salary ₹20–30 LPA'))['salary_status'], 'money_mentions_review')

    def test_greenhouse_and_safe_urls(self):
        self.assertEqual(jobs.plain('Director, FP&A'), 'Director, FP&A')
        source = {'name': 'gh', 'type': 'greenhouse', 'company': 'Employer'}
        result = jobs.parse_ats(source, {'jobs': [{'id': 3, 'title': 'Backend', 'content': '&lt;p&gt;Go &amp; Python&lt;/p&gt;', 'absolute_url': 'https://example.com/3'}]})
        self.assertEqual(result[0]['description'], 'Go & Python')
        with self.assertRaises(ValueError):
            jobs.safe_url('javascript:alert(1)')
        a = jobs.canonical_url('https://example.com/jobs/?gh_jid=1&utm_source=a#apply')
        b = jobs.canonical_url('https://example.com/jobs/?gh_jid=2&utm_source=a')
        self.assertNotEqual(a, b)
        self.assertEqual(a, 'https://example.com/jobs?gh_jid=1')

    def test_ashby_omits_unlisted_and_uses_workplace_type(self):
        source = {'name': 'ash', 'type': 'ashby', 'company': 'Employer'}
        row = {'id': 'a', 'title': 'AI Engineer', 'jobUrl': 'https://example.com/a', 'isRemote': True, 'workplaceType': 'Hybrid', 'location': 'India', 'descriptionPlain': 'Python', 'compensation': {'summaryComponents': [{'currencyCode': 'USD', 'minValue': 20000}]}}
        result = jobs.parse_ats(source, {'jobs': [row, dict(row, id='b', isListed=False)]})
        self.assertEqual(len(result), 1)
        self.assertIn('Hybrid', result[0]['location'])
        self.assertNotIn('Remote', result[0]['location'])
        self.assertEqual(result[0]['compensation'], row['compensation'])

    def test_lever_pagination_and_requirement_lists(self):
        fetch = Mock()
        row = {'id': '1', 'text': 'Backend', 'hostedUrl': 'https://example.com/1', 'descriptionPlain': 'Go', 'lists': [{'text': 'Requirements', 'content': '<li>2 years of experience</li>'}]}
        fetch.json.side_effect = [[dict(row, id=str(i)) for i in range(100)], [dict(row, id='100')]]
        result = jobs.collect_source({'name': 'lever', 'type': 'lever', 'board': 'example', 'company': 'Example'}, fetch)
        self.assertEqual(len(result), 101)
        self.assertIn('2 years of experience', result[0]['description'])
        self.assertEqual(parse_qs(urlsplit(fetch.json.call_args.args[0]).query)['skip'], ['100'])

    def test_feed_parsers_preserve_attribution(self):
        fetch = Mock()
        fetch.json.return_value = [{'legal': 'attribute'}, {'id': 1, 'position': 'Backend', 'url': 'https://remoteok.com/1'}]
        self.assertEqual(len(jobs.collect_source({'name': 'remoteok', 'type': 'remoteok'}, fetch)), 1)
        fetch.json.return_value = {'jobs': [{'id': 2, 'title': 'Backend', 'url': 'https://remotive.com/2', 'salary': '$50k'}]}
        result = jobs.collect_source({'name': 'remotive', 'type': 'remotive'}, fetch)
        self.assertEqual(result[0]['compensation']['text'], '$50k')
        fetch.get.return_value = b'<rss><channel><item><title>ACME: Backend</title><link>https://weworkremotely.com/3</link><description>Python</description></item></channel></rss>'
        result = jobs.collect_source({'name': 'wwr', 'type': 'wwr'}, fetch)
        self.assertEqual((result[0]['company'], result[0]['title']), ('ACME', 'Backend'))
        with self.assertRaises(ValueError):
            fetch.get.return_value = b'<html>Blocked</html>'
            jobs.collect_source({'name': 'wwr', 'type': 'wwr'}, fetch)

    def test_hn_only_keeps_top_level_posts_and_marks_for_review(self):
        fetch = Mock()
        fetch.json.side_effect = [
            {'hits': [{'title': 'Ask HN: Who is hiring? (November 2026)', 'objectID': '10'}]},
            {'nbPages': 1, 'hits': [
                {'objectID': '20', 'parent_id': 10, 'comment_text': 'ACME | Backend engineer | REMOTE'},
                {'objectID': '21', 'parent_id': 20, 'comment_text': 'Is this role open?'}]}]
        result = jobs.collect_source({'name': 'hn', 'type': 'hn'}, fetch)
        self.assertEqual(len(result), 1)
        self.assertEqual(jobs.evaluate(result[0])['role_match'], 'review')
        self.assertEqual(result[0]['url'], 'https://news.ycombinator.com/item?id=20')

    def test_hn_jobs_uses_official_feed_and_skips_removed_items(self):
        fetch = Mock()
        fetch.json.side_effect = [[1, 2, 3, 4, 5],
            {'id': 1, 'type': 'job', 'title': 'Backend engineer', 'url': 'https://example.com/jobs/1'},
            {'id': 2, 'type': 'job', 'title': 'Database engineer', 'text': 'Build distributed systems'},
            {'id': 3, 'deleted': True}, {'id': 4, 'dead': True}, None]
        result = jobs.collect_source({'name': 'hackernews-jobs', 'type': 'hn_jobs'}, fetch)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['url'], 'https://example.com/jobs/1')
        self.assertEqual(result[1]['url'], 'https://news.ycombinator.com/item?id=2')
        self.assertEqual(jobs.evaluate(result[0])['role_match'], 'review')
        self.assertEqual(fetch.json.call_args_list[0].args[0], 'https://hacker-news.firebaseio.com/v0/jobstories.json')
        fetch.json.side_effect = [['../invalid']]
        with self.assertRaises(ValueError):
            jobs.collect_source({'name': 'hackernews-jobs', 'type': 'hn_jobs'}, fetch)

    def test_arbeitnow_latest_page_keeps_remote_and_does_not_follow_next_url(self):
        fetch = Mock()
        row = {'slug': 'backend', 'company_name': 'Example', 'title': 'Backend engineer',
               'remote': True, 'location': 'Germany', 'url': 'https://www.arbeitnow.com/jobs/backend'}
        fetch.json.side_effect = [
            {'data': [row], 'links': {'next': 'https://untrusted.example/page=2'}},
            {'data': [], 'links': {'next': None}}]
        result = jobs.collect_source({'name': 'arbeitnow', 'type': 'arbeitnow'}, fetch)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['location'], 'Germany · Remote')
        fetch.json.assert_called_once_with('https://www.arbeitnow.com/api/job-board-api')

    def test_jobicy_paginates_preserves_compensation_and_rejects_loops(self):
        fetch = Mock()
        row = {'id': 1, 'companyName': 'Example', 'jobTitle': 'Backend engineer', 'jobGeo': 'India',
               'url': 'https://jobicy.com/jobs/1', 'salaryMin': 2000000, 'salaryMax': 3000000,
               'salaryCurrency': 'INR', 'salaryPeriod': 'yearly', 'jobDescription': '2 years of experience'}
        fetch.json.side_effect = [
            {'jobs': [row], 'nextCursor': 'opaque&token', 'hasMore': True},
            {'jobs': [dict(row, id=2)], 'nextCursor': None, 'hasMore': False}]
        result = jobs.collect_source({'name': 'jobicy', 'type': 'jobicy'}, fetch)
        self.assertEqual(len(result), 2)
        self.assertIn('Remote', result[0]['location'])
        self.assertEqual(jobs.compensation_summary(result[0]['compensation']), 'INR 2,000,000–3,000,000 yearly')
        self.assertEqual(parse_qs(urlsplit(fetch.json.call_args.args[0]).query)['cursor'], ['opaque&token'])
        fetch.json.side_effect = None
        fetch.json.return_value = {'jobs': [], 'nextCursor': 'same', 'hasMore': True}
        with self.assertRaisesRegex(ValueError, 'repeated'):
            jobs.collect_source({'name': 'jobicy', 'type': 'jobicy'}, fetch)
        fetch.json.return_value = {'success': False, 'jobs': []}
        with self.assertRaises(ValueError):
            jobs.collect_source({'name': 'jobicy', 'type': 'jobicy'}, fetch)

    def test_yc_public_pages_deduplicate_and_enrich_job_details(self):
        import html
        def page(component, props):
            data = html.escape(json.dumps({'component': component, 'props': props}), quote=True)
            return f'<div data-page="{data}"></div>'.encode()
        row = {'id': 42, 'title': 'Software Engineer', 'companyName': 'Example',
               'url': '/companies/example/jobs/abc-backend-engineer', 'location': 'India / Remote (IN)',
               'roleSpecificType': 'Backend', 'minExperience': '1+ years', 'salaryRange': '₹20–30 LPA',
               'visa': 'US citizenship/visa not required'}
        fetch = Mock()
        fetch.get.side_effect = [page('WaasJobListingsPage', {'jobPostings': [row]})] * 4 + [
            page('WaasShowJobPage', {'job': dict(row, description='Build distributed systems with Python.')})]
        source = {'name': 'ycombinator', 'type': 'yc'}
        result = jobs.collect_source(source, fetch)
        self.assertEqual(len(result), 1)
        self.assertEqual(fetch.get.call_count, 5)
        self.assertEqual(fetch.get.call_args.kwargs, {'accept': 'text/html'})
        self.assertIn('Build distributed systems', result[0]['description'])
        self.assertEqual(result[0]['compensation']['text'], '₹20–30 LPA')
        self.assertEqual(jobs.evaluate(result[0])['experience'], 'possible')
        self.assertEqual(jobs.evaluate(jobs.yc_job(source, dict(row, roleSpecificType='Machine learning')))['role_match'], 'excluded')
        with self.assertRaises(ValueError):
            jobs.yc_job(source, dict(row, url='https://untrusted.example/companies/a/jobs/b'))
        fetch.get.side_effect = None
        fetch.get.return_value = b'<html>Sign in</html>'
        with self.assertRaisesRegex(ValueError, 'data missing'):
            jobs.collect_source(source, fetch)

    def test_snapshot_updates_are_idempotent_and_transactional(self):
        conn = jobs.database(':memory:')
        source = {'name': 'test', 'type': 'greenhouse'}
        jobs.save_source(conn, source, [sample(), sample('2')])
        jobs.save_source(conn, source, [sample()])
        self.assertEqual(conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0], 2)
        self.assertEqual(conn.execute('SELECT COUNT(*) FROM jobs WHERE listed=1').fetchone()[0], 1)
        with self.assertRaises(ValueError):
            jobs.save_source(conn, source, [])
        with self.assertRaises(KeyError):
            jobs.save_source(conn, source, [sample('3'), {}])
        self.assertEqual(conn.execute('SELECT COUNT(*) FROM jobs WHERE listed=1').fetchone()[0], 1)
        self.assertEqual(conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0], 2)
        conn.close()

    def test_feeds_do_not_mark_old_jobs_closed(self):
        conn = jobs.database(':memory:')
        jobs.save_source(conn, {'name': 'test', 'type': 'remoteok'}, [sample(), sample('2')])
        jobs.save_source(conn, {'name': 'test', 'type': 'remoteok'}, [sample()])
        self.assertEqual(conn.execute('SELECT COUNT(*) FROM jobs WHERE listed=1').fetchone()[0], 2)
        conn.close()

    def test_report_escapes_untrusted_content_and_deduplicates_urls(self):
        conn = jobs.database(':memory:')
        item = sample(title='Backend Engineer <img src=x onerror=alert(1)>')
        item['description'] = '<script>alert(1)</script> HEALTH CARDS'
        duplicate = dict(item, source_id='2')
        jobs.save_source(conn, {'name': 'test', 'type': 'greenhouse'}, [item, duplicate])
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(jobs.report(conn, directory), (2, 1))
            page = (Path(directory) / 'report.html').read_text()
            self.assertNotIn('<script>alert(1)</script>', page)
            self.assertIn('&lt;script&gt;', page)
            self.assertIn('HEALTH CARDS', page)
            self.assertEqual(len(json.loads((Path(directory) / 'jobs.json').read_text())['jobs']), 2)
        conn.close()

    def test_report_shows_compensation_before_expanding_details(self):
        cases = [
            ({'text': '$120k–$150k / year'}, '', '$120k–$150k / year'),
            ({'compensationTierSummary': '₹20–30 LPA'}, '', '₹20–30 LPA'),
            ({'currency': 'USD', 'min': 100000, 'max': 140000, 'interval': 'per-year'}, '', 'USD 100,000–140,000 per-year'),
            ({'summaryComponents': [{'currencyCode': 'USD', 'minValue': 80000, 'maxValue': 120000, 'interval': '1 YEAR'}]}, '', 'USD 80,000–120,000 1 YEAR'),
            ({}, 'Salary ₹20–30 LPA plus benefits.', '₹20–30 LPA'),
            ({}, 'We raised $20 million.', 'Money mention · verify:'),
            ({'text': ''}, 'Strong Python skills.', 'Pay undisclosed'),
            ({'text': '<img src=x onerror=alert(1)> $100k'}, '', '&lt;img'),
        ]
        for compensation, description, expected in cases:
            with self.subTest(compensation=compensation, description=description):
                conn = jobs.database(':memory:')
                item = sample(description=description)
                item['compensation'] = compensation
                jobs.save_source(conn, {'name': 'test', 'type': 'greenhouse'}, [item])
                with tempfile.TemporaryDirectory() as directory:
                    jobs.report(conn, directory)
                    page = (Path(directory) / 'report.html').read_text()
                    card_header = page.split('<article ', 1)[1].split('<details>', 1)[0]
                    self.assertIn(expected, card_header)
                    self.assertNotIn('<img', card_header)
                conn.close()

    def test_report_filter_metadata_and_hybrid_precedence(self):
        conn = jobs.database(':memory:')
        item = sample()
        item.update(company='Example "quoted"', location='Remote / hybrid', source_type='ashby')
        jobs.save_source(conn, {'name': 'test', 'type': 'ashby'}, [item])
        with tempfile.TemporaryDirectory() as directory:
            jobs.report(conn, directory)
            page = (Path(directory) / 'report.html').read_text()
            self.assertIn('data-company="Example &quot;quoted&quot;"', page)
            self.assertIn('data-mode="hybrid"', page)
            self.assertIn('data-location="Remote / hybrid"', page)
            self.assertIn('data-pay="unknown"', page)
            self.assertIn('data-experience="possible"', page)
            self.assertNotIn('@@CARDS@@', page)
        conn.close()

    def test_retry_is_bounded_and_success_is_cached(self):
        with tempfile.TemporaryDirectory() as directory:
            response = Mock()
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            response.read.return_value = b'{"ok":true}'
            error = HTTPError('https://example.com', 429, 'limited', {'Retry-After': '1'}, None)
            with patch('jobs.urlopen', side_effect=[error, response]) as opener, patch('jobs.time.sleep'):
                fetch = jobs.Fetcher(directory)
                self.assertEqual(fetch.json('https://example.com'), {'ok': True})
                self.assertEqual(fetch.json('https://example.com'), {'ok': True})
                self.assertEqual(opener.call_count, 2)

    def test_config_rejects_path_injection_and_duplicate_names(self):
        s = {'name': 'a', 'type': 'ashby', 'company': 'A', 'board': '../admin'}
        with self.assertRaises(ValueError):
            jobs.validate_sources([s])
        with self.assertRaises(ValueError):
            jobs.validate_sources([{'name': 'a', 'type': 'hn'}] * 2)


if __name__ == '__main__':
    unittest.main()
