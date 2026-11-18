"""Regression checks for same-data material choices."""
import unittest
from xml.etree import ElementTree as ET

from build_chart_shape_gallery import build, sample_spec
from chart_html import svg_chart
from chart_shapes import STYLES


class ChartShapeTests(unittest.TestCase):
    def test_three_geometry_choices_preserve_data_in_every_family(self):
        for chart in sample_spec()['charts']:
            for mode in ('desktop', 'mobile', 'compact'):
                options = dict(mobile=mode == 'mobile', compact=mode == 'compact')
                baseline, ledger = svg_chart(chart, **options)
                forms = []
                for key, _, _ in STYLES[chart['kind']]:
                    rendered, result = svg_chart(dict(chart, shape=key), **options)
                    self.assertEqual(result, ledger)
                    self.assertEqual(ET.fromstring(rendered).get('viewBox'), ET.fromstring(baseline).get('viewBox'))
                    forms.append(rendered)
                if mode != 'compact' or chart['kind'] != 'line':
                    self.assertEqual(len(set(forms)), 3, (chart['id'], mode))

    def test_gallery_title_and_exports(self):
        html = build(sample_spec())
        self.assertNotIn('@@TITLE@@', html)
        self.assertIn('<h1>图形样式库</h1>', html)
        self.assertEqual(html.count('>下载 SVG</a>'), 21)


if __name__ == '__main__':
    unittest.main()
