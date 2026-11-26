"""Atributos individuais prospectivos. Não lê alvos nem estima início biológico."""
import numpy as np
import pandas as pd
from .disease_history import DISEASES
from .graph_interactions import observed_states, all_pairs


def input_columns():
    return ['id','wave','interview_month','interview_observed','adl_state'] + [
        f'{d}__{f}' for d in DISEASES for f in
        ['history_asof','carried_without_current_evidence','ever_positive_recorded']]


def build_individual_trajectories(panel):
    """Uma linha por entrevista observada. Usa somente a própria pessoa até a onda.

    Mudança exige estados utilizáveis nas duas entrevistas e intervalo válido.
    Ordem usa apenas primeiros positivos cuja ausência anterior foi observada;
    condições já positivas no início do painel não recebem data de início.
    """
    p=panel[input_columns()].copy()
    if p[['id','wave']].isna().any().any() or p.duplicated(['id','wave']).any():
        raise ValueError('Chaves individuais ausentes ou duplicadas')
    if not p.interview_observed.isin([True,False]).all():
        raise ValueError('Indicador de entrevista inválido')
    if not p.adl_state.dropna().isin([0,1]).all():
        raise ValueError('Estado ADL inválido')
    p=p[p.interview_observed].sort_values(['id','wave']).reset_index(drop=True)
    if p.empty: raise ValueError('Nenhuma entrevista observada')
    m=p.interview_month
    if not np.isfinite(m.dropna()).all() or m.dropna().mod(1).ne(0).any():
        raise ValueError('Calendário inválido')
    last_known=m.groupby(p.id).ffill().groupby(p.id).shift()
    if (m.notna() & last_known.notna() & m.le(last_known)).any():
        raise ValueError('Calendário não crescente por pessoa')
    prev_month=m.groupby(p.id).shift()
    gap=m-prev_month
    valid_time=gap.gt(0)
    states=observed_states(p)
    prev=states.groupby(p.id).shift()
    comparable=states.notna() & prev.notna()
    comparable=comparable.mul(valid_time,axis=0).astype(bool)
    features={
        'individual__previous_interviews':p.groupby('id').cumcount().astype(float),
        'individual__interval_months':gap.where(valid_time),
        'individual__wave_gap':(p.wave-p.wave.groupby(p.id).shift()).where(valid_time),
        'individual__known_conditions':states.notna().sum(axis=1).astype(float),
        'individual__positive_conditions':states.sum(axis=1,min_count=len(DISEASES)),
        'individual__comparable_conditions':comparable.sum(axis=1).astype(float),
        'individual__previous_adl':p.adl_state.groupby(p.id).shift().where(valid_time),
    }
    # Histórico funcional anterior; desconhecido não conta como ausência de limitação.
    positives=p.adl_state.eq(1).groupby(p.id).cumsum()-p.adl_state.eq(1)
    known=p.adl_state.notna().groupby(p.id).cumsum()-p.adl_state.notna()
    features['individual__prior_adl_positive']=positives.gt(0).astype(float).where(known.gt(0))
    first_times={}
    new_conditions=[]
    for d in DISEASES:
        ever=p[f'{d}__ever_positive_recorded']
        if not ever.isin([0,1]).all(): raise ValueError('Histórico positivo inválido')
        previous_ever=ever.groupby(p.id).shift()
        new=(states[d].eq(1)&prev[d].eq(0)&previous_ever.eq(0)).astype(float).where(comparable[d])
        features[f'individual__new_record__{d}']=new
        features[f'individual__persistent_pair_of_visits__{d}']=(states[d].eq(1)&prev[d].eq(1)).astype(float).where(comparable[d])
        new_conditions.append(new)
        # Nunca usa mínimos calculados a partir de entrevistas futuras.
        first_times[d]=m.where(new.eq(1)).groupby(p.id).cummin().groupby(p.id).ffill()
    new_frame=pd.concat(new_conditions,axis=1)
    features['individual__new_records_complete']=new_frame.sum(axis=1,min_count=len(DISEASES))
    features['individual__new_records_per_year']=features['individual__new_records_complete']/(gap/12).where(valid_time)
    for a,b in all_pairs():
        valid=comparable[a]&comparable[b]
        current=states[a]*states[b]; previous=prev[a]*prev[b]
        features[f'individual_pair__new__{a}__{b}']=(current.eq(1)&previous.eq(0)).astype(float).where(valid)
        features[f'individual_pair__established__{a}__{b}']=(current.eq(1)&previous.eq(1)).astype(float).where(valid)
        ta,tb=first_times[a],first_times[b]
        both=ta.notna()&tb.notna()&current.eq(1)&m.notna()
        # +1: a registrado antes de b; -1: inverso; 0: mesma entrevista.
        features[f'individual_pair__observed_order__{a}__{b}']=np.sign(tb-ta).where(both)
    return pd.concat([p[['id','wave']],pd.DataFrame(features)],axis=1)


def case_timeline(panel, person_id, wave):
    """Visão local até a entrevista escolhida; nunca retorna futuro ou desfecho."""
    p=panel[input_columns()]
    current=p[p.id.eq(person_id)&p.wave.eq(wave)]
    if len(current)!=1 or pd.isna(current.interview_month.iloc[0]):
        raise ValueError('Entrevista de origem inválida')
    month=current.interview_month.iloc[0]
    history=p[p.id.eq(person_id)&p.wave.le(wave)&p.interview_month.le(month)&p.interview_observed].sort_values('wave')
    states=observed_states(history)
    out=history[['wave','interview_month','adl_state']].copy()
    for d in DISEASES: out[d]=states[d]
    return out.reset_index(drop=True)
