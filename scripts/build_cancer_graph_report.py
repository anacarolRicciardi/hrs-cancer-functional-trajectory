"""Dossiê Word editável com figuras reais do 00k; lê apenas agregados."""
from pathlib import Path
import csv,json,sys
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
RUN=Path(sys.argv[1]).resolve();ROOT=Path(__file__).resolve().parents[1]
FIG=RUN/'figuras';summary=json.loads((FIG/'summary.json').read_text(encoding='utf-8'))
def rows(name):
    with (RUN/name).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
metrics=[r for r in rows('metricas.csv') if r['scope']=='cancer']
contrasts=[r for r in rows('comparacoes.csv') if r['metric']=='brier']
support=[r for r in rows('suporte.csv') if r['split']=='validation'][0]
config=json.loads((RUN/'config.json').read_text(encoding='utf-8'))
names={'B_functional':'Histórico funcional','B_pairs':'+ Todos os pares','B_static':'+ Rede estática',
       'B_rolling':'+ Rede móvel','B_expanding':'+ Rede acumulada'}
def num(v,n=5):return f'{float(v):.{n}f}'.replace('.',',')
def pct(v):return num(float(v)*100,2)+'%'
doc=Document();sec=doc.sections[0]
sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=Cm(1.8);sec.bottom_margin=Cm(1.8);sec.left_margin=Cm(2);sec.right_margin=Cm(2)
for border in doc.styles.element.xpath('.//w:pBdr'):border.getparent().remove(border)
for style in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
    s=doc.styles[style];s.font.name='Calibri';s.font.size=Pt(11);s.font.color.rgb=RGBColor(0,0,0)
    s.paragraph_format.space_after=Pt(6);s.paragraph_format.line_spacing=1.08
doc.styles['Title'].font.size=Pt(28);doc.styles['Title'].font.bold=True
for name in ['Heading 1','Heading 2']:
    doc.styles[name].font.size=Pt(16 if name=='Heading 1' else 12)
    doc.styles[name].paragraph_format.space_before=Pt(9)
    doc.styles[name].paragraph_format.keep_with_next=True
doc.core_properties.title='Grafos de multimorbidade e vulnerabilidade funcional no câncer'
doc.core_properties.author='Adolfo; Ana Carolina R.; Bruna C.'
def p(text,bold=False):
    r=doc.add_paragraph().add_run(text);r.bold=bold
    return r
def h(text):doc.add_heading(text,1)
def page(title):doc.add_page_break();h(title)
def pic(name,caption):
    par=doc.add_paragraph();par.paragraph_format.keep_with_next=True
    par.add_run().add_picture(str(FIG/f'{name}.png'),width=Cm(17))
    r=p(caption);r.font.size=Pt(9)
def table(headers,values,widths):
    t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
    for col,width in zip(t.columns,widths):col.width=Cm(width)
    for j,x in enumerate(headers):t.rows[0].cells[j].text=x
    for row in values:
        cells=t.add_row().cells
        for j,x in enumerate(row):cells[j].text=str(x)
    for i,row in enumerate(t.rows):
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        if i==0:row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
        for j,cell in enumerate(row.cells):
            cell.width=Cm(widths[j]);pr=cell._tc.get_or_add_tcPr()
            margins=OxmlElement('w:tcMar')
            for side in ['top','bottom','left','right']:
                v=OxmlElement('w:'+side);v.set(qn('w:w'),'85');v.set(qn('w:type'),'dxa');margins.append(v)
            pr.append(margins)
            for par in cell.paragraphs:
                par.paragraph_format.space_after=Pt(1)
                for run in par.runs:
                    run.font.size=Pt(10);run.bold=i==0
                    if i==0:run.font.color.rgb=RGBColor(255,255,255)
            if i==0:
                sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'132E46');pr.append(sh)
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','bottom','left','right','insideH','insideV']:
        v=OxmlElement('w:'+edge);v.set(qn('w:val'),'single');v.set(qn('w:sz'),'4');v.set(qn('w:color'),'D9D9D9');borders.append(v)
    t._tbl.tblPr.append(borders);doc.add_paragraph().paragraph_format.space_after=Pt(1)

