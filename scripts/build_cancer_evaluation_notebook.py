"""Reutiliza o desenho 00h sem executar dados reais."""
from pathlib import Path
import nbformat as nb
ROOT=Path(__file__).resolve().parents[1]
original=nb.read(ROOT/'notebooks/00h_ablacao_trajetorias_individuais.ipynb',as_version=4)
def get(marker):
    cells=[c.source for c in original.cells if c.cell_type=='code' and marker in c.source]
    if len(cells)!=1:raise ValueError(marker)
    return cells[0]
md=nb.v4.new_markdown_cell;code=nb.v4.new_code_cell
setup=get('protocol=json.loads')+'''
from hrs_project.cancer_evaluation import calibration_table,absolute_intervals
ABLATION_RUN=SPLIT_DIR/'ablacao_individual_20261122T162234840216Z'
AUDIT_RUN=SPLIT_DIR/'viabilidade_cancer_20261122T170924213017Z'
for run in [ABLATION_RUN,AUDIT_RUN]:assert (run/'_SUCCESS').exists()
previous=json.loads((ABLATION_RUN/'config.json').read_text(encoding='utf-8'))
assert Path(previous['split_source']).resolve()==SPLIT_DIR.resolve()
assert previous['split_config_sha256']==hashlib.sha256((SPLIT_DIR/'config.json').read_bytes()).hexdigest()
for name,digest in previous['code_sha256'].items():
    assert hashlib.sha256((ROOT/'src/hrs_project'/name).read_bytes()).hexdigest()==digest, name
audit_config=json.loads((AUDIT_RUN/'config.json').read_text(encoding='utf-8'))
assert audit_config['split_config_sha256']==previous['split_config_sha256']
# Apenas as pessoas que já integram treino/validação. Nenhum X/y de teste é lido.
development_ids=pd.concat([pd.read_parquet(SPLIT_DIR/f'{s}_X.parquet',columns=['id'])
                          for s in ['train','validation']]).id.unique().tolist()
'''
load=get('dates=pd.concat').replace("pd.read_parquet(p,columns=['id','wave','interview_month'])",
    "pd.read_parquet(p,columns=['id','wave','interview_month'],filters=[('id','in',development_ids),('wave','<=',13)])")
design=get('pd.testing.assert_frame_equal').replace('pd.read_parquet(p,columns=input_columns())',
    "pd.read_parquet(p,columns=input_columns(),filters=[('id','in',development_ids),('wave','<=',13)])")
