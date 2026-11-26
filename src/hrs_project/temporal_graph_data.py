"""Grafos de prefixos individuais, sem PyTorch, ajuste ou acesso a arquivos."""
import numpy as np
import pandas as pd
from .disease_history import DISEASES

DISEASE_NAMES = tuple(DISEASES)
VISIT_FIELDS = ('age_end', 'proxy', 'adl_state', 'interview_month', 'gap_months', 'gap_waves')
CONDITION_FIELDS = ('history_asof', 'ever_positive_recorded',
                    'carried_without_current_evidence', 'waves_since_evidence')
EVIDENCE = ('UNKNOWN', 'positive', 'positive_tia', 'positive_dispute',
            'past_condition_not_current', 'preload_heart_history', 'denies_ever',
            'dispute_history_uncertain', 'no_new_report', 'missing', 'no_interview',
            'review_code_2', 'review_code_3', 'review_code_6',
            'review_negative_wording', 'review_unrecognized_code')
EVIDENCE_INDEX = {name: i for i, name in enumerate(EVIDENCE)}


def development_filter(ids, wave_cap, end_month):
    """Filtro Parquet explícito: preserva datas nulas, sem ler futuro clínico."""
    import pyarrow.dataset as ds
    return (ds.field('id').isin(ids) & (ds.field('wave') <= wave_cap)
            & ((ds.field('interview_month') <= end_month) | ds.field('interview_month').is_null()))


def required_columns():
    return ['id', 'wave', 'interview_observed', 'interview_month', 'age_end', 'proxy',
            'adl_state'] + [f'{d}__{f}' for d in DISEASE_NAMES for f in (*CONDITION_FIELDS, 'evidence')]


def numeric_values(frame):
    raw = frame.apply(pd.to_numeric, errors='raise').to_numpy(dtype=float, na_value=np.nan)
    if np.isinf(raw).any():
        raise ValueError('Valor infinito no prefixo')
    mask = ~np.isnan(raw)
    return np.where(mask, raw, 0.).astype(np.float32), mask


def edge_array(source, target):
    return np.asarray([source, target], dtype=np.int64).reshape(2, -1)


