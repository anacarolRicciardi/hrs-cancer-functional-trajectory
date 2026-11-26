"""Painel funcional auditável. Importação não lê microdados."""
import numpy as np
import pandas as pd
from .extraction import missing_value_mask

ADL_ITEMS = ('BATHA', 'DRESSA', 'EATA', 'BEDA', 'WALKRA')
INTERVIEW_CODES = (1, 2)


def adl_state(items):
    """Zero exige cinco negativos válidos; um positivo confirma dificuldade.

    Valores especiais devem ser mascarados antes. Outros códigos são inválidos,
    preservados na contagem de qualidade. Não fornece data de início da limitação.
    """
    if items.shape[1] != 5:
        raise ValueError('Esperados exatamente cinco itens ADL')
    numeric = items.apply(pd.to_numeric, errors='coerce')
    valid = numeric.isin([0, 1])
    positive = (numeric.eq(1) & valid).sum(axis=1)
    count = valid.sum(axis=1)
    state = pd.Series(np.nan, index=items.index, dtype=float)
    state.loc[count.eq(5) & positive.eq(0)] = 0.
    state.loc[positive.gt(0)] = 1.
    return pd.DataFrame({
        'adl_valid_items': count, 'adl_positive_items': positive,
        'adl_invalid_items': (items.notna() & ~valid).sum(axis=1),
        'adl_complete': count.eq(5), 'adl_state': state,
        'adl_sum_complete': positive.where(count.eq(5))
    })


def required_columns(waves):
    return ['HHIDPN', 'HHID'] + [f'R{w}{s}' for w in waves for s in
        (*ADL_ITEMS, 'ADL5A', 'AGEY_E', 'IWSTAT', 'PROXY', 'IWENDY', 'IWENDM')]


def build_panel(wide, waves=range(3, 17), missing_ranges=None):
    missing_ranges = missing_ranges or {}
    waves = list(waves)
    missing = sorted(set(required_columns(waves)) - set(wide.columns))
    if missing:
        raise ValueError(f'Colunas obrigatórias ausentes: {missing}')
    if wide.HHIDPN.isna().any() or wide.HHIDPN.duplicated().any():
        raise ValueError('HHIDPN ausente ou duplicado; não deduplicar automaticamente')
    pieces = []
    names = {'AGEY_E': 'age_end', 'IWSTAT': 'status', 'PROXY': 'proxy',
             'IWENDY': 'year', 'IWENDM': 'month', 'ADL5A': 'adl_rand'}
    for wave in waves:
        p = pd.DataFrame({'id': wide.HHIDPN, 'household_id': wide.HHID, 'wave': wave})
        for suffix in (*ADL_ITEMS, *names):
            col = f'R{wave}{suffix}'
            raw = wide[col]
            p[names.get(suffix, suffix.lower())] = pd.to_numeric(
                raw.mask(missing_value_mask(raw, missing_ranges.get(col, []))), errors='coerce')
        p = pd.concat([p, adl_state(p[[s.lower() for s in ADL_ITEMS]])], axis=1)
        integer_date = p.year.mod(1).eq(0) & p.month.mod(1).eq(0)
        date_valid = p.year.between(1992, 2035) & p.month.between(1, 12) & integer_date
        p['date_valid'] = date_valid
        p['interview_month'] = (p.year * 12 + p.month).where(date_valid)
        p['interview_observed'] = p.status.isin(INTERVIEW_CODES)
        p['eligible_baseline'] = p.interview_observed & p.age_end.ge(50) & p.adl_state.eq(0)
        # Controle documental: zero RAND não equivale necessariamente a zero confirmado.
        p['rand_zero_unconfirmed'] = p.adl_rand.eq(0) & ~p.adl_state.eq(0)
        p['rand_disagreement_complete'] = p.adl_complete & p.adl_rand.notna() & p.adl_rand.ne(p.adl_sum_complete)
        pieces.append(p)
    panel = pd.concat(pieces, ignore_index=True).sort_values(['id', 'wave']).reset_index(drop=True)
    if panel.duplicated(['id', 'wave']).any():
        raise ValueError('Pessoa–onda duplicada')
    return panel


def build_transitions(panel):
    """Preserva elegíveis sem futuro; não confunde lacuna com onda consecutiva."""
    p = panel.sort_values(['id', 'wave']).copy()
    if p.duplicated(['id', 'wave']).any():
        raise ValueError('Pessoa–onda duplicada')
    for name in ['wave', 'status', 'proxy', 'adl_state', 'adl_complete', 'interview_month']:
        p['next_' + name] = p.groupby('id', sort=False)[name].shift(-1)
    p = p[p.eligible_baseline].copy()
    adjacent = p.next_wave.eq(p.wave + 1)
    next_interview = p.next_status.isin(INTERVIEW_CODES)
    p['interval_months'] = (p.next_interview_month - p.interview_month).where(adjacent)
    chronology = p.interval_months.gt(0)
    p['followup'] = np.select(
        [~adjacent, adjacent & p.next_status.isin([5, 6]), adjacent & p.next_status.eq(3),
         adjacent & next_interview & ~chronology,
         adjacent & next_interview & p.next_adl_state.notna(), adjacent & next_interview,
         adjacent & p.next_status.eq(4), adjacent & p.next_status.eq(7)],
        ['no_adjacent_wave', 'death_status_review', 'proxy_death_review', 'calendar_review',
         'observed', 'adl_unknown', 'nonresponse_alive', 'dropped'], default='other_or_unknown')
    p['target'] = p.next_adl_state.where(p.followup.eq('observed'))
    p['target_complete_only'] = p.target.where(p.next_adl_complete.eq(True))
    p['self_response_pair'] = p.proxy.eq(0) & p.next_proxy.eq(0)
    return p


def aggregate_audit(panel, transitions):
    observed = panel[panel.interview_observed]
    quality = observed.groupby('wave').agg(
        interviews=('id', 'size'), eligible=('eligible_baseline', 'sum'),
        complete_adl=('adl_complete', 'sum'), invalid_items=('adl_invalid_items', 'sum'),
        rand_zero_unconfirmed=('rand_zero_unconfirmed', 'sum'),
        rand_disagreement_complete=('rand_disagreement_complete', 'sum'),
        invalid_calendar=('date_valid', lambda s: int((~s).sum())))
    flow = transitions.groupby(['wave', 'followup']).size().rename('n').reset_index()
    events = transitions.groupby('wave').agg(
        eligible=('id', 'size'), observed=('target', 'count'), events=('target', 'sum'),
        observed_complete=('target_complete_only', 'count'), events_complete=('target_complete_only', 'sum'))
    # Sem desfecho observado, zero eventos não deve parecer ausência de risco.
    events['events'] = events.events.where(events.observed.gt(0))
    events['events_complete'] = events.events_complete.where(events.observed_complete.gt(0))
    events['observed_proportion'] = (events.events / events.observed).where(events.observed.ge(20))
    return {'qualidade': quality, 'fluxo': flow, 'eventos': events}
