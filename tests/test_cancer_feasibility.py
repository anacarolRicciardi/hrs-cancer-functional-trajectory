import unittest
import numpy as np
import pandas as pd
from hrs_project.cancer_feasibility import classify_cancer,aggregate_feasibility
from hrs_project.evaluation_split import partition_group


def fixture():
    h=next(i for i in range(100) if partition_group(i)=='train')
    return pd.DataFrame({'id':[1]*4,'household_id':[h]*4,'wave':[8,9,10,11],
        'status':[1,1,1,5],'proxy':0,'age_end':65,'adl_state':[0,0,1,np.nan],
        'adl_complete':[True,True,True,False],'interview_month':[24061,24085,24109,np.nan],
        'interview_observed':[True,True,True,False],'eligible_baseline':[True,True,False,False],
        'cancer__history_asof':[0,1,1,1],'cancer__ever_positive_recorded':[0,1,1,1],
        'cancer__carried_without_current_evidence':[False,False,False,True],
        'cancer__evidence':['denies_ever','positive','no_new_report','no_interview']})


class CancerTests(unittest.TestCase):
    def test_new_report_and_future_invariance(self):
        p=fixture();a=classify_cancer(p.iloc[:2]);b=classify_cancer(p)
        pd.testing.assert_frame_equal(a,b.iloc[:2])
        self.assertEqual(b.new_report.tolist(),[False,True,False,False])

    def test_uncertain_or_preexisting_not_new(self):
        for col,value in [('cancer__carried_without_current_evidence',True),
                          ('cancer__history_asof',np.nan),('cancer__ever_positive_recorded',1)]:
            p=fixture();p.loc[0,col]=value
            self.assertFalse(classify_cancer(p).new_report.any())
        p=fixture();p.loc[1,'cancer__evidence']='positive_dispute'
        self.assertFalse(classify_cancer(p).new_report.any())

    def test_zero_events_vs_no_observation(self):
        p=fixture();p.loc[2,['adl_state','eligible_baseline']]=[0,True]
        cfg={'seed':2026,'fractions':[.6,.2,.2],'train_end_month':24156,'validation_end_month':24204}
        t=aggregate_feasibility(p,cfg)
        summary=t['resumo_viabilidade'].set_index('cancer_group')
        self.assertEqual(summary.loc['historico_positivo','observed'],1)
        self.assertEqual(summary.loc['historico_positivo','events_adl'],0)
        self.assertEqual(summary.loc['historico_positivo','unknown_outcome'],1)
        self.assertIn('death_status_review',set(t['seguimento'].followup))

    def test_terminal_wave_is_not_death_or_nonresponse(self):
        p=fixture().iloc[:2].copy()
        cfg={'seed':2026,'fractions':[.6,.2,.2],'train_end_month':24156,'validation_end_month':24204}
        t=aggregate_feasibility(p,cfg)
        s=t['resumo_viabilidade'].set_index('cancer_group').loc['historico_positivo']
        self.assertEqual(s.observed,0);self.assertTrue(pd.isna(s.event_fraction))
        self.assertIn('no_adjacent_wave',set(t['seguimento'].followup))

    def test_test_household_rejected(self):
        p=fixture();p['household_id']=next(i for i in range(100) if partition_group(i)=='test')
        cfg={'seed':2026,'fractions':[.6,.2,.2],'train_end_month':24156,'validation_end_month':24204}
        with self.assertRaises(ValueError):aggregate_feasibility(p,cfg)

    def test_duplicates_rejected(self):
        p=fixture()
        with self.assertRaises(ValueError):classify_cancer(pd.concat([p,p.iloc[:1]]))

if __name__=='__main__':unittest.main()
