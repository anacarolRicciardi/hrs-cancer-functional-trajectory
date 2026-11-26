"""Avaliação agregada de probabilidades no subgrupo; não ajusta modelos."""
import numpy as np
import pandas as pd
from .reference_models import probability_metrics
from .cluster_uncertainty import cluster_indices

BINS = [0.,.05,.10,.20,.40,1.]


def calibration_table(y,probabilities):
    y=np.asarray(y);p=np.asarray(probabilities,dtype=float)
    probability_metrics(y,p)
    frame=pd.DataFrame({'y':y,'p':p})
    frame['bin']=pd.cut(p,BINS,include_lowest=True,right=True)
    out=frame.groupby('bin',observed=False).agg(n=('y','size'),events=('y','sum'),
        observed_fraction=('y','mean'),mean_prediction=('p','mean')).reset_index()
    out['bin']=out.bin.astype(str)
    out['small_bin']=out.n.lt(20)
    return out


def absolute_intervals(y,probabilities,groups,n_boot=1000,seed=2026):
    y=np.asarray(y);p=np.asarray(probabilities,dtype=float);groups=np.asarray(groups)
    if len(groups)!=len(y) or n_boot<20:raise ValueError('Grupos ou réplicas inválidos')
    point=probability_metrics(y,p)
    point['mean_prediction_minus_observed']=float(p.mean()-y.mean())
    metrics=['brier','log_loss','roc_auc','average_precision','mean_prediction_minus_observed']
    rng=np.random.default_rng(seed);draws=[]
    for _ in range(n_boot):
        ix=cluster_indices(groups,rng)
        row=probability_metrics(y[ix],p[ix])
        row['mean_prediction_minus_observed']=float(p[ix].mean()-y[ix].mean())
        draws.append(row)
    draws=pd.DataFrame(draws);rows=[]
    for name in metrics:
        valid=draws[name].dropna();enough=len(valid)>=.9*n_boot
        rows.append({'metric':name,'estimate':point[name],
            'low':valid.quantile(.025) if enough else np.nan,
            'high':valid.quantile(.975) if enough else np.nan,
            'valid_replicates':len(valid),'requested_replicates':n_boot})
    return pd.DataFrame(rows)
