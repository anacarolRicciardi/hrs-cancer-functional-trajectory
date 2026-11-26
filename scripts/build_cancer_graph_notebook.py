"""Experimento 00k: grafos sobre a mesma referência funcional, sem executar dados."""
from pathlib import Path
import nbformat as nb
ROOT=Path(__file__).resolve().parents[1]
old=nb.read(ROOT/'notebooks/00j_avaliacao_cancer.ipynb',as_version=4)
inherited=[c.source for c in old.cells if c.cell_type=='code'][:5]
md=nb.v4.new_markdown_cell;code=nb.v4.new_code_cell
cells=[md('''# 00k — Grafos de multimorbidade na previsão funcional em câncer

## Protocolo exploratório fixado antes desta execução
Referência B: história básica + história funcional + calendário, já avaliada no 00j.
Acrescentar separadamente (1) todos os 28 produtos binários, (2) rede fixa de 2000,
(3) rede móvel de 48 meses, (4) rede acumulada. Mesmas linhas, regressão C=1,
pré-processamento aprendido somente no treino geral. Não seleciona modelo ou limiar.

Comparação principal: **rede móvel menos B, no Brier, na validação com câncer**.
Controles: móvel versus estática e versus todos os pares. Demais são secundários.
Seleção dessa extensão ocorreu depois dos resultados anteriores: não é confirmação.
Não é GNN: são produtos dos estados de doenças ponderados por associação phi.

Redes do 00b estimadas somente na população de referência de treino, sem alvos,
uma última entrevista por pessoa antes de cada corte. Na validação, redes temporais
congeladas em janeiro de 2013. Rede estática de janeiro de 2000 é antiga por desenho.
Isso testa a representação aprendida temporalmente, não atualização online na validação.
28 colunas candidatas por extensão; a dimensão efetiva pode ser menor. Padronização
pode absorver pesos constantes, portanto peso phi não é importância clínica.
'''),md('## Reproduzir desenho e métricas do 00h/00j')]+[code(s) for s in inherited]
cells += [code('''from hrs_project.graph_interactions import augment_interactions
from hrs_project.temporal_features import augment_temporal
NETWORK_DIR=Path(protocol['network_dir'])
GRAPH_REFERENCE=SPLIT_DIR/'avaliacao_cancer_20261122T173738515878Z'
assert (NETWORK_DIR/'_SUCCESS').exists() and (GRAPH_REFERENCE/'_SUCCESS').exists()
network_config=json.loads((NETWORK_DIR/'config.json').read_text(encoding='utf-8'))
assert network_config['split_config']==config
assert network_config['strictly_before_month'] and not network_config['condition_on_future_outcome']
edges=pd.read_csv(NETWORK_DIR/'arestas_temporais.csv')
network_audit=pd.read_csv(NETWORK_DIR/'auditoria_temporal.csv')
assert network_audit.max_source_month.lt(network_audit.cutoff_month).all()
assert edges.cutoff_month.max()==config['train_end_month']+1
graph_designs={};map_rows=[]
for split,(keys,x,y,months,groups) in datasets.items():
    base=designs[split]['B_functional']
    graph_designs[split]={'B_functional':base,'B_pairs':augment_interactions(base,all_pairs())}
    for name,mode,frozen in [('B_static','rolling_48',ANCHOR),('B_rolling','rolling_48',None),('B_expanding','expanding',None)]:
        frame,mapping=augment_temporal(base,months,edges,mode,frozen)
        pd.testing.assert_frame_equal(frame[base.columns],base)
        assert mapping.snapshot_cutoff.le(mapping.prediction_month).all()
        if split=='validation' and frozen is None:
            assert mapping.snapshot_cutoff.eq(config['train_end_month']+1).all()
        graph_designs[split][name]=frame
        summary=mapping.groupby('snapshot_cutoff').agg(n=('prediction_month','size'),
            first_prediction=('prediction_month','min'),last_prediction=('prediction_month','max')).reset_index()
        summary['model']=name;summary['split']=split;map_rows.append(summary)
mapping_audit=pd.concat(map_rows,ignore_index=True)
'''),md('## Ajustar extensões e avaliar sem modificar o recorte'),code('''graph_predictions={'B_functional':predictions['B_functional']}
graph_fits={'B_functional':fitted_models['B_functional']};metrics_rows=[];dimensions=[]
for name,frame in graph_designs['train'].items():
    if name!='B_functional':
        fitted=fit_references(frame,datasets['train'][2]);graph_fits[name]=fitted
        graph_predictions[name]=predict_references(fitted,graph_designs['validation'][name])['logistic']
    dimensions.append({'model':name,'candidate_columns':len(frame.columns),
        'nonconstant_columns':int(frame.nunique(dropna=True).gt(1).sum()),
        'all_missing_columns':int(frame.isna().all().sum()),
        'transformed_columns':len(graph_fits[name]['model'].named_steps['logistic'].coef_[0])})
    for scope,select in [('general',np.ones(len(mask),dtype=bool)),('cancer',mask)]:
        metrics_rows.append({'scope':scope,'model':name,**probability_metrics(
            datasets['validation'][2].loc[select],graph_predictions[name][select])})
graph_metrics=pd.DataFrame(metrics_rows);dimensions=pd.DataFrame(dimensions)
expected=pd.read_csv(GRAPH_REFERENCE/'metricas_cancer.csv').set_index('model').loc['B_functional']
actual=graph_metrics[(graph_metrics.scope=='cancer')&(graph_metrics.model=='B_functional')].iloc[0]
for key in ['n','events','brier','log_loss','roc_auc','average_precision','mean_prediction']:
    assert np.isclose(actual[key],expected[key],rtol=1e-7,atol=1e-9),key
display(graph_metrics);display(dimensions)
'''),md('''## Incerteza pareada no subgrupo
1.000 réplicas de domicílios; condicionado aos modelos e redes ajustados.
Não inclui estimação das redes ou reajuste dos modelos. Sem ajuste de multiplicidade.
Comparações na população geral são apenas métricas descritivas de contexto.
'''),code('''PAIRS=[('B_functional','B_rolling'),('B_static','B_rolling'),('B_pairs','B_rolling'),
       ('B_functional','B_expanding'),('B_functional','B_static'),('B_functional','B_pairs')]
graph_intervals=[];graph_absolute=[];graph_calibration=[]
for reference,candidate in PAIRS:
    summary,_=paired_bootstrap(sub_y,graph_predictions[reference][mask],graph_predictions[candidate][mask],
        sub_groups,N_BOOT,SEED)
    summary['reference']=reference;summary['candidate']=candidate;graph_intervals.append(summary)
for name,p in graph_predictions.items():
    summary=absolute_intervals(sub_y,p[mask],sub_groups,N_BOOT,SEED);summary['model']=name;graph_absolute.append(summary)
    cal=calibration_table(sub_y,p[mask]);cal['model']=name;graph_calibration.append(cal)
graph_intervals=pd.concat(graph_intervals,ignore_index=True)
graph_absolute=pd.concat(graph_absolute,ignore_index=True)
graph_calibration=pd.concat(graph_calibration,ignore_index=True)
display(graph_intervals[graph_intervals.metric.eq('brier')])
'''),md('## Salvar agregados e protocolo da execução'),code('''OUT=SPLIT_DIR/('grafos_cancer_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
OUT.mkdir(exist_ok=False)
for name,frame in [('metricas',graph_metrics),('comparacoes',graph_intervals),('intervalos_absolutos',graph_absolute),
    ('calibracao',graph_calibration),('suporte',support),('dimensoes',dimensions),('atribuicao_redes',mapping_audit),
    ('arestas_temporais',edges),('auditoria_redes',network_audit)]:
    frame.to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig')
record={'stage':'cancer_graph_exploratory_v1','split_source':str(SPLIT_DIR),'network_source':str(NETWORK_DIR),
    'reference_run':str(GRAPH_REFERENCE),'training_population':'general_train','test_evaluated':False,
    'validation_previously_used':True,'individual_exported':False,'network_frozen_month':24157,
    'primary_comparison':['B_functional','B_rolling'],'primary_metric':'brier','n_boot':N_BOOT,'seed':SEED,
    'thresholds':{k:network_config[k] for k in ['min_pairs','min_coverage','min_abs_phi']},
    'python':sys.version,'pandas':pd.__version__,'numpy':np.__version__,'sklearn':sklearn.__version__,
    'code_sha256':{name:hashlib.sha256((ROOT/'src/hrs_project'/name).read_bytes()).hexdigest()
      for name in ['graph_interactions.py','temporal_features.py','reference_models.py','individual_ablation.py',
                   'individual_trajectories.py','cancer_evaluation.py','cluster_uncertainty.py']},
    'network_sha256':hashlib.sha256((NETWORK_DIR/'arestas_temporais.csv').read_bytes()).hexdigest(),
    'split_config_sha256':hashlib.sha256((SPLIT_DIR/'config.json').read_bytes()).hexdigest(),
    'reference_metrics_sha256':hashlib.sha256((GRAPH_REFERENCE/'metricas_cancer.csv').read_bytes()).hexdigest()}
(OUT/'config.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
(OUT/'_SUCCESS').write_text('ok',encoding='utf-8')
print('GRAFOS CÂNCER CONCLUÍDOS:',OUT)
''')]
n=nb.v4.new_notebook(cells=cells,metadata=old.metadata)
nb.validate(n)
for c in cells:
    if c.cell_type=='code':compile(c.source,'cell','exec')
nb.write(n,ROOT/'notebooks/00k_grafos_cancer.ipynb')
print('Notebook 00k gerado e sintaxe validada.')
