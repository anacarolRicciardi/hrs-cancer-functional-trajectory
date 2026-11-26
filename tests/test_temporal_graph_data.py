"""Testes artificiais de invariância, sem evidência empírica HRS."""
import sys
from pathlib import Path
import unittest
import tempfile
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from hrs_project.temporal_graph_data import (DISEASE_NAMES, build_prefix_graph,
                                           batch_graphs, calendar_boundary_audit, development_filter)


def fixture():
    p = pd.DataFrame({'id': ['fake']*3, 'wave': [5, 6, 7],
        'interview_observed': [True]*3, 'interview_month': [24001, 24025, 24049],
        'age_end': [60, 62, 64], 'proxy': [0]*3, 'adl_state': [0, 0, 1]})
    for d in DISEASE_NAMES:
        for f, val in [('history_asof', 0.), ('ever_positive_recorded', 0.),
                       ('carried_without_current_evidence', False),
                       ('waves_since_evidence', 0.), ('evidence', 'denies_ever')]:
            p[f'{d}__{f}'] = val
    return p


class GraphTests(unittest.TestCase):
    def same(self, a, b):
        self.assertEqual(set(a), set(b))
        for key in a:
            np.testing.assert_array_equal(a[key], b[key])

    def test_future_and_labels_do_not_change_graph(self):
        p = fixture()
        original = build_prefix_graph(p, 'fake', 6)
        p.loc[2, 'interview_month'] = 1
        p.loc[2, 'cancer__history_asof'] = 88
        p['target'] = [1, 0, 1]
        p['next_adl_state'] = [99, 99, 99]
        self.same(original, build_prefix_graph(p, 'fake', 6))
        self.same(original, build_prefix_graph(p.iloc[:2], 'fake', 6))
        p = pd.concat([p, p.iloc[[2]]], ignore_index=True)
        self.same(original, build_prefix_graph(p, 'fake', 6))

    def test_other_person_and_order(self):
        p = fixture()
        other = p.assign(id='other', age_end=999)
        self.same(build_prefix_graph(p, 'fake', 6),
                  build_prefix_graph(pd.concat([p, other]).sample(frac=1, random_state=3), 'fake', 6))

    def test_duplicates_and_chronology_fail(self):
        p = fixture()
        with self.assertRaises(ValueError):
            build_prefix_graph(pd.concat([p, p.iloc[[0]]]), 'fake', 6)
        p.loc[1, 'interview_month'] = 24000
        with self.assertRaises(ValueError):
            build_prefix_graph(p, 'fake', 6)
        p.loc[1, 'interview_month'] = np.nan
        with self.assertRaises(ValueError):
            build_prefix_graph(p, 'fake', 6)

    def test_unknown_is_distinct_from_zero(self):
        p = fixture()
        a = build_prefix_graph(p, 'fake', 6)
        p.loc[0, 'cancer__history_asof'] = np.nan
        b = build_prefix_graph(p, 'fake', 6)
        np.testing.assert_array_equal(a['condition_x'], b['condition_x'])
        self.assertFalse(np.array_equal(a['condition_mask'], b['condition_mask']))

    def test_single_visit_and_temporal_direction(self):
        one = build_prefix_graph(fixture(), 'fake', 5)
        self.assertEqual(one['visit_temporal'].shape, (2, 0))
        self.assertEqual(one['condition_temporal'].shape, (2, 0))
        g = build_prefix_graph(fixture(), 'fake', 6)
        for edge, month in [('visit_temporal', 'visit_month'), ('condition_temporal', 'condition_month')]:
            src, dst = g[edge]
            self.assertTrue((g[month][dst] > g[month][src]).all())

    def test_batch_has_no_cross_example_edges(self):
        b = batch_graphs([build_prefix_graph(fixture(), 'fake', 5), build_prefix_graph(fixture(), 'fake', 6)])
        for edge, left, right in [('condition_to_visit', 'condition_batch', 'visit_batch'),
                                  ('condition_temporal', 'condition_batch', 'condition_batch'),
                                  ('visit_temporal', 'visit_batch', 'visit_batch')]:
            src, dst = b[edge]
            np.testing.assert_array_equal(b[left][src], b[right][dst])
        np.testing.assert_array_equal(b['origin_visit'], [0, 2])

    def test_calendar_removal_is_identified_without_clinical_data(self):
        meta = fixture()[['id', 'wave', 'interview_month']]
        result = calendar_boundary_audit(meta, 'train', 24030, 7)
        self.assertEqual(result.wave.tolist(), [6])

    def test_unseen_evidence_has_fixed_unknown_category(self):
        p = fixture()
        p.loc[0, 'cancer__evidence'] = 'new-category'
        self.assertEqual(build_prefix_graph(p, 'fake', 5)['evidence'][2], 0)

    def test_parquet_filter_preserves_null_dates_excludes_future_and_other_people(self):
        p = fixture()
        p.loc[0, 'interview_month'] = np.nan
        p = pd.concat([p, p.iloc[[1]].assign(id='test-person')], ignore_index=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'artificial.parquet'
            p.to_parquet(path, index=False)
            got = pd.read_parquet(path, filters=development_filter(['fake'], 7, 24030))
        self.assertEqual(got.wave.tolist(), [5, 6])
        self.assertTrue(pd.isna(got.interview_month.iloc[0]))


if __name__ == '__main__':
    unittest.main()