fit=get('predictions={}; fitted_models={}; rows=[]')
cells=[md('''# 00j — Modelos temporais no subgrupo com histórico de câncer

## Pergunta e desenho
O benefício do histórico funcional aparece na validação de participantes com histórico
de câncer? **Resultados reais pendentes.** Execute pessoalmente com `.venv-local`.
Reajusta A–D no mesmo treino geral do 00h, confere a reprodução e avalia suas previsões
no subgrupo de validação. Não treina modelos exclusivos para câncer, não recalibra,
não altera hiperparâmetros e não avalia teste. Os modelos anteriores não foram salvos;
o reajuste reproduz seu procedimento, com verificação das métricas.

A: histórico básico; B: A + passado funcional; C: B + acompanhamento;
D: C + atributos adicionais das doenças. A–D não contêm atributos de arestas de grafos.
Comparação principal desta extensão: **B−A no Brier**; D−C e demais contrastes são
secundários. Hipótese definida após os resultados gerais, portanto exploratória.

Histórico de câncer = `cancer__history_asof == 1` na origem; não significa câncer ativo.
O subgrupo inclui história carregada sem evidência atual, como no 00i. Não usar
novos relatos isoladamente para selecionar modelos. Existem somente 39 eventos na
validação auditada. Não se estima efeito causal do câncer nem benefício clínico.
'''),code(setup),md('## Reconstituir o recorte e os atributos do 00h'),code(load),code(design),
md('''## Reproduzir os modelos gerais antes de avaliar câncer
As verificações herdadas conferem A/D com 00g. A seguir, todos os modelos serão
conferidos com 00h. Divergência interrompe o notebook; não relaxe a tolerância.
'''),code(fit),code('''old=pd.read_csv(ABLATION_RUN/'metricas_validacao.csv').set_index('model')
current=metrics.set_index('model');checks_00h=[]
for model in current.index:
    for metric in ['n','events','event_rate','mean_prediction','brier','log_loss','roc_auc','average_precision']:
        a=float(current.loc[model,metric]);b=float(old.loc[model,metric])
        checks_00h.append({'model':model,'metric':metric,'current':a,'reference':b,
                          'passed':bool(np.isclose(a,b,rtol=1e-7,atol=1e-9,equal_nan=True))})
reproduction_00h=pd.DataFrame(checks_00h)
assert reproduction_00h.passed.all(), 'Métricas gerais divergem do 00h.'
support=[];masks={}
audit=pd.read_csv(AUDIT_RUN/'resumo_viabilidade.csv')
for split,(keys,x,y,months,groups) in datasets.items():
    mask=x['cancer__history_asof'].eq(1).to_numpy();masks[split]=mask
    expected=audit[audit.group.eq(split)&audit.cancer_group.eq('historico_positivo')].iloc[0]
    assert mask.sum()==expected.observed and y.loc[mask].sum()==expected.events_adl, 'Subgrupo difere do 00i.'
    support.append({'split':split,'transitions':int(mask.sum()),'people':keys.loc[mask,'id'].nunique(),
        'households':groups.loc[mask].nunique(),'events':int(y.loc[mask].sum()),
        'carried_history':int(x.loc[mask,'cancer__carried_without_current_evidence'].sum())})
support=pd.DataFrame(support);display(support)
mask=masks['validation']
sub_y=datasets['validation'][2].loc[mask].reset_index(drop=True)
sub_groups=datasets['validation'][4].loc[mask].reset_index(drop=True)
assert sub_y.nunique()==2 and sub_groups.nunique()>=2
sub_predictions={name:np.asarray(p)[mask] for name,p in predictions.items()}
'''),md('''## Desempenho e incerteza no subgrupo
Bootstrap de domicílios com 1.000 réplicas, condicionado aos modelos ajustados.
Não inclui incerteza do treinamento nem corrige multiplicidade. AP é average precision;
compare-a com a frequência de eventos, sem interpretar AUC como utilidade clínica.
'''),code('''sub_metrics=pd.DataFrame([{'model':name,**probability_metrics(sub_y,p),
    'mean_prediction_minus_observed':float(p.mean()-sub_y.mean())} for name,p in sub_predictions.items()])
absolute=[];comparisons=[]
for name,p in sub_predictions.items():
    part=absolute_intervals(sub_y,p,sub_groups,N_BOOT,SEED);part['model']=name;absolute.append(part)
for reference,candidate in COMPARISONS:
    part,_=paired_bootstrap(sub_y,sub_predictions[reference],sub_predictions[candidate],sub_groups,N_BOOT,SEED)
    part['reference']=reference;part['candidate']=candidate;comparisons.append(part)
absolute=pd.concat(absolute,ignore_index=True)
intervals=pd.concat(comparisons,ignore_index=True)
display(sub_metrics.round(5));display(intervals[intervals.metric.eq('brier')])
'''),md('''## Calibração descritiva
Faixas fixas de probabilidade: 0–5%, 5–10%, 10–20%, 20–40% e 40–100%, limites
superiores inclusivos. Mostrar contagens; células com menos de 20 transições são
marcadas como pequenas (regra visual, não garantia de precisão). Não são decis de risco.
Diferença média previsão−observado >0 indica superestimação média; não substitui
intercepto/inclinação de calibração. Nenhuma recalibração será feita nesta validação.
'''),code('''calibration=[]
fig_cal,axes=plt.subplots(2,2,figsize=(10,8))
for ax,(name,p) in zip(axes.flat,sub_predictions.items()):
    part=calibration_table(sub_y,p);part['model']=name;calibration.append(part)
    shown=part[part.n.gt(0)]
    ax.plot([0,1],[0,1],'--',color='gray')
    ax.scatter(shown.mean_prediction,shown.observed_fraction,color='#176b83')
    for row in shown.itertuples():
        ax.annotate(f'n={row.n}'+('*' if row.small_bin else ''),(row.mean_prediction,row.observed_fraction),
                    xytext=(3,5),textcoords='offset points',fontsize=8)
    ax.set(xlim=(0,1),ylim=(0,1),title=name,xlabel='Probabilidade média prevista',ylabel='Fração ADL observada')
fig_cal.suptitle('Câncer — calibração descritiva; * faixa com n < 20')
fig_cal.tight_layout();plt.show()
calibration=pd.concat(calibration,ignore_index=True);display(calibration)
points=intervals[intervals.metric.eq('brier')].reset_index(drop=True)
fig_delta,ax=plt.subplots(figsize=(9,4))
for i,row in points.iterrows():
    ax.plot([row.low,row.high],[i,i],color='#176b83');ax.plot(row.delta,i,'o',color='#176b83')
ax.axvline(0,color='gray',ls='--')
ax.set_yticks(range(len(points)),points.candidate+' − '+points.reference)
ax.set(xlabel='Delta Brier e IC95% — negativo favorece candidato',title='Validação no subgrupo com histórico de câncer')
fig_delta.tight_layout();plt.show()
'''),md('''## Exportar apenas agregados
Não exporta IDs, probabilidades individuais ou modelos. A igualdade das métricas
gerais é uma verificação numérica, não prova identidade bit a bit dos ajustes.
'''),code('''OUT=SPLIT_DIR/('avaliacao_cancer_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
OUT.mkdir(exist_ok=False)
for name,frame in [('suporte',support),('metricas_cancer',sub_metrics),('intervalos_absolutos',absolute),
    ('comparacoes_pareadas',intervals),('calibracao',calibration),('reproducao_00h',reproduction_00h)]:
    frame.to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig')
fig_cal.savefig(OUT/'calibracao.png',dpi=160,bbox_inches='tight')
fig_delta.savefig(OUT/'incrementos.png',dpi=160,bbox_inches='tight')
record={'stage':'cancer_subgroup_evaluation_v1','split_source':str(SPLIT_DIR),'source':str(SOURCE),
    'reference_run':str(ABLATION_RUN),'audit_run':str(AUDIT_RUN),
    'training_population':'original_general_train','subgroup_rule':'cancer__history_asof == 1 at origin',
    'test_evaluated':False,'validation_previously_used':True,'individual_exported':False,
    'primary_comparison':['A_history','B_functional'],'primary_metric':'brier',
    'n_boot':N_BOOT,'seed':SEED,'python':sys.version,'pandas':pd.__version__,
    'numpy':np.__version__,'sklearn':sklearn.__version__,'calibration_bins':[0,.05,.1,.2,.4,1],
    'code_sha256':{name:hashlib.sha256((ROOT/'src/hrs_project'/name).read_bytes()).hexdigest()
      for name in ['cancer_evaluation.py','individual_ablation.py','individual_trajectories.py',
                   'reference_models.py','cluster_uncertainty.py']},
    'reference_sha256':hashlib.sha256((ABLATION_RUN/'metricas_validacao.csv').read_bytes()).hexdigest(),
    'audit_sha256':hashlib.sha256((AUDIT_RUN/'resumo_viabilidade.csv').read_bytes()).hexdigest(),
    'split_config_sha256':hashlib.sha256((SPLIT_DIR/'config.json').read_bytes()).hexdigest()}
(OUT/'config.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
(OUT/'_SUCCESS').write_text('ok',encoding='utf-8')
print('AVALIAÇÃO CÂNCER CONCLUÍDA:',OUT)
'''),md('''## Interpretação após execução
Verificar B−A e seu intervalo, D−C como contraste secundário e calibração.
Intervalo contendo zero não prova equivalência; uma diferença de significância entre
população geral e subgrupo não demonstra interação com câncer. Não selecionar vencedor
nem ajustar o modelo nesta validação. Eventuais conclusões sobre grafos exigem uma
comparação posterior que inclua explicitamente atributos relacionais.
''')]
n=nb.v4.new_notebook(cells=cells,metadata=original.metadata)
nb.validate(n)
for cell in cells:
    if cell.cell_type=='code':compile(cell.source,'cell','exec')
nb.write(n,ROOT/'notebooks/00j_avaliacao_cancer.ipynb')
print('00j criado; dados reais não executados.')
