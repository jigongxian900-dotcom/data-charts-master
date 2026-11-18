"""Verify that the authored layouts preserve their business and input boundaries."""
import copy
import json
from pathlib import Path
import re
import unittest

from build_report_layout_samples import layouts
from operating_gap_review import build, reviewed


FIXTURE = Path(__file__).resolve().parents[1] / 'examples' / 'operating-story' / 'input.json'


class OperatingGapReviewTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(FIXTURE.read_text(encoding='utf-8-sig'))
        self.raw['same_store_metric'] = '同店营业额'

    def test_each_format_uses_its_own_proof_and_the_same_original_rows(self):
        reports = build(self.raw)
        self.assertEqual(set(reports), {'brief.html', 'report.html', 'slides.html'})
        for html in reports.values():
            source = re.search(r'id="source-data">(.*?)</script>', html).group(1)
            self.assertEqual(json.loads(source), self.raw)
            self.assertIn('download="target-gap.svg"', html)
            self.assertNotIn('可追回金额', html)
        self.assertIn('53<small>%</small>', reports['brief.html'])
        self.assertIn('79.6%', reports['report.html'])
        self.assertIn('复核老挝、新加坡的同店名单和降幅', reports['report.html'])
        self.assertEqual(reports['slides.html'].count(' data-slide>'), 4)
        self.assertIn('下月改善措施、估算金额与依据', reports['slides.html'])

    def test_majority_language_and_ranking_follow_the_supplied_rows(self):
        source = copy.deepcopy(self.raw)
        next(row for row in source['rows'] if row['id']=='VN')['target'] += 19
        data = reviewed(source)
        self.assertEqual(data['lead']['name'], '印尼')
        self.assertLess(data['share'], 50)
        self.assertIn('印尼占缺口 45%', build(source)['report.html'])

    def test_missing_and_over_target_values_keep_general_reporting_path(self):
        missing = copy.deepcopy(self.raw)
        missing['rows'][0]['revenue'] = None
        self.assertIsNone(build(missing))
        self.assertIn('id="chart-spec"', layouts(missing)['report.html'])
        exceeded = copy.deepcopy(self.raw)
        exceeded['rows'][0]['target'] = 200
        self.assertIsNone(build(exceeded))


if __name__ == '__main__':
    unittest.main()
