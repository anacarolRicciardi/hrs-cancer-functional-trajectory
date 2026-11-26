"""Integração estrita por pessoa e onda; separa atributos e futuro."""
import pandas as pd
from .functional_panel import required_columns, build_panel, build_transitions
from .disease_history import DISEASES, build_disease_history

HISTORY_FIELDS = ['history_asof', 'ever_positive_recorded',
                  'carried_without_current_evidence', 'waves_since_evidence', 'evidence']


def history_waves(waves, history_start=None):
    waves=list(waves)
    if not waves or sorted(set(waves))!=waves:
        raise ValueError('Ondas devem ser únicas e ordenadas')
    start=min(waves) if history_start is None else history_start
    if not isinstance(start,int) or start<1 or start>min(waves):
        raise ValueError('Início histórico inválido')
    return list(range(start,max(waves)+1))


def integrated_columns(waves, history_start=None):
    waves = list(waves)
    historical=history_waves(waves,history_start)
    return list(dict.fromkeys(required_columns(waves) +
        [f'R{w}{suffix}{q}' for w in historical for suffix in DISEASES.values() for q in ['', 'Q']] +
        [f'R{w}IWSTAT' for w in historical]))


def join_history(panel, history):
    keys = ['id', 'wave']
    if panel[keys].isna().any().any() or panel.duplicated(keys).any():
        raise ValueError('Chave pessoa–onda inválida no painel')
    if history[keys+['disease']].isna().any().any() or history.duplicated(keys+['disease']).any():
        raise ValueError('Chave pessoa–onda–doença inválida')
    if set(history.disease.unique()) != set(DISEASES):
        raise ValueError('Conjunto de doenças incompleto ou inesperado')
    expected = pd.MultiIndex.from_frame(panel[keys])
    result = panel.copy()
    for disease in DISEASES:
        part = history[history.disease.eq(disease)][keys+HISTORY_FIELDS]
        actual = pd.MultiIndex.from_frame(part[keys])
        if len(expected.difference(actual)) or len(actual.difference(expected)):
            raise ValueError(f'Chaves não coincidem para {disease}')
        part = part.rename(columns={c:f'{disease}__{c}' for c in HISTORY_FIELDS})
        result = result.merge(part, on=keys, how='left', validate='one_to_one')
    return result.sort_values(keys).reset_index(drop=True)


def feature_columns():
    # Lista positiva: nunca selecionar automaticamente todas as colunas numéricas.
    return ['age_end', 'proxy'] + [f'{d}__{f}' for d in DISEASES for f in HISTORY_FIELDS if f != 'evidence']


def separate_supervised(panel):
    transitions = build_transitions(panel)
    keys = ['id', 'wave']
    features = transitions[keys+['household_id']+feature_columns()].copy()
    outcomes = transitions[keys+['target','target_complete_only','followup','interval_months','self_response_pair']].copy()
    assert features[keys].equals(outcomes[keys])
    return features, outcomes


def graph_view(panel):
    """Somente entrevistas 50+, estados com evidência atual; mantém desconhecidos."""
    p = panel[panel.interview_observed & panel.age_end.ge(50)].copy()
    out = p[['id','wave','adl_state']].copy()
    for disease in DISEASES:
        carried = p[f'{disease}__carried_without_current_evidence']
        value = p[f'{disease}__history_asof']
        out[disease] = value.where(~carried)
        out[f'{disease}__observed'] = out[disease].notna()
    return out


def integrate_block(wide, waves=range(3,17), missing_ranges=None, include_tia=True, history_start=None):
    waves=list(waves)
    panel = build_panel(wide,waves,missing_ranges)
    history = build_disease_history(wide,history_waves(waves,history_start),missing_ranges,include_tia)
    history = history[history.wave.isin(waves)]
    integrated = join_history(panel,history)
    features,outcomes = separate_supervised(integrated)
    return integrated,features,outcomes,graph_view(integrated)
