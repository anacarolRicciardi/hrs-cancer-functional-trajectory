"""Controle estático: seleciona interações usando somente transições de treino."""
from itertools import combinations
import pandas as pd
from .disease_history import DISEASES
from .pair_support import pair_counts
from .descriptive_graphs import canonical_counts,select_edges


def observed_states(x):
    states=pd.DataFrame(index=x.index)
    for d in DISEASES:
        state=x[f'{d}__history_asof']
        carried=x[f'{d}__carried_without_current_evidence']
        if not state.dropna().isin([0,1]).all() or not carried.isin([0,1,False,True]).all():
            raise ValueError('Estados ou máscara de evidência inválidos')
        states[d]=state.where(carried.eq(0))
    return states


def learn_graph(x,keys,min_pairs=100,min_coverage=.5,min_abs_phi=.1):
    if not x.index.equals(keys.index) or len(x)!=len(keys):
        raise ValueError('Índices dos atributos e chaves não coincidem')
    if keys[['id','wave']].isna().any().any() or keys.duplicated(['id','wave']).any():
        raise ValueError('Chaves inválidas')
    states=observed_states(x)
    # Uma linha por transição: pessoas com mais transições têm maior contribuição.
    # O id abaixo é apenas identificador temporário da linha, não identificador HRS.
    states['id']=range(len(states)); states['wave']=0
    counts=canonical_counts(pair_counts(states,sorted(DISEASES)))
    edges=select_edges(counts,min_pairs,min_coverage,min_abs_phi)
    pairs=list(edges.loc[edges.selected,['node_a','node_b']].itertuples(index=False,name=None))
    return edges,pairs


def augment_interactions(x,pairs):
    states=observed_states(x)
    out=x.copy()
    seen=set()
    for a,b in pairs:
        pair=tuple(sorted((a,b)))
        if a==b or a not in DISEASES or b not in DISEASES or pair in seen:
            raise ValueError('Par inválido ou duplicado')
        seen.add(pair)
        # Produto ausente se qualquer estado não tiver evidência atual.
        out[f'interaction__{pair[0]}__{pair[1]}']=states[a]*states[b]
    return out


def all_pairs():
    return list(combinations(sorted(DISEASES),2))
