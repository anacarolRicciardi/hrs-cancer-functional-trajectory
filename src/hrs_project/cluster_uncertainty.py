"""Bootstrap pareado de domicílios da validação, condicionado ao modelo ajustado."""
import numpy as np
import pandas as pd
from .reference_models import probability_metrics

METRICS=['brier','log_loss','roc_auc','average_precision']


def cluster_indices(groups,rng):
    codes,unique=pd.factorize(np.asarray(groups))
    if (codes<0).any() or len(unique)<2:
        raise ValueError('Necessários pelo menos dois grupos conhecidos')
    members=[np.flatnonzero(codes==i) for i in range(len(unique))]
    sampled=rng.integers(0,len(unique),size=len(unique))
    return np.concatenate([members[i] for i in sampled])


def paired_bootstrap(y,reference,candidate,groups,n_boot=1000,seed=2026):
    y=np.asarray(y); reference=np.asarray(reference); candidate=np.asarray(candidate)
    groups=np.asarray(groups)
    if len(groups)!=len(y) or n_boot<20:
        raise ValueError('Grupos incompatíveis ou menos de 20 réplicas')
    baseline=probability_metrics(y,reference)
    model=probability_metrics(y,candidate)
    rng=np.random.default_rng(seed)
    records=[]
    for b in range(n_boot):
        ix=cluster_indices(groups,rng)
        a=probability_metrics(y[ix],reference[ix]); c=probability_metrics(y[ix],candidate[ix])
        for metric in METRICS:
            records.append({'replicate':b,'metric':metric,'delta':c[metric]-a[metric]})
    draws=pd.DataFrame(records)
    rows=[]
    for metric in METRICS:
        values=draws.loc[draws.metric.eq(metric),'delta'].dropna()
        enough=len(values)>=0.9*n_boot
        rows.append(dict(metric=metric,delta=model[metric]-baseline[metric],
            low=values.quantile(.025) if enough else np.nan,
            high=values.quantile(.975) if enough else np.nan,
            valid_replicates=len(values),requested_replicates=n_boot,
            preferred_direction='negative' if metric in ['brier','log_loss'] else 'positive'))
    return pd.DataFrame(rows),draws
