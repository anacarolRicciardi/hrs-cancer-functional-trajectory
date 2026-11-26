"""Seleção por esquema; nenhuma leitura de dados ocorre ao importar o módulo."""
import re


def select_columns(available, patterns, explicit=(), required=()):
    """Seleciona nomes reais, sem inferir que uma variável existe ou é harmonizada."""
    available = list(available)
    lookup = {name.upper(): name for name in available}
    missing = [name for name in (*explicit, *required) if name.upper() not in lookup]
    if missing:
        raise ValueError(f"Colunas solicitadas ausentes: {missing}")
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    mandatory = {name.upper() for name in (*explicit, *required)}
    selected = [name for name in available if name.upper() in mandatory or any(p.search(name) for p in compiled)]
    if not selected:
        raise ValueError("Nenhuma coluna selecionada. Revise o dicionário e os padrões.")
    return selected


def missing_value_mask(series, ranges):
    """Marca códigos SPSS declarados, inclusive intervalos; não confunde zero com ausência.

    As regras vêm de meta.missing_ranges com user_missing=True.
    Os valores originais são preservados pelo extrator, para auditoria posterior.
    """
    mask = series.isna()
    for bounds in ranges:
        low, high = bounds["lo"], bounds["hi"]
        if low == high:
            mask = mask | series.eq(low).fillna(False)
        else:
            mask = mask | series.between(low, high).fillna(False)
    return mask
