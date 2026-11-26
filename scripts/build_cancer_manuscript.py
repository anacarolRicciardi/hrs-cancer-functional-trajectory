"""Artigo e proveniência a partir de fontes textuais e agregados verificados."""
from pathlib import Path
import csv,json,re,hashlib,math
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
ROOT=Path(__file__).resolve().parents[1]
SPLIT=ROOT/'resultados/painel_inicializado_20261121T145340415825Z/avaliacao_20261121T151622102211Z'
RUN=SPLIT/'grafos_cancer_20261122T174503746571Z'
assert (RUN/'_SUCCESS').exists()
def read(name):
    with (RUN/name).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
metrics=[r for r in read('metricas.csv') if r['scope']=='cancer']
comparisons=[r for r in read('comparacoes.csv') if r['metric']=='brier']
assert len(metrics)==5 and len(comparisons)==6
assert all(int(r['n'])==353 and int(r['events'])==39 for r in metrics)
assert math.isclose(float(comparisons[0]['delta']),.0004901509945153953,abs_tol=1e-12)
assert all(float(r['low'])<0<float(r['high']) for r in comparisons)
names={'B_functional':'B — Histórico funcional','B_pairs':'B + Todos os pares','B_static':'B + Rede estática',
       'B_rolling':'B + Rede móvel','B_expanding':'B + Rede acumulada'}
short={'B_functional':'B','B_pairs':'Pares','B_static':'Estática','B_rolling':'Móvel','B_expanding':'Acumulada'}
def n(value,d=5):return f'{float(value):.{d}f}'.replace('.',',')
def mtable(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
        ['| '+' | '.join(map(str,row))+' |' for row in rows])
source=(ROOT/'docs/cancer/artigo_template.md').read_text(encoding='utf-8')
source=source.replace('{{TABLE_MODELS}}',mtable(['Representação','Informação adicional a B','Rede na validação'],[
 ['B','Nenhuma','Não se aplica'],['Todos os pares','28 produtos binários sem seleção por rede','Não se aplica'],
 ['Estática','Produtos ponderados por phi selecionado em 2000','Janeiro de 2000'],
 ['Móvel','Produtos com phi da última janela de 48 meses','Janeiro de 2013'],
 ['Acumulada','Produtos com phi da última referência acumulada','Janeiro de 2013']]))
source=source.replace('{{TABLE_METRICS}}',mtable(['Modelo','Brier ↓','Log loss ↓','ROC-AUC ↑','AP ↑'],[
 [names[r['model']],n(r['brier']),n(r['log_loss']),n(r['roc_auc'],4),n(r['average_precision'],4)] for r in metrics]))
source=source.replace('{{TABLE_CONTRASTS}}',mtable(['Candidato − referência','Delta Brier','IC95%'],[
 [short[r['candidate']]+' − '+short[r['reference']],n(r['delta']),f"[{n(r['low'])}; {n(r['high'])}]"] for r in comparisons]))
assert '{{' not in source
markdown=re.sub(r'\[\[FIGURE:([^|]+)\|([^\]]+)\]\]',lambda m:
    '!['+m[2]+'](../'+(RUN/'figuras'/f'{m[1]}.png').relative_to(ROOT).as_posix()+')',source)
(ROOT/'docs/ARTIGO_CANCER_GRAFOS.md').write_text(markdown,encoding='utf-8')

doc=Document();sec=doc.sections[0];sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=Cm(2);sec.bottom_margin=Cm(2);sec.left_margin=Cm(2.2);sec.right_margin=Cm(2.2)
for border in doc.styles.element.xpath('.//w:pBdr'):border.getparent().remove(border)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
    s=doc.styles[name];s.font.name='Times New Roman';s.font.size=Pt(11);s.font.color.rgb=RGBColor(0,0,0)
    s.paragraph_format.space_after=Pt(5);s.paragraph_format.line_spacing=1.08;s.paragraph_format.widow_control=True
doc.styles['Normal'].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
doc.styles['Title'].font.size=Pt(19);doc.styles['Title'].font.bold=True
doc.styles['Title'].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER
for name in ['Heading 1','Heading 2']:
    doc.styles[name].font.size=Pt(12);doc.styles[name].font.bold=True
    doc.styles[name].paragraph_format.keep_with_next=True;doc.styles[name].paragraph_format.space_before=Pt(9)
