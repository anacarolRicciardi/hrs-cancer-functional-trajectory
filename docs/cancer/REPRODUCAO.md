# Reprodução da extensão sobre câncer

**Nota de distribuição:** as instruções abaixo registram a execução na raiz
original. Esta cópia não contém os notebooks executados, alguns notebooks
anteriores nem os dados e artefatos necessários. A reprodução integral em uma
nova máquina não foi verificada.

## Ambiente efetivamente utilizado

Raiz do projeto: `C:\Users\T-GAMER\Documents\ChatGPT\SERIES_TEMPORAIS`.
Kernel empírico: `.venv-local\Scripts\python.exe`.

| Componente | Versão registrada |
|---|---|
| Python | 3.14.4 |
| pandas | 3.1.1 |
| NumPy | 2.5.5 |
| scikit-learn | 1.9.1 |

As versões são provenientes dos manifestos da execução, não recomendações para
atualização. `.venv` foi usado para gerar notebooks e testes de software; não é o
ambiente que reproduziu os resultados empíricos recentes. Os requirements antigos
contêm faixas e não fixam todas as dependências. Um lock completo transferível ainda
é pendência de distribuição. Não instalar versões diferentes para contornar asserts.

## Executar com os artefatos já existentes

1. Abrir a raiz original no VS Code, não a cópia antiga `github_release`.
2. Conferir `config/protocolo_teste_piloto_v1.json`: `split_dir` e `network_dir`.
3. Selecionar o kernel `.venv-local` no notebook e reiniciar o kernel.
4. Executar todas as células em ordem. Não é necessário reconstruir o SAV ou o painel.

| Notebook | Pré-requisitos principais | Saída |
|---|---|---|
| 00i_viabilidade_cancer | Painel inicializado, manifesto, divisão concluída | `viabilidade_cancer_*` |
| 00j_avaliacao_cancer | 00g, 00h e auditoria 00i de referência | `avaliacao_cancer_*` |
| 00k_grafos_cancer | Referências do 00j e redes 00b correspondentes | `grafos_cancer_*` |

Os caminhos das execuções de referência estão nas células de configuração. Em outra
máquina, migrar os caminhos sem trocar silenciosamente a identidade dos arquivos.
Uma execução nova recebe pasta nova; `_SUCCESS` só aparece após a gravação final.
Não criar marcadores manualmente nem remover asserts para forçar conclusão.

## Pré-requisitos de dados

Painéis `painel_*.parquet` com histórico inicializado na onda 1, versão
`history_initialized_v2`, `individual_saved=true`. Divisão com `_WORKFLOW_SUCCESS`,
X/y de treino e validação, atribuições locais e configuração. Redes com `_SUCCESS`,
arestas, auditoria e configuração. O código não acompanha os dados autorizados.
Não substituir por CSV sintético: fixtures só verificam regras do software.

00j/00k verificam versões, hashes, chaves, cronologia, separação e reprodução das
métricas de referência. Seus modelos gerais são reajustados porque os modelos
anteriores não foram persistidos; não são retreinados apenas no subgrupo.

## Figuras e artigo

Executar o gerador de figuras apontando para a pasta 00k concluída:

```powershell
.\.venv-local\Scripts\python.exe scripts\plot_cancer_graph_report.py "CAMINHO_DA_EXECUCAO_00k"
```

`scripts/build_cancer_graph_report.py RUN` gera o dossiê a partir dos agregados e
figuras. `scripts/build_cancer_manuscript.py` gera artigo Word, Markdown e
`docs/cancer/PROVENIENCIA.json`. Esses dois geradores usam python-docx; nesta sessão
foi usado o runtime de documentos do Codex, separado do ambiente empírico. Os caminhos
das execuções estão explicitamente fixados no gerador do artigo para rastreabilidade.

O template editorial é `docs/cancer/artigo_template.md`. Tabelas numéricas são
preenchidas dos CSVs; não editar números manualmente no Word esperando que o gerador
os preserve. Mudanças no texto Word não retornam automaticamente ao template.
Não executar os geradores de notebooks para abrir um notebook já anotado: eles
recriam o arquivo e podem substituir células e saídas que o usuário tenha editado.

## Verificação realizada

Seis testes de viabilidade e cinco de calibração/bootstrap passaram com dados
artificiais. Os notebooks foram validados estruturalmente e compilados. As execuções
reais 00j e 00k completaram as verificações e salvaram agregados. Dossiê e artigo são
renderizados no Word e inspecionados visualmente; isso não substitui revisão científica
dos autores. As execuções em lote salvaram CSVs, gráficos e manifestos; os notebooks
fontes não contêm necessariamente as saídas incorporadas às células.

## Problemas comuns

| Mensagem / problema | Ação |
|---|---|
| Ambiente diferente do 00g | Conferir executável exibido e selecionar `.venv-local` |
| Métricas divergiram | Conferir fontes, hashes e versões; interromper interpretação |
| `_SUCCESS` ausente | Ler o erro anterior; não criar marcador manualmente |
| Painéis não encontrados | Corrigir caminho do protocolo/manifesto e exportação individual |
| FigureCanvasAgg não interativo | Em execução sem janela, verificar PNGs salvos; não é falha do cálculo |
| Word aberto ao regerar | Fechar o arquivo de destino; preservar edições em outra cópia |

Não enviar registros individuais no diagnóstico. Preferir mensagens de erro e agregados.