header=sec.header.paragraphs[0];header.text='HRS  /  SÉRIES TEMPORAIS  /  EXPERIMENTO 00k'
for r in header.runs:r.font.size=Pt(9);r.font.color.rgb=RGBColor.from_string('647482')
footer=sec.footer.paragraphs[0];footer.text='Pesquisa exploratória • 22 novembro 2026   |   '
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
for r in footer.runs:r.font.size=Pt(9)

doc.add_paragraph('Grafos de multimorbidade\ne vulnerabilidade funcional\nno câncer',style='Title')
p('Experimento temporal com controle do histórico funcional',True)
p('Adolfo • Ana Carolina R. • Bruna C. • [quarto integrante]')
p('SCC5977 — Aprendizado de Máquina para Séries Temporais\nProf. Dr. Diego Furtado Silva\nDepartamento de Ciência da Computação · ICMC · Universidade de São Paulo\nSão Carlos, 2026')
h('Resumo executivo')
if summary['primary_conclusive_gain']:verdict='A rede móvel apresentou ganho no Brier neste contraste exploratório.'
elif summary['primary_conclusive_worse']:verdict='A rede móvel apresentou piora no Brier neste contraste exploratório.'
else:verdict='A rede móvel não demonstrou ganho conclusivo além do histórico funcional.'
p(verdict,True)
p(f"A diferença principal foi {num(summary['primary_delta'])} no Brier, com IC95% de {num(summary['primary_low'])} a {num(summary['primary_high'])}. Valores negativos favorecem a rede. O intervalo descreve a incerteza condicional aos modelos e redes ajustados; não é uma avaliação clínica. [1–2]")
p(f"Validação: {support['people']} pessoas, {support['households']} domicílios, {support['transitions']} transições e {support['events']} eventos ADL. Os cinco modelos usam o mesmo treino geral e o mesmo subgrupo. [1]")
table(['Modelo','Brier ↓','ROC-AUC ↑','AP ↑'],[[names[r['model']],num(r['brier']),num(r['roc_auc'],4),num(r['average_precision'],4)] for r in metrics],[7.1,3.3,3.3,3.3])
p('AP = average precision. Frequência observada de ADL: '+pct(metrics[0]['event_rate'])+'. Não escolher um vencedor apenas pela menor estimativa pontual.',False)
p('ADL = atividades básicas da vida diária. Brier = erro quadrático das probabilidades (menor é melhor). ROC-AUC = discriminação entre eventos e não eventos. IC95% = intervalo de confiança de 95%.')

page('As redes mostram associações entre condições')
pic('01_redes','Figura 1 · Mesmas posições em 2000 e 2013. As redes usam uma entrevista anterior por pessoa da referência de treino. O tamanho/destaque do câncer é editorial; não mede risco. Linhas representam associação, não transmissão nem causalidade. [3]')
p(f"No corte de 2000 há {summary['networks'][0]['selected_edges']} arestas selecionadas; em 2013, {summary['networks'][1]['selected_edges']}. Arestas diretamente ligadas ao câncer: {summary['networks'][0]['cancer_edges']} e {summary['networks'][1]['cancer_edges']}, respectivamente.")
pic('02_cancer_tempo','Figura 2 · Phi entre câncer e cada outra condição, nos 14 cortes anuais. Células sem suporte ficam ausentes; ponto preto indica seleção pelo limiar. A escala é comum a todos os anos. [3]')
p(f"Maior |phi| observado nesses pares: {num(summary['max_abs_cancer_phi'],3)}. A seleção ocorreu em {summary['cancer_selected_rows']} dos {summary['cancer_assessable_rows']} pares–cortes avaliáveis. Não seleção pelo limiar não equivale a ausência de relação clínica.")
p('Câncer–artrite ultrapassou o limiar em 2012 e 2013. Phi não foi ajustado por idade ou coorte; cruzar o limiar não prova que uma relação clínica surgiu nesses anos. ADL é o alvo do modelo, não um nó destas redes.')

