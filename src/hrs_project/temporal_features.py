"""Atribuição retrospectiva auditável de snapshots conhecidos antes da previsão."""
import numpy as np
import pandas as pd
from .graph_interactions import observed_states,all_pairs


def assign_cutoffs(months,cutoffs,frozen_cutoff=None):
    values=np.asarray(months,dtype=float)
    cuts=np.asarray(sorted(set(cutoffs)),dtype=float)
    if values.ndim!=1 or not np.isfinite(values).all() or (values%1!=0).any():
        raise ValueError('Meses de previsão inválidos')
    if not len(cuts) or not np.isfinite(cuts).all() or (cuts%1!=0).any():
        raise ValueError('Cortes inválidos')
    if frozen_cutoff is not None:
        if frozen_cutoff not in cuts or (values<frozen_cutoff).any():
            raise ValueError('Rede estática indisponível antes do seu corte')
        return np.full(len(values),frozen_cutoff,dtype=float)
    ix=np.searchsorted(cuts,values,side='right')-1
    if (ix<0).any():
        raise ValueError('Previsão anterior à primeira rede: aplicar recorte comum')
    return cuts[ix]


def augment_temporal(x,months,edges,mode,frozen_cutoff=None):
    if len(x)!=len(months):
        raise ValueError('Número de meses incompatível')
    if isinstance(months,pd.Series) and not x.index.equals(months.index):
        raise ValueError('Índices de meses e atributos desalinhados')
    e=edges[edges['mode'].eq(mode)].copy()
    if e.empty or e.duplicated(['cutoff_month','node_a','node_b']).any():
        raise ValueError('Snapshots ausentes ou duplicados')
    for flag in ['selected','assessable']:
        if e[flag].dtype!=bool:
            raise ValueError('Máscaras devem ser booleanas')
    if (e.selected & ~e.assessable).any():
        raise ValueError('Aresta selecionada sem suporte')
    expected=set(all_pairs())
    for _,part in e.groupby('cutoff_month'):
        if set(zip(part.node_a,part.node_b))!=expected:
            raise ValueError('Snapshot não contém exatamente os 28 pares canônicos')
    if not np.isfinite(e.loc[e.assessable,'phi']).all() or e.loc[e.assessable,'phi'].abs().gt(1).any():
        raise ValueError('Phi inválido nos pares avaliáveis')
    assigned=assign_cutoffs(months,e.cutoff_month.unique(),frozen_cutoff)
    out=x.copy(); states=observed_states(x)
    for a,b in all_pairs():
        part=e[e.node_a.eq(a)&e.node_b.eq(b)].set_index('cutoff_month')
        weights=part.phi.where(part.selected,0.).where(part.assessable)
        w=pd.Series(assigned,index=x.index).map(weights)
        # Desconhecido permanece ausente mesmo se a aresta não foi selecionada.
        out[f'graph_product__{a}__{b}']=states[a]*states[b]*w
    audit=pd.DataFrame({'prediction_month':np.asarray(months), 'snapshot_cutoff':assigned,
        'months_since_snapshot':np.asarray(months)-assigned},index=x.index)
    return out,audit
