"""História de relatos construída para frente; não é diagnóstico clínico.

Regras conservadoras baseadas no codebook RAND 2022 V2, pp. 534–536.
As séries ever corrigidas retrospectivamente não são usadas.
"""
import numpy as np
import pandas as pd
from .extraction import missing_value_mask

DISEASES = {'hypertension':'HIBP', 'diabetes':'DIAB', 'cancer':'CANCR',
            'lung':'LUNG', 'heart':'HEART', 'stroke':'STROK',
            'psychiatric':'PSYCH', 'arthritis':'ARTHR'}
EVER_QUESTION = {1, 5, 10, 11}
SINCE_QUESTION = {2, 6, 12, 15, 18, 19}


def interpret_response(raw, wording, wave, disease, include_tia=True):
    """Evento de evidência, não binarização indiscriminada dos códigos."""
    if pd.isna(raw):
        return 'missing'
    if raw == 1:
        return 'positive'
    if raw == 2:
        return 'positive_tia' if disease == 'stroke' and include_tia else 'review_code_2'
    if raw == 3:
        return 'positive_dispute' if 5 <= wave <= 13 else 'review_code_3'
    if raw == 4:
        return 'denies_ever' if wave >= 14 else 'dispute_history_uncertain'
    if raw == 5:
        return 'dispute_history_uncertain'
    if raw == 6:
        if wave >= 14:
            return 'past_condition_not_current'
        if wave == 4 and disease == 'heart':
            return 'preload_heart_history'
        return 'review_code_6'
    if raw == 0:
        if wording in EVER_QUESTION:
            return 'denies_ever'
        if wording in SINCE_QUESTION:
            return 'no_new_report'
        return 'review_negative_wording'
    return 'review_unrecognized_code'


def history_for_person(records, include_tia=True):
    """Um participante/condição. Preserva história conhecida e idade da evidência."""
    if records.wave.duplicated().any():
        raise ValueError('Ondas duplicadas')
    state, last_evidence, any_positive = np.nan, np.nan, False
    rows = []
    for row in records.sort_values('wave').itertuples():
        event = interpret_response(row.raw, row.wording, row.wave, row.disease, include_tia) if row.interview else 'no_interview'
        old = state
        if event in ['positive', 'positive_tia', 'positive_dispute', 'past_condition_not_current', 'preload_heart_history']:
            state, last_evidence, any_positive = 1., row.wave, True
        elif event == 'denies_ever':
            state, last_evidence = 0., row.wave
        elif event == 'dispute_history_uncertain' or event.startswith('review_'):
            state, last_evidence = np.nan, np.nan
        elif event == 'no_new_report' and pd.notna(state):
            # Não ter novo relato não apaga um diagnóstico previamente relatado.
            last_evidence = row.wave
        # missing/no_interview: conserva apenas o último estado conhecido, rotulado como carry.
        rows.append({'wave':row.wave, 'evidence':event, 'history_asof':state,
                     'ever_positive_recorded':int(any_positive),
                     'carried_without_current_evidence':event in ['missing','no_interview'],
                     'waves_since_evidence':row.wave-last_evidence if pd.notna(last_evidence) else np.nan,
                     'changed_known_state':pd.notna(old) and pd.notna(state) and old != state,
                     'tia_report':event in ['positive_tia','review_code_2'] and row.disease == 'stroke'})
    return pd.DataFrame(rows)


def build_disease_history(wide, waves=range(3,17), missing_ranges=None, include_tia=True):
    if wide.HHIDPN.isna().any() or wide.HHIDPN.duplicated().any():
        raise ValueError('HHIDPN deve ser único e não ausente')
    missing_ranges = missing_ranges or {}
    frames = []
    for disease, suffix in DISEASES.items():
        for wave in waves:
            cols = [f'R{wave}{suffix}', f'R{wave}{suffix}Q', f'R{wave}IWSTAT']
            if any(c not in wide for c in cols):
                raise ValueError(f'Colunas necessárias ausentes para {disease}, onda {wave}')
            values = [pd.to_numeric(wide[c].mask(missing_value_mask(wide[c],missing_ranges.get(c,[]))),errors='coerce') for c in cols]
            frames.append(pd.DataFrame({'id':wide.HHIDPN, 'disease':disease, 'wave':wave,
                                        'raw':values[0], 'wording':values[1], 'interview':values[2].isin([1,2])}))
    long = pd.concat(frames,ignore_index=True)
    output = []
    for (person, disease), frame in long.groupby(['id','disease'],sort=False):
        result = history_for_person(frame,include_tia)
        result['id'],result['disease'] = person,disease
        output.append(result)
    return pd.concat(output,ignore_index=True) if output else pd.DataFrame()
