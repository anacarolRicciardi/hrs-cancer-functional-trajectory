# Protocolo implementado e decisões

## Pergunta

Em participantes com histórico de câncer e sem dificuldade ADL na origem, acrescentar
atributos de grafos temporais melhora a previsão de dificuldade na próxima entrevista,
além do histórico funcional? A referência é o modelo B do 00h.

## Etapas e natureza da evidência

| Etapa | Decisão / objetivo | Avaliação |
|---|---|---|
| 00h | Separar informação funcional, acompanhamento e doenças | Validação geral, exploratória |
| 00i | Auditar suporte e seguimento no recorte de câncer | Contagens; sem modelos |
| 00j | Avaliar A–D gerais no subgrupo com câncer | Principal B−A em Brier |
| 00k | Acrescentar pares, rede estática, móvel e acumulada a B | Principal móvel−B em Brier |

As comparações de cada extensão foram codificadas antes de sua execução, mas foram
escolhidas após resultados anteriores. Não houve pré-registro confirmatório, nova
amostra independente ou ajuste por multiplicidade. O teste original do piloto já foi
consultado; 00j/00k não leem seus X/y e não o reutilizam para escolher modelos.

## População e alvo

Origem observada, idade ≥50, cinco itens ADL negativos. Alvo: um ou mais itens ADL
positivos na onda seguinte observada, com data válida e posterior. Zero exige cinco
negativos; ausências e óbito não viram zero. Possível recorrência após recuperação.
Histórico de câncer definido na origem por `cancer__history_asof == 1`, sem usar
informação futura. Não é uma coorte de câncer ativo ou de incidência.

Treino geral (49.389 transições) é mantido, inclusive pessoas sem histórico de câncer.
Validação do subgrupo: 353 transições, 345 pessoas, 325 domicílios, 39 eventos.
Não treinar especificamente no subgrupo nesta versão. Não selecionar o modelo pelo
resultado em apenas 37 transições com novo relato e três eventos.

## Informação temporal

História inicializada desde onda 1. Origens desde janeiro/2000. Hash por domicílio
de origem, semente 2026, frações nominais 60/20/20. Treino com desfecho até 12/2012;
validação com origem após 12/2012 e desfecho até 12/2016. Indivíduos e domicílios
de origem disjuntos; não é prova de ausência de qualquer vínculo familiar.

Redes na referência de treino sem condicionar a desfechos: uma última entrevista
por pessoa antes de cada corte anual, 2000–2013. Janelas de 48 meses ou acumuladas.
Na validação, redes temporais congeladas no corte 01/2013; estática no corte 01/2000.
Datas de entrevista não são datas de publicação dos dados. O corte estático é antigo
por desenho. Não há atualização online na validação.

## Grafos e modelos

Oito condições; 28 pares; phi; suporte ≥100, cobertura ≥0,50, |phi|≥0,10. ADL é alvo,
não nó. Nós não são pessoas. Arestas não são contatos, transmissão ou relações causais.
Sem ajuste de phi por idade/coorte. Estado desconhecido ou par sem suporte permanece
ausente; par avaliável não selecionado tem peso zero. Produtos individuais recebem
o peso da rede disponível na origem. Estados carregados sem evidência não são observados.

Todas as extensões partem de B (37 colunas candidatas) e acrescentam 28 colunas.
O controle de todos os pares usa produtos não ponderados. Mediana, indicadores de
ausência e padronização aprendidos no treino; regressão logística C=1, lbfgs, 2.000
iterações. Não convergência interrompe. Não é GNN. Dimensões candidatas e efetivas
estão em `dimensoes.csv`; pesos constantes podem ser absorvidos pela padronização.

## Comparações e incerteza

Principal de 00k: `B_rolling − B_functional`, Brier. Secundárias: móvel−estática,
móvel−pares, acumulada−B, estática−B e pares−B. Métricas auxiliares: log loss, ROC-AUC,
AP e calibração. Bootstrap pareado de 1.000 amostras de domicílios, semente 2026,
condicionado aos ajustes. Não inclui incerteza de treinamento ou das redes.
IC só é fornecido com ≥90% de réplicas válidas. Não há correção de multiplicidade.

Faixas de calibração fixas: 0–5–10–20–40–100%, limite superior incluso. Faixas vazias
ficam sem frequência; n<20 recebe marca visual, não garantia de precisão. Sem IC por
faixa, recalibração ou escolha de limiar de decisão. Proximidade média não prova calibração.

## Extensões futuras

Novos limiares, redes ajustadas, outras arquiteturas ou dados de tratamento requerem
novo protocolo e estratégia de avaliação independente. Não escolher alterações apenas
para obter ganho na validação já consultada. Antes de uso clínico: confirmar óbito e
perdas, avaliar calibração e benefício para uma decisão definida, validar externamente
e testar compreensão por profissionais. Nenhuma dessas etapas está concluída.
