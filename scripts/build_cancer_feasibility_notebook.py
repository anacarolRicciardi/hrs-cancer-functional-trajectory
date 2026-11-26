"""Gera notebook sem ler dados HRS."""
from pathlib import Path
import nbformat as nb
ROOT=Path(__file__).resolve().parents[1]
md=nb.v4.new_markdown_cell;code=nb.v4.new_code_cell
cells=[md('''# 00i — Viabilidade do experimento sobre câncer e funcionalidade

## Objetivo
Contar o suporte disponível para estudar dificuldade ADL na próxima entrevista em
pessoas com histórico de câncer. **Resultados reais ainda não executados.**
Execute pessoalmente, no kernel `.venv-local`. Não é necessário extrair outra base.
Nenhum modelo será ajustado e nenhum registro individual será exportado.

## Definições
- ADL: atividades básicas da vida diária; elegibilidade exige idade ≥50 e cinco itens negativos na origem.
- Histórico positivo: estado reconstruído até a entrevista, não câncer ativo.
- Novo relato: positivo explícito, negativo utilizável na entrevista observada anterior,
  sem positivo previamente registrado e intervalo de datas válido. Não equivale a incidência clínica.
- Históricos carregados sem evidência atual, desconhecidos e negativos contestados são separados.
- Seguimento preserva categorias do pipeline: `death_status_review` e `proxy_death_review`
  são códigos a revisar, **não óbitos confirmados**. Última onda não é perda de acompanhamento.
- A unidade é pessoa–onda. Pessoas podem contribuir em várias ondas e categorias;
  não some contagens de pessoas entre linhas para obter o total de indivíduos.

## Escopo de desenvolvimento
Mantém domicílios de treino e validação; exclui teste antes da leitura das colunas clínicas.
Treino até onda 11/2012; validação até onda 13/2016. Não consulta ondas posteriores
para recuperar retornos. Origem desde 2000; validação com origem após 2012.
Frequências descritivas sem pesos, sem interpretação populacional ou causal.
'''),code('''from pathlib import Path
from datetime import datetime, timezone
import sys, json, hashlib
import pandas as pd
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'src/hrs_project').is_dir())
sys.path.insert(0,str(ROOT/'src'))
from hrs_project.cancer_feasibility import COLS, aggregate_feasibility
from hrs_project.evaluation_split import partition_group
protocol=json.loads((ROOT/'config/protocolo_teste_piloto_v1.json').read_text(encoding='utf-8'))
SPLIT_DIR=Path(protocol['split_dir'])
config=json.loads((SPLIT_DIR/'config.json').read_text(encoding='utf-8'))
SOURCE=Path(config['source'])
manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
assert manifest.get('history_start')==1 and manifest.get('individual_saved'), 'Use o painel inicializado exportado.'
assert manifest.get('pipeline_version')=='history_initialized_v2'
assert config['train_end_month']==2012*12+12 and config['validation_end_month']==2016*12+12
assert (SPLIT_DIR/'_WORKFLOW_SUCCESS').exists()
print('Python:',sys.executable)
print('Fonte:',SOURCE)
'''),md('''## Carregar apenas o desenvolvimento
As chaves locais servem para filtrar domicílios; não são exibidas nem exportadas.
Os filtros de Parquet excluem teste e ondas posteriores aos tetos antes da auditoria.
'''),code('''files=sorted(SOURCE.glob('painel_*.parquet'))
assert files, 'Nenhum painel encontrado'
parts=[]
for path in files:
    keys=pd.read_parquet(path,columns=['id','household_id']) .drop_duplicates()
    assert not keys.id.duplicated().any(), 'Domicílio variável dentro do bloco'
    partitions=keys.household_id.map(lambda h:partition_group(h,config['seed'],config['fractions']))
    for group,last_wave in [('train',11),('validation',13)]:
        ids=keys.loc[partitions.eq(group),'id'].tolist()
        if ids:
            part=pd.read_parquet(path,columns=COLS,filters=[('id','in',ids),('wave','<=',last_wave)])
            parts.append(part)
panel=pd.concat(parts,ignore_index=True)
assert not panel.duplicated(['id','wave']).any(), 'Pessoas/ondas repetidas entre blocos'
tables=aggregate_feasibility(panel,config)
del panel,parts,keys
display(tables['resumo_viabilidade'])
'''),md('''## Novos relatos e perdas
`novos_relatos_e_adl` contém somente origens elegíveis sem dificuldade funcional.
`entrevistas_por_onda` também conta novos relatos em pessoas com ADL positiva ou desconhecida.
Ausência de uma categoria na tabela significa ausência de linhas, não uma estimativa de risco zero.
'''),code('''display(tables['novos_relatos_e_adl'])
display(tables['seguimento'].groupby(['group','followup'],as_index=False).transitions.sum())
display(tables['evidencia_cancer'])
'''),md('''## Suporte por onda
O gráfico mostra transições observadas e eventos ADL, não prevalência populacional.
Ondas sem origens elegíveis não aparecem; zero evento só é interpretável com denominador observado.
'''),code('''import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(12,4))
data=tables['transicoes_por_onda']
for ax,group in zip(axes,['train','validation']):
    s=data[data.group.eq(group)&data.cancer_group.eq('historico_positivo')]
    if s.empty:
        ax.text(.5,.5,'Sem transições elegíveis',ha='center',transform=ax.transAxes)
    else:
        ax.bar(s.wave-.18,s.observed,width=.36,label='Desfecho observado')
        ax.bar(s.wave+.18,s.events_adl,width=.36,label='Evento ADL')
        ax.legend()
    ax.set(title=group+' — histórico de câncer',xlabel='Onda de origem',ylabel='Transições')
    ax.set_ylim(bottom=0)
fig.tight_layout();plt.show()
'''),md('''## Salvar somente agregados
Pasta nova, sem alterar resultados anteriores. `config.json` registra versões e hashes.
Antes de compartilhar resultados, revise regras institucionais sobre células pequenas.
'''),code('''OUT=SPLIT_DIR/('viabilidade_cancer_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
OUT.mkdir(exist_ok=False)
for name,frame in tables.items():frame.to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig')
fig.savefig(OUT/'suporte_por_onda.png',dpi=160,bbox_inches='tight')
record={'stage':'cancer_feasibility_v1','source':str(SOURCE),'split_source':str(SPLIT_DIR),
        'test_evaluated':False,'models_fitted':False,'individual_exported':False,
        'python':sys.version,'pandas':pd.__version__,'anchor':24001,
        'wave_caps':{'train':11,'validation':13},'source_blocks':len(files),
        'code_sha256':{n:hashlib.sha256((ROOT/'src/hrs_project'/n).read_bytes()).hexdigest()
          for n in ['cancer_feasibility.py','functional_panel.py','evaluation_split.py']},
        'split_config_sha256':hashlib.sha256((SPLIT_DIR/'config.json').read_bytes()).hexdigest()}
(OUT/'config.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
(OUT/'_SUCCESS').write_text('ok',encoding='utf-8')
print('VIABILIDADE CÂNCER CONCLUÍDA:',OUT)
'''),md('''## Próxima decisão
Revisar pessoas e domicílios distintos, eventos e não eventos em treino/validação,
novos relatos e proporções de seguimento desconhecido. Não há limiar automático que
prove suficiência amostral. Se o suporte for pequeno, começar com descrição ou avaliação
do modelo atual no subgrupo; se adequado, planejar comparação incremental com calibração
e incerteza por domicílio. Esta auditoria não demonstra efeito do câncer, benefício de
tratamentos nem valor clínico de grafos. Tipos de tumor, estágio e tratamentos não foram extraídos.
''')]
n=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python (.venv-local)','language':'python','name':'python3'}})
nb.validate(n)
for c in cells:
    if c.cell_type=='code':compile(c.source,'cell','exec')
nb.write(n,ROOT/'notebooks/00i_viabilidade_cancer.ipynb')
print('00i criado; dados reais não executados.')