lang=OxmlElement('w:lang');lang.set(qn('w:val'),'pt-BR');doc.styles['Normal'].element.get_or_add_rPr().append(lang)
doc.core_properties.author='Adolfo; Ana Carolina R.; Bruna C.'
doc.core_properties.title=source.splitlines()[0].lstrip('# ')
def rich(par,text):
    for token in re.split(r'(\[[^\]]+\]\([^)]+\)|\*\*.*?\*\*)',text):
        link=re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)',token)
        if link:
            h=OxmlElement('w:hyperlink');h.set(qn('r:id'),par.part.relate_to(link[2],RT.HYPERLINK,is_external=True))
            r=OxmlElement('w:r');t=OxmlElement('w:t');t.text=link[1];r.append(t);h.append(r);par._p.append(h)
        elif token.startswith('**'):par.add_run(token[2:-2]).bold=True
        else:par.add_run(token)
def table(lines):
    rows=[[x.strip() for x in line.strip('|').split('|')] for line in lines]
    rows=[r for r in rows if not all(re.fullmatch('[-: ]+',x) for x in r)]
    count=len(rows[0]);widths=([5.8,2.7,2.7,2.7,2.7] if count==5 else
        [5.0,7.2,4.4] if rows[0][0]=='Representação' else [6.8,3.0,6.8])
    t=doc.add_table(rows=0,cols=count);t.autofit=False
    for col,w in zip(t.columns,widths):col.width=Cm(w)
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','bottom','left','right','insideH','insideV']:
        e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
    t._tbl.tblPr.append(borders)
    for i,data in enumerate(rows):
        row=t.add_row();row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        if i==0:row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
        for j,value in enumerate(data):
            cell=row.cells[j];cell.width=Cm(widths[j]);par=cell.paragraphs[0];rich(par,value)
            par.paragraph_format.space_before=Pt(3);par.paragraph_format.space_after=Pt(3)
            par.alignment=WD_ALIGN_PARAGRAPH.LEFT
            for run in par.runs:run.font.size=Pt(10);run.bold=i==0
            if i==0:
                sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EDF2');cell._tc.get_or_add_tcPr().append(sh)
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
lines=source.splitlines();i=0;front=True
while i<len(lines):
    line=lines[i].strip();i+=1
    if not line:continue
    if line.startswith('# '):doc.add_paragraph(line[2:],style='Title');continue
    if line.startswith('##'):
        front=False;level=1 if line.startswith('## ') else 2
        doc.add_heading(line.lstrip('# '),level);continue
    if line.startswith('[[FIGURE:'):
        match=re.fullmatch(r'\[\[FIGURE:([^|]+)\|(.+)\]\]',line)
        par=doc.add_paragraph();par.paragraph_format.keep_with_next=True
        par.add_run().add_picture(str(RUN/'figuras'/f'{match[1]}.png'),width=Cm(16.6))
        caption=doc.add_paragraph(match[2]);caption.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT
        for run in caption.runs:run.font.size=Pt(9)
        continue
    if line.startswith('|'):
        block=[line]
        while i<len(lines) and lines[i].startswith('|'):block.append(lines[i]);i+=1
        table(block);continue
    par=doc.add_paragraph();rich(par,line)
    if front:
        par.alignment=WD_ALIGN_PARAGRAPH.CENTER
        for run in par.runs:run.font.size=Pt(10)
    if re.match(r'^\d+\. ',line):par.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)
out=ROOT/'entrega_disciplina/Artigo_Cancer_Grafos_Temporais.docx';doc.save(out)
records={}
for label,path in {'00h':SPLIT/'ablacao_individual_20261122T162234840216Z',
 '00i':SPLIT/'viabilidade_cancer_20261122T170924213017Z',
 '00j':SPLIT/'avaliacao_cancer_20261122T173738515878Z','00k':RUN}.items():
    assert (path/'_SUCCESS').exists()
    cfg=json.loads((path/'config.json').read_text(encoding='utf-8'))
    records[label]={'run':str(path.relative_to(ROOT)), 'config':cfg,
        'aggregate_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in path.glob('*.csv')}}
(ROOT/'docs/cancer/PROVENIENCIA.json').write_text(json.dumps(records,indent=2,ensure_ascii=False),encoding='utf-8')
print(out);print('Artigo, Markdown e proveniência gerados; nenhuma execução de microdados.')
