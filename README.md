# HRS Cancer Functional Trajectory

Projeto do artigo sobre histórico de câncer e previsão longitudinal de dificuldade ADL no HRS.

## Pergunta

A multimorbidade representada por relações temporais melhora a previsão além do histórico funcional em pessoas com histórico de câncer?

## Conteúdo

- viabilidade do subgrupo;
- definição prospectiva de câncer;
- histórico funcional;
- redes estáticas e temporais;
- comparação exploratória;
- calibração descritiva;
- auditoria de não resposta e óbito.

## Estrutura

- `src/`: módulos de câncer e avaliação;
- `scripts/`: notebooks geradores e relatório;
- `tests/`: testes sintéticos;
- `docs/`: manuscrito e fontes;
- `deliverables/`: DOCX e figuras;
- `results/`: somente agregados;
- `data/`: vazio; microdados fora do Git.

## Estado

Exploratório. Validação pequena com 353 transições e 39 eventos na validação. Não demonstra causalidade ou utilidade clínica.

## Distribuição e reprodução

Este repositório reúne o manuscrito, código e testes da extensão. A análise
usa grafos de associações entre doenças como atributos de regressão logística;
não é uma GNN. Os dados HRS, previsões individuais, modelos e resultados locais
não são distribuídos.

O [protocolo](docs/cancer/PROTOCOLO.md), os [resultados](docs/cancer/RESULTADOS.md)
e as [instruções históricas de reprodução](docs/cancer/REPRODUCAO.md) descrevem
as execuções na raiz original. Os notebooks executados e seus artefatos
intermediários não foram incluídos nesta cópia; os scripts geradores estão em
`scripts/`. Os geradores 00j e 00k dependem de notebooks anteriores que não
acompanham esta cópia. Gerá-los não recupera os dados nem os artefatos
necessários, e a reprodução integral nesta cópia ainda não foi verificada. Os requisitos possuem
faixas e não são um lock do ambiente empírico documentado.

As figuras ligadas no Markdown do artigo apontam para resultados locais não
distribuídos; as figuras estão incorporadas no documento Word em `deliverables/`.
O material é preliminar e precisa de revisão acadêmica e institucional.
