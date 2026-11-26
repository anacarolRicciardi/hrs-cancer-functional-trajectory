# Resultados e conclusões permitidas

Fontes e hashes completos foram registrados no arquivo local `PROVENIENCIA.json`,
que não integra esta distribuição. Não há resultados
sintéticos nas tabelas científicas. Frequências sem ponderação amostral.

## O que foi observado

| Comparação | Delta Brier | IC95% | Interpretação |
|---|---:|---|---|
| B−A na validação geral (00h) | −0,003966 | [−0,006063; −0,001903] | Sinal favorável à memória funcional neste desenho |
| B−A no subgrupo de câncer (00j) | −0,003645 | [−0,010363; +0,002634] | Inconclusivo na métrica principal |
| Móvel−B no subgrupo (00k) | +0,000490 | [−0,000703; +0,001710] | Sem ganho conclusivo do grafo |

O conjunto de câncer inclui 353 transições/39 eventos, 345 pessoas/325 domicílios.
00k: Brier B=0,088361; pares=0,088220; estática=0,088725; móvel=0,088851;
acumulada=0,088741. As seis comparações pareadas de Brier incluem zero. Não usar a
pequena vantagem pontual de pares para declarar vencedor ou selecionar limiares.

No grafo móvel, câncer–artrite cruzou o limiar em 2012 (phi=0,109843) e 2013
(0,105304). Foram dois de 98 pares–cortes avaliáveis envolvendo câncer. A rede
completa tinha 12 arestas em 2000 e 16 em 2013. As redes são populacionais da
referência de treino; não são redes exclusivas de pacientes oncológicos.

## O que não foi estabelecido

- Efeito causal do câncer, da artrite, de tratamento ou de uma aresta sobre ADL.
- Equivalência entre modelos ou inutilidade geral de grafos.
- Variação específica do benefício por câncer: não houve teste formal de interação.
- Calibração adequada em toda a faixa de risco; médias próximas são insuficientes.
- Benefício de decisão clínica, validação externa ou transporte para o Brasil.
- Surgimento biológico da relação câncer–artrite em 2012.

## Por que o resultado tem valor metodológico

A referência incorpora o próprio passado funcional antes de testar relações entre
doenças. Isso impede atribuir automaticamente a grafos ganhos que podem vir de
memória individual. Controles de todos os pares e rede estática distinguem seleção
relacional de simples aumento da flexibilidade. O congelamento temporal torna a
interpretação auditável, mas restringe o experimento a esse cenário.

## Limitações que acompanham qualquer apresentação

Validação reutilizada; 39 eventos no subgrupo; bootstrap condicionado aos ajustes;
sem correção de multiplicidade; relatos históricos; seleção por observação do alvo;
sem pesos ou riscos competitivos; phi não ajustado; rede estática antiga e redes
temporais congeladas na validação. Datas de entrevista não são datas de liberação
dos dados. A análise é de previsão, não uma recomendação assistencial.

## Continuidade

Primeiro definir qual limitação um novo experimento resolverá. Possibilidades:
validar códigos de óbito/perdas, avaliar estabilidade das redes ou ampliar informação
oncológica com auditoria temporal. Definir novo protocolo e avaliação independente
antes de testar uma arquitetura mais complexa. O estudo de compreensão por clínicos
permanece separado e não executado.
