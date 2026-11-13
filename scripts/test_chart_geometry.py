"""Mathematical and coverage checks for composable geometry primitives."""
import copy
import math
import unittest

from chart_geometry import area_radius, annular_sector, band_scale, hierarchy_partition, linear_scale, polar_point


class GeometryTests(unittest.TestCase):
    def test_linear_reversed_clamped_null_and_degenerate_domain(self):
        self.assertEqual(linear_scale(25, (0, 100), (200, 0)), 150)
        self.assertEqual(linear_scale(150, (0, 100), (0, 20), clamp=True), 20)
        self.assertEqual(linear_scale(150, (0, 100), (0, 20)), 30)
        self.assertIsNone(linear_scale(None, (0, 1)))
        with self.assertRaises(ValueError):
            linear_scale(1, (1, 1))
        for value in [float('nan'), float('inf'), True]:
            with self.assertRaises(ValueError):
                linear_scale(value, (0, 1))

    def test_band_scale_conserves_steps_with_explicit_spacing_and_order(self):
        bands = band_scale(['B', 'A'], (0, 100), padding=.2)
        self.assertEqual(list(bands), ['B', 'A'])
        self.assertEqual(bands['B'], {'start': 5, 'end': 45, 'center': 25, 'width': 40})
        self.assertAlmostEqual(bands['A']['start']-bands['B']['end'], 10)
        self.assertEqual(band_scale(['A'], (100, 0))['A']['width'], 100)
        self.assertEqual(band_scale([], (0, 100)), {})
        with self.assertRaises(ValueError):
            band_scale(['A', 'A'])

    def test_polar_start_rotation_and_signed_angles(self):
        x, y = polar_point(10, 20, 5, -math.pi/2)
        self.assertAlmostEqual(x, 10)
        self.assertAlmostEqual(y, 15)
        x, y = polar_point(10, 20, 5, math.pi)
        self.assertAlmostEqual(x, 5)
        self.assertAlmostEqual(y, 20)

    def test_area_radius_is_square_root_with_inner_radius_and_missing_rule(self):
        for inner in [0, 4]:
            for value in [0, 1, 25, 100]:
                radius = area_radius(value, 100, 10, inner_radius=inner)
                self.assertAlmostEqual((radius*radius-inner*inner)/(100-inner*inner), value/100)
        self.assertEqual(area_radius(0, 100, 10, inner_radius=4), 4)
        self.assertIsNone(area_radius(None, 100, 10))
        for value in [-1, 101, float('inf')]:
            with self.assertRaises(ValueError):
                area_radius(value, 100, 10)
        with self.assertRaises(ValueError):
            area_radius(0, 0, 10)

    def test_equal_angle_fan_areas_track_values_not_radii(self):
        # A half-circle split into three equal angles, rotated to face upward.
        values = [4, 16, 36]
        sectors = [annular_sector(0, 0, 2, area_radius(v, 36, 10, inner_radius=2),
                                  -math.pi+i*math.pi/3, math.pi/3)
                   for i, v in enumerate(values)]
        for sector, value in zip(sectors, values):
            self.assertAlmostEqual(sector['area']/sectors[-1]['area'], value/36)
        self.assertAlmostEqual(sectors[0]['outer_start'][1], 0)
        self.assertLess(sectors[1]['outer_start'][1], 0)

    def test_sector_arc_direction_and_full_annulus_are_mathematically_correct(self):
        for span in [math.pi/2, -math.pi, math.tau, -math.tau]:
            sector = annular_sector(3, 5, 2, 7, .3, span)
            self.assertAlmostEqual(sector['area'], abs(span)/2*(49-4))
            end = polar_point(3, 5, 7, .3+span)
            self.assertAlmostEqual(sector['outer_end'][0], end[0])
            self.assertAlmostEqual(sector['outer_end'][1], end[1])
            self.assertEqual(sector['path'].count(' A'), 4 if abs(span) > math.pi else 2)
        self.assertEqual(annular_sector(0, 0, 0, 4, 0, 0)['area'], 0)
        self.assertEqual(annular_sector(0, 0, 4, 4, 0, math.pi)['area'], 0)
        with self.assertRaises(ValueError):
            annular_sector(0, 0, 0, 4, 0, math.tau+.01)

    def setUp(self):
        self.rows = [{'id': 'root', 'parent': None, 'value': 100},
                     {'id': 'a', 'parent': 'root', 'value': None},
                     {'id': 'a1', 'parent': 'a', 'value': 10},
                     {'id': 'a2', 'parent': 'a', 'value': 30},
                     {'id': 'b', 'parent': 'root', 'value': 60},
                     {'id': 'z', 'parent': 'root', 'value': 0}]

    def test_hierarchy_rectangles_cover_source_and_conserve_parent_breadth(self):
        original = copy.deepcopy(self.rows)
        cells = hierarchy_partition(self.rows, bounds=(10, 20, 300, 90))
        self.assertEqual(self.rows, original)
        self.assertEqual([cell['source_index'] for cell in cells], list(range(len(self.rows))))
        by_id = {cell['id']: cell for cell in cells}
        self.assertEqual(by_id['a']['value'], 40)
        self.assertEqual(by_id['a']['width'], 120)
        self.assertEqual(by_id['b']['width'], 180)
        self.assertEqual(by_id['z']['width'], 0)
        for key in ['root', 'a']:
            children = [cell for cell in cells if cell['parent'] == key]
            self.assertAlmostEqual(sum(cell['width'] for cell in children), by_id[key]['width'])
            self.assertAlmostEqual(children[0]['x'], by_id[key]['x'])
            self.assertAlmostEqual(children[-1]['x']+children[-1]['width'], by_id[key]['x']+by_id[key]['width'])

    def test_hierarchy_angular_conservation_rotation_and_equal_area_rings(self):
        cells = hierarchy_partition(self.rows, layout='angular', start_angle=-math.pi, angle_span=math.pi, inner_radius=2, outer_radius=10)
        by_id = {cell['id']: cell for cell in cells}
        self.assertAlmostEqual(by_id['a']['angle_span'], math.pi*.4)
        self.assertAlmostEqual(by_id['b']['start_angle'], -math.pi+math.pi*.4)
        for key in ['root', 'a']:
            self.assertAlmostEqual(sum(c['angle_span'] for c in cells if c['parent'] == key), by_id[key]['angle_span'])
        root, child, grandchild = by_id['root'], by_id['a'], by_id['a1']
        areas = [cell['outer_radius']**2-cell['inner_radius']**2 for cell in [root, child, grandchild]]
        self.assertAlmostEqual(areas[0], areas[1])
        self.assertAlmostEqual(areas[1], areas[2])
        self.assertAlmostEqual(child['inner_radius'], root['outer_radius'])

    def test_zero_tree_keeps_all_nodes_but_no_positive_breadth(self):
        rows = [{'id': 'r', 'parent': None, 'value': None}, {'id': 'a', 'parent': 'r', 'value': 0}]
        for layout, field in [('rect', 'width'), ('angular', 'angle_span')]:
            cells = hierarchy_partition(rows, layout=layout)
            self.assertEqual(len(cells), 2)
            self.assertTrue(all(cell[field] == 0 for cell in cells))

    def test_hierarchy_cycles_unknown_parents_forests_and_duplicate_ids_fail(self):
        cases = [[{'id': 'a', 'parent': 'b', 'value': 1}, {'id': 'b', 'parent': 'a', 'value': 1}],
                 [{'id': 'a', 'parent': 'unknown', 'value': 1}],
                 [{'id': 'a', 'parent': None, 'value': 1}, {'id': 'b', 'parent': None, 'value': 1}],
                 [{'id': 'a', 'parent': None, 'value': 1}, {'id': 'a', 'parent': None, 'value': 1}]]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                hierarchy_partition(rows)

    def test_hierarchy_total_missing_negative_and_nonfinite_fail(self):
        for index, value in [(0, 99), (2, None), (2, -1), (2, float('nan'))]:
            rows = copy.deepcopy(self.rows)
            rows[index]['value'] = value
            with self.subTest(index=index, value=value), self.assertRaises(ValueError):
                hierarchy_partition(rows)


if __name__ == '__main__':
    unittest.main()
