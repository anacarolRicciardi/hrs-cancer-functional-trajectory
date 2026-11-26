"""Figuras científicas PNG/SVG a partir exclusivamente de agregados do 00k."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.lines import Line2D

RUN=Path(sys.argv[1]).resolve();OUT=RUN/'figuras';OUT.mkdir(exist_ok=True)
edges=pd.read_csv(RUN/'arestas_temporais.csv')
metrics=pd.read_csv(RUN/'metricas.csv');contrasts=pd.read_csv(RUN/'comparacoes.csv')
cal=pd.read_csv(RUN/'calibracao.csv')
LABEL={'arthritis':'Artrite','cancer':'Câncer','diabetes':'Diabetes','heart':'Doença cardíaca',
       'hypertension':'Hipertensão','lung':'Doença pulmonar','psychiatric':'Condição psiquiátrica','stroke':'AVC'}
MODELS={'B_functional':'Histórico funcional','B_pairs':'+ Todos os pares',
        'B_static':'+ Rede estática','B_rolling':'+ Rede móvel','B_expanding':'+ Rede acumulada'}
TEAL='#007F86';NAVY='#132E46';ORANGE='#C75B35';GRAY='#647482'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.titlesize':15,
    'axes.labelsize':12,'axes.spines.top':False,'axes.spines.right':False,
    'axes.edgecolor':'#B9C4CB','text.color':NAVY,'axes.labelcolor':NAVY,
    'xtick.color':GRAY,'ytick.color':GRAY,'svg.fonttype':'none'})
def save(fig,name):
    fig.savefig(OUT/f'{name}.png',dpi=240,bbox_inches='tight',facecolor='white')
    fig.savefig(OUT/f'{name}.svg',bbox_inches='tight',facecolor='white');plt.close(fig)

# Layout idêntico em todos os cortes, para que mudança geométrica não simule mudança de aresta.
nodes=list(LABEL);theta=np.linspace(np.pi/2,np.pi/2+2*np.pi,len(nodes),endpoint=False)
pos={n:np.array([np.cos(a),np.sin(a)]) for n,a in zip(nodes,theta)}
fig,axes=plt.subplots(1,2,figsize=(12,5.4))
network_rows=[]
for ax,year in zip(axes,[2000,2013]):
    e=edges[edges['mode'].eq('rolling_48')&edges.cutoff_month.eq(year*12+1)]
    selected=e[e.selected]
    for r in selected.itertuples():
        a,b=pos[r.node_a],pos[r.node_b]
        ax.plot([a[0],b[0]],[a[1],b[1]],color=TEAL if r.phi>=0 else ORANGE,
                lw=1+10*abs(r.phi),alpha=.65,zorder=1)
    for n,xy in pos.items():
        ax.scatter(*xy,s=720 if n=='cancer' else 400,c=ORANGE if n=='cancer' else NAVY,zorder=2,edgecolor='white',linewidth=2)
        labelxy=xy*1.40
        label=LABEL[n].replace('Doença ','Doença\n').replace('Condição ','Condição\n')
        if n=='psychiatric':labelxy=np.array([1.18,0.])
        ax.text(*labelxy,label,ha='left' if n=='psychiatric' else 'center',va='center',fontsize=10,fontweight='bold' if n=='cancer' else 'normal')
    direct=selected[selected.node_a.eq('cancer')|selected.node_b.eq('cancer')]
    network_rows.append({'year':year,'selected_edges':len(selected),'cancer_edges':len(direct)})
    ax.set_title(f'Janeiro de {year}\n{len(selected)} arestas selecionadas',pad=18)
    ax.set(xlim=(-1.95,1.95),ylim=(-1.65,1.65));ax.set_aspect('equal');ax.axis('off')
fig.subplots_adjust(wspace=.10,top=.82,bottom=.13)
fig.text(.5,.03,'Nós = condições • espessura = |phi| • destaque do câncer é editorial, não importância\nSomente arestas selecionadas: |phi| ≥ 0,10; suporte ≥ 100; cobertura ≥ 50%',ha='center',fontsize=11,color=GRAY)
save(fig,'01_redes');pd.DataFrame(network_rows).to_csv(OUT/'resumo_redes.csv',index=False)

c=edges[edges['mode'].eq('rolling_48')&(edges.node_a.eq('cancer')|edges.node_b.eq('cancer'))].copy()
c['other']=np.where(c.node_a.eq('cancer'),c.node_b,c.node_a)
c['year']=((c.cutoff_month-1)//12).astype(int)
names=[n for n in nodes if n!='cancer'];years=sorted(c.year.unique())
matrix=c.pivot(index='other',columns='year',values='phi').reindex(index=names,columns=years)
assess=c.pivot(index='other',columns='year',values='assessable').reindex(index=names,columns=years)
selected=c.pivot(index='other',columns='year',values='selected').reindex(index=names,columns=years)
bound=max(.1,float(np.nanmax(np.abs(matrix.to_numpy()))))
fig,ax=plt.subplots(figsize=(10,4.8),layout='constrained')
im=ax.imshow(matrix.where(assess).to_numpy(),cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound),aspect='auto')
ax.set_yticks(range(len(names)),[LABEL[n] for n in names]);ax.set_xticks(range(len(years)),years,rotation=45)
for i in range(len(names)):
    for j in range(len(years)):
        if selected.iloc[i,j]:ax.text(j,i,'●',ha='center',va='center',fontsize=8,color='black')
ax.set_xlabel('Ano do corte da rede móvel de 48 meses')
fig.colorbar(im,ax=ax,label='Associação phi (não causal)',shrink=.85)
save(fig,'02_cancer_tempo')
c[['year','other','phi','assessable','selected','n_pair','pair_coverage']].to_csv(OUT/'associacoes_cancer.csv',index=False)

b=contrasts[contrasts.metric.eq('brier')].reset_index(drop=True)
labels=['Móvel − histórico funcional','Móvel − estática','Móvel − todos os pares',
        'Acumulada − histórico funcional','Estática − histórico funcional','Todos os pares − histórico funcional']
fig,ax=plt.subplots(figsize=(10,5),layout='constrained')
for i,r in b.iterrows():
    color=TEAL if i==0 else GRAY
    ax.plot([r.low,r.high],[i,i],lw=3 if i==0 else 2,color=color)
    ax.scatter(r.delta,i,s=65 if i==0 else 40,color=color,zorder=3)
ax.axvline(0,color=ORANGE,ls='--',lw=1.3);ax.set_yticks(range(len(b)),labels);ax.invert_yaxis()
ax.set_xlabel('Delta Brier e IC95% · negativo favorece o candidato')
ax.grid(axis='x',alpha=.15)
save(fig,'03_comparacoes')

fig,axes=plt.subplots(1,2,figsize=(10,4.4),layout='constrained')
for ax,name in zip(axes,['B_functional','B_rolling']):
    rows=cal[cal.model.eq(name)&cal.n.gt(0)]
    ax.plot([0,1],[0,1],ls='--',color=GRAY,lw=1)
    ax.scatter(rows.mean_prediction,rows.observed_fraction,s=60,color=TEAL if name=='B_rolling' else NAVY)
    for r in rows.itertuples():
        ax.annotate(f'n={r.n}'+('*' if r.small_bin else ''),(r.mean_prediction,r.observed_fraction),
            xytext=(4,6),textcoords='offset points',fontsize=9)
    upper=max(.6,float(rows[['mean_prediction','observed_fraction']].max().max())+.08)
    ax.set(xlim=(0,upper),ylim=(0,upper),title=MODELS[name],xlabel='Probabilidade média prevista',ylabel='Fração ADL observada')
    ax.grid(alpha=.12)
save(fig,'04_calibracao')

primary=b.iloc[0]
summary={'primary_delta':float(primary.delta),'primary_low':float(primary.low),'primary_high':float(primary.high),
    'primary_conclusive_gain':bool(primary.high<0),'primary_conclusive_worse':bool(primary.low>0),
    'cancer_selected_rows':int(c.selected.sum()),'cancer_assessable_rows':int(c.assessable.sum()),
    'max_abs_cancer_phi':float(c.loc[c.assessable,'phi'].abs().max()),'networks':network_rows}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2));print('FIGURAS:',OUT)
