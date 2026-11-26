"""Redes descritivas de associação; não estima causalidade ou previsão."""
import numpy as np
import pandas as pd
from .pair_support import summarize_pairs


def select_edges(counts, min_pairs=100, min_coverage=0.5, min_abs_phi=0.1):
    if not 0 <= min_coverage <= 1 or not 0 <= min_abs_phi <= 1:
        raise ValueError('Limiares devem estar entre 0 e 1')
    c=counts.copy()
    if c[['node_a','node_b']].isna().any().any() or c.node_a.eq(c.node_b).any():
        raise ValueError('Nós ausentes ou autorrelações')
    if (c.node_a > c.node_b).any():
        raise ValueError('Ordene os nomes dos nós antes de gerar as contagens')
    out=summarize_pairs(c,min_pairs)
    out['assessable']=out.status.eq('eligible_descriptive') & out.pair_coverage.ge(min_coverage)
    out['selected']=out.assessable & out.phi.abs().ge(min_abs_phi) & out.phi.ne(0)
    out['edge_status']=np.select(
        [~out.status.eq('eligible_descriptive'),~out.assessable,out.selected],
        [out.status,'low_coverage','selected'],default='below_effect_threshold')
    return out


def canonical_counts(counts):
    """Inverter orientação exige também trocar células 01 e 10."""
    c=counts.copy()
    swap=c.node_a > c.node_b
    c.loc[swap,['node_a','node_b']]=c.loc[swap,['node_b','node_a']].to_numpy()
    c.loc[swap,['n01','n10']]=c.loc[swap,['n10','n01']].to_numpy()
    return c


def compare_waves(edges):
    if edges.duplicated(['wave','node_a','node_b']).any():
        raise ValueError('Pares duplicados por onda')
    rows=[]
    waves=sorted(edges.wave.unique())
    for previous,current in zip(waves,waves[1:]):
        if current != previous+1:
            continue
        p=edges[edges.wave.eq(previous)]
        q=edges[edges.wave.eq(current)]
        common=p.merge(q,on=['node_a','node_b'],suffixes=('_before','_after'),validate='one_to_one')
        common=common[common.assessable_before & common.assessable_after]
        before=common.selected_before; after=common.selected_after
        union=int((before|after).sum()); intersection=int((before&after).sum())
        rows.append(dict(wave_before=previous,wave_after=current,n_common=len(common),
            gained=int((~before&after).sum()),lost=int((before&~after).sum()),
            retained=intersection,jaccard=intersection/union if union else np.nan,
            sign_flips=int((before&after&(common.phi_before*common.phi_after<0)).sum()),
            mean_abs_delta_phi=(common.phi_after-common.phi_before).abs().mean()))
    return pd.DataFrame(rows,columns=['wave_before','wave_after','n_common','gained','lost',
        'retained','jaccard','sign_flips','mean_abs_delta_phi'])


def plot_snapshots(edges,nodes,labels):
    import matplotlib.pyplot as plt
    import networkx as nx
    from matplotlib.lines import Line2D
    waves=sorted(edges.wave.unique())
    if not waves:
        raise ValueError('Não há ondas para desenhar')
    pos=nx.circular_layout(nodes)
    fig,axes=plt.subplots((len(waves)+2)//3,3,figsize=(18,5*((len(waves)+2)//3)),squeeze=False)
    for ax,wave in zip(axes.flat,waves):
        g=nx.Graph(); g.add_nodes_from(nodes)
        part=edges[edges.wave.eq(wave)]
        chosen=part[part.selected]
        for r in chosen.itertuples(): g.add_edge(r.node_a,r.node_b,weight=r.phi)
        nx.draw_networkx_nodes(g,pos,ax=ax,node_size=280,node_color='#dce7ef')
        nx.draw_networkx_labels(g,pos,labels={k:labels.get(k,k) for k in nodes},ax=ax,font_size=8)
        for positive,color,style in [(True,'#1261a0','solid'),(False,'#b35412','dashed')]:
            pairs=[(a,b) for a,b,d in g.edges(data=True) if (d['weight']>0)==positive]
            nx.draw_networkx_edges(g,pos,ax=ax,edgelist=pairs,edge_color=color,style=style,
                width=[0.5+4*abs(g[a][b]['weight']) for a,b in pairs])
        ax.set_title(f'Onda {wave}: {len(chosen)} arestas / {int(part.assessable.sum())} pares avaliáveis')
        ax.margins(0.3); ax.axis('off')
    for ax in list(axes.flat)[len(waves):]: ax.axis('off')
    fig.legend(handles=[Line2D([0],[0],color='#1261a0',label='Phi positivo'),
        Line2D([0],[0],color='#b35412',linestyle='--',label='Phi negativo')],loc='upper center',bbox_to_anchor=(0.5,0.94),ncol=2)
    fig.suptitle('Associações descritivas por onda — entrevistas 50+, sem ponderação',y=0.99)
    fig.tight_layout(rect=(0,0,1,0.85))
    return fig
