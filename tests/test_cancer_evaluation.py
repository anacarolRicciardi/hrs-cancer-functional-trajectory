import unittest
import numpy as np
import pandas as pd
from hrs_project.cancer_evaluation import calibration_table,absolute_intervals

class EvaluationTests(unittest.TestCase):
    def test_bins_cover_endpoints_and_preserve_totals(self):
        y=[0,1,0,1,1,0];p=[0,.05,.1,.2,.4,1]
        t=calibration_table(y,p)
        self.assertEqual(t.n.sum(),6);self.assertEqual(t.events.sum(),3)
        self.assertEqual(t.n.tolist(),[2,1,1,1,1])

    def test_empty_bins_are_unknown_not_zero_risk(self):
        t=calibration_table([0,1],[.1,.1])
        self.assertTrue(t.loc[t.n.eq(0),'observed_fraction'].isna().all())

    def test_bad_probabilities_rejected(self):
        for p in [[-.1,.2],[np.nan,.3],[.1,1.1]]:
            with self.assertRaises(ValueError):calibration_table([0,1],p)

    def test_cluster_intervals_reproducible_and_mean_error(self):
        y=np.array([0,1]*8);p=np.array([.2,.8]*8);g=np.repeat(np.arange(8),2)
        a=absolute_intervals(y,p,g,20);b=absolute_intervals(y,p,g,20)
        pd.testing.assert_frame_equal(a,b)
        r=a.set_index('metric')
        self.assertAlmostEqual(r.loc['brier','estimate'],.04)
        self.assertAlmostEqual(r.loc['mean_prediction_minus_observed','estimate'],0)
        self.assertTrue(a.valid_replicates.eq(20).all())

    def test_unknown_or_single_household_rejected(self):
        for g in [[1,1],[1,np.nan]]:
            with self.assertRaises(ValueError):absolute_intervals([0,1],[.2,.8],g,20)

if __name__=='__main__':unittest.main()
