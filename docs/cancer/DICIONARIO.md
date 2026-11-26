# Dicionário e contratos de dados

A seguir estão os campos e distinções que controlam a extensão de câncer.
O glossário geral pertence ao projeto original e não acompanha esta cópia.

| Campo / termo | Definição operacional |
|---|---|
| `id`, `wave` | Chave pessoa–onda; única e não ausente |
| `household_id`, `split_group` | Domicílio de origem, agrupamento de separação e bootstrap |
| `interview_month` | Ano × 12 + mês; janeiro/2000=24001 |
| `adl_state` | 0: cinco itens negativos; 1: ao menos um positivo; ausente: não classificável |
| `eligible_baseline` | Entrevista observada, idade ≥50, ADL=0 |
| `target` | ADL na próxima onda observada com cronologia válida; não é mortalidade |
| `cancer__history_asof` | Estado histórico de câncer até a origem; não câncer ativo |
| `cancer__ever_positive_recorded` | Registro positivo conhecido até a origem |
| `cancer__carried_without_current_evidence` | Estado histórico mantido sem evidência na entrevista atual |
| `cancer__evidence` | Interpretação do relato/código; contestação, ausência e revisões são preservadas |
| `new_report` | Positivo explícito após negativo utilizável observado, sem positivo anterior e datas crescentes |
| `phi` | Associação binária entre condições; não ajuste causal nem importância do modelo |
| `assessable` | Par com suporte e condições para calcular associação |
| `selected` | Par avaliável que também satisfaz os limiares do grafo |
| `cutoff_month` | Corte da rede, com fontes estritamente anteriores |
| `snapshot_cutoff` | Corte atribuído à origem preditiva; nunca posterior a ela |
| `Brier` | Média de (probabilidade − alvo)²; menor é melhor |
| `ROC-AUC` | Discriminação de positivos e negativos; maior é melhor |
| `AP` | Average precision, resumo de precisão–revocação |
| `delta` | Métrica do candidato menos a da referência |
| `low`, `high` | Limites percentis 2,5% e 97,5% do bootstrap |

## Categorias da auditoria

`historico_positivo`: história igual a 1. `negativo_sem_positivo_previo`: história 0 e
nenhum positivo conhecido. `negativo_com_positivo_previo`: história atual 0 com registro
positivo anterior, preservando a contestação. `desconhecido`: não classificável.
Categorias dependem da origem; uma pessoa pode mudar de categoria.

`observed` possui alvo binário; `adl_unknown` não possui ADL classificável.
`nonresponse_alive`, `dropped`, `calendar_review` e `other_or_unknown` são distintos.
`death_status_review` e `proxy_death_review` exigem validação dos códigos antes de
serem tratados como óbito. `no_adjacent_wave` inclui a última onda da janela e não é
automaticamente perda. `outside_time_window` ultrapassa o limite do desenho.

## Saídas 00i

`resumo_viabilidade.csv` e `transicoes_por_onda.csv`: `transitions` são origens
elegíveis; `observed` é o denominador com alvo; `events_adl` e `nonevents_adl` somam
`observed`; `unknown_outcome` é a diferença. `event_fraction` fica ausente com zero
observações. `people` e `households` são distintos dentro da linha, não aditivos
entre ondas/categorias. `entrevistas_por_onda` inclui pessoas não elegíveis por ADL.

## Saídas 00j e 00k

| Arquivo | Conteúdo |
|---|---|
| `suporte.csv` | Pessoas/domicílios distintos no recorte observado e número de eventos |
| `metricas_cancer.csv` (00j) | A–D no subgrupo |
| `metricas.csv` (00k) | B e extensões; separar `scope=cancer` de `scope=general` |
| `comparacoes_pareadas.csv` / `comparacoes.csv` | Deltas e IC pareados por modelo e métrica |
| `intervalos_absolutos.csv` | Estimativas e IC de cada modelo |
| `calibracao.csv` | Faixas fixas, n, eventos, previsão média e fração observada |
| `reproducao_00h.csv` (00j) | Conferência de métricas antes da avaliação do subgrupo |
| `dimensoes.csv` (00k) | Colunas candidatas, não constantes, totalmente ausentes e transformadas |
| `atribuicao_redes.csv` | Resumo de cortes usados por conjunto/modelo |
| `arestas_temporais.csv` | Todos os pares–cortes; presença de linha não implica seleção |
| `auditoria_redes.csv` | Número de pessoas e limites das fontes por corte |
| `config.json` | Escopo, fontes, versões, parâmetros e hashes |
| `_SUCCESS` | Gravação concluída, não validação clínica |

No gráfico de calibração, n<20 marca uma faixa pequena; não é critério inferencial.
Na visualização de rede, o câncer destacado tem finalidade editorial. Posições fixas
evitam que mudanças do layout simulem mudanças do grafo. ADL não é um nó.
