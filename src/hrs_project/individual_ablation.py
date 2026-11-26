"""Comparação incremental fixa, sem seleção orientada pelos resultados."""
import numpy as np
import pandas as pd
from .disease_history import DISEASES
from .integrated_panel import feature_columns

FUNCTIONAL = ['individual__previous_adl','individual__prior_adl_positive']
OBSERVATION = ['individual__previous_interviews','individual__interval_months',
               'individual__wave_gap','individual__known_conditions','individual__comparable_conditions']
DISEASE = ['individual__positive_conditions','individual__new_records_complete',
           'individual__new_records_per_year'] + [f'individual__{field}__{d}'
           for d in DISEASES for field in ['new_record','persistent_pair_of_visits']]
MODELS = ('A_history','B_functional','C_observation','D_disease')
COMPARISONS = (('A_history','B_functional'),('B_functional','C_observation'),
               ('C_observation','D_disease'),('A_history','D_disease'))


def build_ablation_designs(x, extra, months, anchor=24001):
    if not x.index.equals(extra.index) or not x.index.equals(months.index):
        raise ValueError('Índices desalinhados')
    if x.columns.duplicated().any() or extra.columns.duplicated().any():
        raise ValueError('Colunas duplicadas')
    if list(x.columns)!=feature_columns():
        raise ValueError('Esperados exatamente os atributos de referência auditados')
    expected=set(FUNCTIONAL+OBSERVATION+DISEASE)
    actual={c for c in extra if c.startswith('individual__')}
    if actual!=expected:
        raise ValueError('Contrato de atributos individuais mudou')
    if not np.isfinite(months.to_numpy(dtype=float)).all() or months.lt(anchor).any():
        raise ValueError('Calendário fora do recorte')
    designs={}
    for name,group in zip(MODELS,[[],FUNCTIONAL,FUNCTIONAL+OBSERVATION,FUNCTIONAL+OBSERVATION+DISEASE]):
        # Mesma ordem de colunas do 00g no modelo D, para reproduzir seu ajuste.
        selected=[c for c in extra if c in group]
        frame=pd.concat([x,extra[selected]],axis=1)
        frame['calendar_year_since_2000']=(months-anchor)/12
        if np.isinf(frame.to_numpy(dtype=float)).any():raise ValueError('Atributos infinitos')
        designs[name]=frame
    return designs


def feature_groups():
    return pd.DataFrame([{'feature':c,'group':g} for g,cols in
        [('functional',FUNCTIONAL),('observation',OBSERVATION),('disease',DISEASE)] for c in cols])