def build_prefix_graph(panel, person_id, origin_wave):
    """Sem rótulos. Valida apenas o prefixo: mudar futuro não altera este grafo.

    Cada linha observada gera uma visita e oito nós condição–visita. Valores
    ausentes têm preenchimento zero E máscara explícita; não são negativos.
    """
    missing = set(required_columns()) - set(panel.columns)
    if missing:
        raise ValueError(f'Campos necessários ausentes: {sorted(missing)}')
    p = panel.loc[panel.id.eq(person_id) & panel.wave.le(origin_wave), required_columns()].copy()
    if p.empty or p[['id', 'wave']].isna().any().any() or p.wave.duplicated().any():
        raise ValueError('Prefixo ausente ou chaves duplicadas')
    if not p.interview_observed.isin([True, False]).all():
        raise ValueError('Indicador de entrevista inválido')
    p = p[p.interview_observed].sort_values('wave').reset_index(drop=True)
    if p.empty or p.wave.iloc[-1] != origin_wave:
        raise ValueError('Origem não observada')
    for col in ['wave', 'interview_month']:
        s = pd.to_numeric(p[col], errors='raise')
        if s.isna().any() or not np.isfinite(s).all() or s.mod(1).ne(0).any():
            raise ValueError('Data/onda ausente ou inválida no prefixo')
    if p.interview_month.diff().dropna().le(0).any():
        raise ValueError('Datas não crescentes no prefixo')
    if not p.adl_state.dropna().isin([0, 1]).all():
        raise ValueError('Estado ADL inválido')
    if p.adl_state.iloc[-1] != 0 or not p.age_end.iloc[-1] >= 50:
        raise ValueError('Origem não elegível para alvo ADL')
    p['gap_months'] = p.interview_month.diff()
    p['gap_waves'] = p.wave.diff()
    vx, vm = numeric_values(p[list(VISIT_FIELDS)])
    rows = []
    evidence = []
    for row in p.to_dict('records'):
        for d in DISEASE_NAMES:
            rows.append({f: row[f'{d}__{f}'] for f in CONDITION_FIELDS})
            event = row[f'{d}__evidence']
            evidence.append(EVIDENCE_INDEX.get(event, 0) if pd.notna(event) else 0)
    c = pd.DataFrame(rows, columns=CONDITION_FIELDS)
    for col in CONDITION_FIELDS[:3]:
        if not c[col].dropna().isin([0, 1]).all():
            raise ValueError('Estado ou indicador de condição inválido')
    age = pd.to_numeric(c.waves_since_evidence, errors='raise').dropna()
    if age.lt(0).any() or age.mod(1).ne(0).any():
        raise ValueError('Idade da evidência inválida')
    cx, cm = numeric_values(c)
    n, k = len(p), len(DISEASE_NAMES)
    visit_index = np.repeat(np.arange(n), k)
    return {
        'visit_x': vx, 'visit_mask': vm, 'condition_x': cx, 'condition_mask': cm,
        'evidence': np.asarray(evidence, dtype=np.int64),
        'condition_type': np.tile(np.arange(k, dtype=np.int64), n),
        'visit_month': p.interview_month.to_numpy(dtype=np.int64),
        'condition_month': np.repeat(p.interview_month.to_numpy(dtype=np.int64), k),
        'condition_to_visit': edge_array(np.arange(n*k), visit_index),
        'condition_temporal': edge_array(np.arange((n-1)*k), np.arange(k, n*k)),
        'visit_temporal': edge_array(np.arange(n-1), np.arange(1, n)),
        'origin_visit': np.asarray([n-1], dtype=np.int64),
    }


def batch_graphs(graphs):
    """União disjunta sem padding; IDs de batch não são atributos preditores."""
    if not graphs:
        raise ValueError('Batch vazio')
    lists = {key: [] for key in graphs[0]}
    visit_batch, condition_batch = [], []
    nv = nc = 0
    for index, g in enumerate(graphs):
        for key, value in g.items():
            if key == 'condition_to_visit':
                value = value + np.asarray([[nc], [nv]])
            elif key == 'condition_temporal':
                value = value + nc
            elif key in ('visit_temporal', 'origin_visit'):
                value = value + nv
            lists[key].append(value)
        visit_batch.extend([index] * len(g['visit_x']))
        condition_batch.extend([index] * len(g['condition_x']))
        nv += len(g['visit_x'])
        nc += len(g['condition_x'])
    out = {key: np.concatenate(values, axis=1 if key in (
        'condition_to_visit', 'condition_temporal', 'visit_temporal') else 0)
        for key, values in lists.items()}
    out['visit_batch'] = np.asarray(visit_batch, dtype=np.int64)
    out['condition_batch'] = np.asarray(condition_batch, dtype=np.int64)
    return out


def calendar_boundary_audit(metadata, group, end_month, wave_cap):
    """Somente chaves/datas. Não lê estado clínico posterior ao limite.

    Identifica pares adjacentes existentes cujo sucessor seria removido pelo
    filtro de calendário. A contagem inclui todas as origens com data no limite,
    não apenas as elegíveis; o chamador cruza as chaves em memória.
    """
    m = metadata[metadata.wave.le(wave_cap)].sort_values(['id', 'wave']).copy()
    if m[['id', 'wave']].isna().any().any() or m.duplicated(['id', 'wave']).any():
        raise ValueError('Metadados duplicados ou ausentes')
    next_wave = m.groupby('id').wave.shift(-1)
    next_month = m.groupby('id').interview_month.shift(-1)
    flag = next_wave.eq(m.wave + 1) & next_month.gt(end_month) & m.interview_month.le(end_month)
    return m.loc[flag, ['id', 'wave']].assign(group=group)