page('O ganho preditivo precisa superar os controles')
pic('03_comparacoes','Figura 3 · Diferenças pareadas no subgrupo com câncer. Destaque: comparação principal. IC95% percentil por 1.000 reamostragens de domicílios. A linha tracejada marca zero; cruzá-la não prova equivalência. [2]')
short={'B_functional':'Histórico','B_pairs':'Pares','B_static':'Estática','B_rolling':'Móvel','B_expanding':'Acumulada'}
table(['Candidato − referência','Delta Brier','IC95%'],[[short[r['candidate']]+' − '+short[r['reference']],num(r['delta']),f"[{num(r['low'])}; {num(r['high'])}]"] for r in contrasts],[7.2,3.0,6.8])
p('Por que esses controles importam',True)
p('Todos os pares verifica se o ganho vem apenas de permitir interações. A rede estática controla a representação relacional sem atualização histórica. A comparação com o histórico funcional exige que o grafo acrescente informação além da memória de dificuldades anteriores.')
p('A rede estática de 2000 é antiga por desenho. A comparação temporal pode refletir mudança de composição e atualização da referência, não superioridade geral de algoritmos dinâmicos. Os pesos phi constantes podem ser absorvidos pela padronização.')

page('Calibração e interpretação para a saúde')
pic('04_calibracao','Figura 4 · Probabilidade média prevista versus frequência de ADL em faixas fixas. Diagonal = igualdade. * indica menos de 20 transições; pontos não têm IC e não sustentam decisões individuais. [4]')
table(['Modelo','Média prevista','Frequência observada'],[[names[r['model']],pct(r['mean_prediction']),pct(r['event_rate'])] for r in metrics],[7.1,4.9,5.0])
p('O que este piloto permite dizer',True)
p('Ele testa se uma representação explícita das relações entre doenças melhora a previsão funcional em pessoas com histórico de câncer. Mesmo quando as redes são visualmente compreensíveis, seu valor preditivo precisa ser demonstrado por comparação pareada.')
p('O que ainda não foi demonstrado',True)
p('Não há efeito causal do câncer ou de tratamento estimado, avaliação prospectiva clínica, validação externa ou benefício de decisão médica. O subgrupo reúne históricos de câncer; não identifica doença ativa, estágio ou tipo de tumor. A utilidade de explicar trajetórias a profissionais requer um estudo próprio.')

page('Método e rastreabilidade')
table(['Elemento','Definição'],[
 ['População de ajuste','Treino geral: 49.389 transições. Sem ajuste exclusivo para câncer.'],
 ['Desfecho','Alguma dificuldade ADL na próxima entrevista, entre origens com cinco itens negativos e idade ≥50.'],
 ['Modelos','Regressão logística C=1; mediana, indicadores de ausência e padronização ajustados no treino.'],
 ['Grafos','8 condições e 28 pares; phi; mínimo de 100 pares observados, cobertura 50% e |phi| ≥0,10.'],
 ['Tempo','Cortes anuais 2000–2013. Janela móvel de 48 meses ou acumulada. Validação: rede congelada em janeiro/2013.'],
 ['Controle de informação','Sem desfechos na estimação das redes; fontes anteriores ao corte. Pessoas e domicílios separados entre treino e validação.'],
 ['Incerteza','1.000 réplicas por domicílio; sem reajuste dos modelos ou reestimação das redes; sem correção por multiplicidade.'],
 ['Escopo','Validação já utilizada, análise exploratória, sem pesos amostrais e sem ajuste causal das associações. Não é GNN e não consulta teste.']],[4.0,13.0])
p('Fontes locais e arquivos verificáveis',True)
p('[1] metricas.csv e suporte.csv. [2] comparacoes.csv e intervalos_absolutos.csv. [3] arestas_temporais.csv e auditoria_redes.csv, provenientes do 00b. [4] calibracao.csv. Todos são agregados da mesma execução 00k.')
p('Execução: '+RUN.name)
p('Notebook: notebooks/00k_grafos_cancer.ipynb. Configuração e hashes: config.json. Controle de sucesso: _SUCCESS. Figuras reproduzíveis em PNG e SVG; tabelas e texto deste documento são editáveis.')
p('Próximo passo científico',True)
p('Manter o resultado deste contraste, sem procurar limiares que o tornem favorável. Uma nova representação deve ter justificativa metodológica, protocolo separado e avaliação independente. Validar óbito e perdas e ampliar a precisão são prioridades antes de alegar utilidade clínica.')
OUT=ROOT/'entrega_disciplina';OUT.mkdir(exist_ok=True)
target=OUT/'Dossie_Grafos_Cancer.docx';doc.save(target)
print(target)
