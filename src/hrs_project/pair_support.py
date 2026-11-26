"""Contagens aditivas por par; associação descritiva sem imputar ausências."""
from itertools import combinations
import numpy as np
import pandas as pd

KEYS = ['wave', 'node_a', 'node_b']
COUNTS = ['n_total', 'n_pair', 'n00', 'n01', 'n10', 'n11']


def pair_counts(frame, nodes):
    nodes = list(nodes)
    if len(nodes) < 2 or len(set(nodes)) != len(nodes):
        raise ValueError('Forneça pelo menos dois nós distintos')
    if frame[['id','wave']].isna().any().any() or frame.duplicated(['id','wave']).any():
        raise ValueError('Chaves pessoa–onda inválidas')
    if not frame[nodes].isin([0,1]).where(frame[nodes].notna(), True).all().all():
        raise ValueError('Estados devem ser 0, 1 ou ausentes')
    rows = []
    for wave, part in frame.groupby('wave'):
        for a,b in combinations(nodes,2):
            paired = part[[a,b]].dropna()
            row = dict(wave=wave,node_a=a,node_b=b,n_total=len(part),n_pair=len(paired))
            for x,y in [(0,0),(0,1),(1,0),(1,1)]:
                row[f'n{x}{y}'] = int((paired[a].eq(x)&paired[b].eq(y)).sum())
            rows.append(row)
    return pd.DataFrame(rows,columns=KEYS+COUNTS)


def summarize_pairs(counts, min_pairs=100):
    """Agrega blocos antes de calcular phi; limiar operacional, não inferencial."""
    if min_pairs < 1:
        raise ValueError('min_pairs deve ser positivo')
    values = counts[COUNTS]
    if values.isna().any().any() or (values < 0).any().any() or (values % 1 != 0).any().any():
        raise ValueError('Contagens inválidas')
    if counts[KEYS].isna().any().any():
        raise ValueError('Chaves de pares ausentes')
    if not counts[['n00','n01','n10','n11']].sum(axis=1).eq(counts.n_pair).all() or (counts.n_pair > counts.n_total).any():
        raise ValueError('Contagens inconsistentes')
    out = counts.groupby(KEYS,as_index=False)[COUNTS].sum()
    a,b,c,d = (out[k].astype(float) for k in ['n00','n01','n10','n11'])
    denominator = np.sqrt((a+b)*(c+d)*(a+c)*(b+d))
    out['pair_coverage'] = out.n_pair/out.n_total.replace(0,np.nan)
    out['status'] = np.select([out.n_pair.lt(min_pairs),denominator.eq(0)],
                              ['insufficient_support','constant_node'],default='eligible_descriptive')
    out['phi'] = ((a*d-b*c)/denominator.replace(0,np.nan)).where(out.status.eq('eligible_descriptive'))
    return out
