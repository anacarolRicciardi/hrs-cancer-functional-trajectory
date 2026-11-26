"""Auditoria agregada, sem ajustar modelos ou estimar incidência de câncer."""
import numpy as np
import pandas as pd
from .functional_panel import build_transitions
from .evaluation_split import partition_group

COLS = ['id','household_id','wave','status','proxy','age_end','adl_state',
        'adl_complete','interview_month','interview_observed','eligible_baseline',
        'cancer__history_asof','cancer__ever_positive_recorded',
        'cancer__carried_without_current_evidence','cancer__evidence']


def classify_cancer(panel):
    p=panel.sort_values(['id','wave']).copy().reset_index(drop=True)
    if p[['id','wave']].isna().any().any() or p.duplicated(['id','wave']).any():
        raise ValueError('Chaves inválidas ou duplicadas')
    for col in ['interview_observed','cancer__carried_without_current_evidence']:
        if not p[col].isin([True,False]).all():raise ValueError(f'Indicador inválido: {col}')
    for col in ['cancer__history_asof','cancer__ever_positive_recorded']:
        if not p[col].dropna().isin([0,1]).all():raise ValueError(f'Estado inválido: {col}')
    s=p.cancer__history_asof
    p['cancer_group']=np.select([s.eq(1),s.eq(0)&p.cancer__ever_positive_recorded.eq(0),
        s.eq(0)&p.cancer__ever_positive_recorded.eq(1)],
        ['historico_positivo','negativo_sem_positivo_previo','negativo_com_positivo_previo'],default='desconhecido')
    p['new_report']=False
    v=p[p.interview_observed].copy()
    state=v.cancer__history_asof.where(~v.cancer__carried_without_current_evidence)
    prev=state.groupby(v.id).shift()
    prev_ever=v.cancer__ever_positive_recorded.groupby(v.id).shift()
    gap=v.interview_month-v.interview_month.groupby(v.id).shift()
    new=(state.eq(1)&prev.eq(0)&prev_ever.eq(0)&gap.gt(0)&v.cancer__evidence.eq('positive'))
    p.loc[v.index,'new_report']=new
    # A classificação utiliza apenas o passado. Novos relatos não são datas de diagnóstico.
    p['first_observed_in_panel']=False
    p.loc[v.index,'first_observed_in_panel']=v.groupby('id').cumcount().eq(0)
    return p


def aggregate_feasibility(panel, config, anchor=24001):
    """Painel de desenvolvimento pré-filtrado; teste nunca entra nos agregados.

    Cada grupo usa seu teto de ondas (11/2012; 13/2016). Isso preserva estados
    sem data, inclusive perdas, sem consultar as ondas posteriores para achar retornos.
    """
    required=set(COLS)-set(panel.columns)
    if required:raise ValueError(f'Colunas ausentes: {sorted(required)}')
    if panel.groupby('id').household_id.nunique(dropna=False).gt(1).any():
        raise ValueError('Domicílio variável por pessoa')
    p=classify_cancer(panel)
    p['group']=p.household_id.map(lambda h:partition_group(h,config['seed'],config['fractions']))
    if p.group.eq('test').any():raise ValueError('Filtre domicílios de teste antes da auditoria')
    visits=[]; transitions=[]
    for group,last_wave,end in [('train',11,config['train_end_month']),('validation',13,config['validation_end_month'])]:
        q=p[p.group.eq(group)&p.wave.le(last_wave)].copy()
        v=q[q.interview_observed&q.age_end.ge(50)&q.interview_month.ge(anchor)&q.interview_month.le(end)].copy()
        if group=='validation':v=v[v.interview_month.gt(config['train_end_month'])]
        visits.append(v)
        t=build_transitions(q)
        t=t[t.interview_month.ge(anchor)&t.interview_month.le(end)].copy()
        if group=='validation':t=t[t.interview_month.gt(config['train_end_month'])]
        outside=t.next_interview_month.gt(end)
        t.loc[outside,'followup']='outside_time_window'
        t.loc[outside,'target']=np.nan
        transitions.append(t)
    v=pd.concat(visits,ignore_index=True);t=pd.concat(transitions,ignore_index=True)
    def summarize(frame,keys):
        a=frame.assign(event=frame.target.eq(1),nonevent=frame.target.eq(0),observed=frame.target.notna())
        out=a.groupby(keys,dropna=False).agg(transitions=('id','size'),people=('id','nunique'),
            households=('household_id','nunique'),observed=('observed','sum'),events_adl=('event','sum'),
            nonevents_adl=('nonevent','sum'),new_reports=('new_report','sum')).reset_index()
        out['unknown_outcome']=out.transitions-out.observed
        out['event_fraction']=out.events_adl.div(out.observed.where(out.observed.gt(0)))
        assert (out.events_adl+out.nonevents_adl).eq(out.observed).all()
        return out
    tables={
        'entrevistas_por_onda':v.groupby(['group','wave','cancer_group'],dropna=False).agg(
            interviews=('id','size'),people=('id','nunique'),new_reports=('new_report','sum'),
            carried=('cancer__carried_without_current_evidence','sum'),
            first_in_panel=('first_observed_in_panel','sum')).reset_index(),
        'transicoes_por_onda':summarize(t,['group','wave','cancer_group']),
        'resumo_viabilidade':summarize(t,['group','cancer_group']),
        'seguimento':t.groupby(['group','wave','cancer_group','followup'],dropna=False).agg(
            transitions=('id','size'),people=('id','nunique')).reset_index(),
        'novos_relatos_e_adl':summarize(t[t.new_report],['group']),
        'evidencia_cancer':v.groupby(['group','cancer__evidence'],dropna=False).size().rename('interviews').reset_index(),
    }
    # Distintos por grupo, não soma de pessoas por onda. Pessoas podem mudar de categoria.
    assert tables['seguimento'].transitions.sum()==tables['resumo_viabilidade'].transitions.sum()
    return tables
