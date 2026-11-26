"""Separação prospectiva por calendário e domicílio de origem, sem ajuste de modelo."""
import hashlib
import numbers
import numpy as np
import pandas as pd
from .functional_panel import build_transitions


def group_key(value):
    if pd.isna(value) or str(value).strip() == '':
        raise ValueError('Domicílio ausente: revisar antes da separação')
    if isinstance(value, numbers.Real) and float(value).is_integer():
        return str(int(value))
    return str(value).strip()


def partition_group(key,seed=2026,fractions=(0.6,0.2,0.2)):
    value=int(hashlib.sha256(f'{seed}:{group_key(key)}'.encode()).hexdigest()[:16],16)/2**64
    return 'train' if value<fractions[0] else 'validation' if value<sum(fractions[:2]) else 'test'


def allocate_splits(panel, train_end=2012*12+12, validation_end=2016*12+12,
                    seed=2026, fractions=(0.6,0.2,0.2)):
    if train_end >= validation_end:
        raise ValueError('Cortes temporais fora de ordem')
    if len(fractions)!=3 or any(f<=0 for f in fractions) or not np.isclose(sum(fractions),1):
        raise ValueError('Três proporções positivas devem somar 1')
    if panel[['id','wave']].isna().any().any() or panel.duplicated(['id','wave']).any():
        raise ValueError('Chaves pessoa–onda inválidas')
    p=panel.copy()
    p['split_group']=p.household_id.map(group_key)
    if p.groupby('id').split_group.nunique().gt(1).any():
        raise ValueError('Pessoa vinculada a mais de um grupo; revisar vínculos')
    t=build_transitions(p)
    t['group_partition']=t.split_group.map(lambda key: partition_group(key,seed,fractions))
    start=t.interview_month; end=t.next_interview_month
    observed=t.followup.eq('observed') & t.target.isin([0,1])
    chronology=start.notna() & end.gt(start)
    t['time_partition']=np.select(
        [chronology & end.le(train_end),
         chronology & start.gt(train_end) & end.le(validation_end),
         chronology & start.gt(validation_end)],
        ['train','validation','test'],default='boundary_or_unknown')
    t['split']=np.where(observed & t.group_partition.eq(t.time_partition),t.group_partition,'excluded')
    t['split_reason']=np.select([~observed,~chronology,t.time_partition.eq('boundary_or_unknown'),
        t.group_partition.ne(t.time_partition)],
        ['outcome_unavailable','invalid_calendar','crosses_boundary','group_time_mismatch'],default='included')
    assigned=t[t.split.ne('excluded')]
    if assigned.groupby('id').split.nunique().gt(1).any() or assigned.groupby('split_group').split.nunique().gt(1).any():
        raise AssertionError('Sobreposição de pessoas ou domicílios entre conjuntos')
    return t


def split_audit(transitions):
    flow=transitions.groupby(['group_partition','time_partition','split','split_reason'],dropna=False).size().rename('n').reset_index()
    included=transitions[transitions.split.ne('excluded')]
    summary=included.groupby('split').agg(rows=('id','size'),people=('id','nunique'),
        households=('split_group','nunique'),events=('target','sum'),
        first_baseline_month=('interview_month','min'),last_outcome_month=('next_interview_month','max'))
    summary=summary.reindex(['train','validation','test'])
    summary['ready_for_binary_model']=summary.rows.gt(summary.events)&summary.events.gt(0)
    return flow,summary
