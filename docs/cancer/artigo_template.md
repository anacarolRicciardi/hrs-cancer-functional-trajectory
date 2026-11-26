# Históricos individuais e grafos temporais na previsão de dificuldade funcional em pessoas com histórico de câncer

Autores: Adolfo; Ana Carolina R.; Bruna C.; [quarto integrante]
Departamento de Ciência da Computação · Instituto de Ciências Matemáticas e de Computação · Universidade de São Paulo
SCC5977 — Aprendizado de Máquina para Séries Temporais · Prof. Dr. Diego Furtado Silva · São Carlos, 2026
Versão para revisão dos autores — 22 de novembro de 2026

## Resumo

Este trabalho investiga se representações por grafos temporais de multimorbidade acrescentam informação à previsão de dificuldade em atividades básicas da vida diária (ADL), além do histórico funcional individual. Utilizou-se um painel local derivado do RAND HRS Longitudinal File 1992–2022 V2, com reconstrução prospectiva de relatos, separação por domicílio de origem e calendário, e avaliação exploratória em participantes com histórico de câncer. O treinamento geral compreendeu 49.389 transições. A validação do subgrupo incluiu 353 transições de 345 pessoas, com 39 eventos ADL. Modelos logísticos com o mesmo histórico funcional foram comparados a extensões com todos os pares de doenças, grafo estático, grafo móvel de 48 meses e grafo acumulado. As redes foram estimadas exclusivamente na referência de treino anterior a cada corte e congeladas em janeiro de 2013 na validação. O Brier foi 0,08836 para o histórico funcional e 0,08885 com a rede móvel; a diferença de +0,00049 apresentou IC95% de −0,00070 a +0,00171. Nenhuma das seis comparações em Brier demonstrou ganho conclusivo. Descritivamente, câncer–artrite ultrapassou o limiar de seleção em dois dos 14 cortes. Os resultados distinguem estrutura associativa de utilidade preditiva e sustentam avaliar a complexidade relacional contra referências longitudinais informativas. A reutilização da validação e o pequeno número de eventos impedem interpretação confirmatória ou clínica.

Palavras-chave: dados longitudinais; grafos temporais; multimorbidade; câncer; atividades da vida diária; avaliação preditiva.

## 1 Introdução

Entrevistas sucessivas permitem representar estados de saúde e a história que os antecede. Para prever dificuldade funcional, duas pessoas sem dificuldade na entrevista atual podem diferir quanto a episódios prévios, condições registradas e continuidade do acompanhamento. O desafio de séries temporais consiste em organizar essas informações segundo sua disponibilidade, preservando ausências e intervalos variáveis.

O Health and Retirement Study (HRS) fornece dados longitudinais sobre envelhecimento, e o produto RAND harmoniza informações das entrevistas [1]. O estudo de funcionalidade em pessoas com câncer tem antecedentes no HRS: Westrick, Langa e Kobayashi avaliaram associações entre comportamentos anteriores ao diagnóstico e trajetórias funcionais posteriores [2]. Portanto, câncer e funcionalidade não constituem, isoladamente, uma lacuna inédita.

Grafos permitem representar associações entre condições de saúde em diferentes períodos. A revisão de Gravina e Bacciu discute modelos de grafos dinâmicos e a importância de comparações de desempenho consistentes [3]. Sua existência, porém, não implica que atributos relacionais melhorem qualquer tarefa. Uma referência que omita episódios funcionais anteriores pode atribuir ao grafo um ganho proveniente de informação longitudinal mais simples.

A pergunta deste trabalho é: **atributos de grafos de multimorbidade melhoram a previsão de dificuldade ADL na próxima entrevista, em pessoas com histórico de câncer, além do histórico funcional individual?** A contribuição é experimental e metodológica: reconstruir históricos sem usar o futuro da pessoa, controlar a disponibilidade temporal das redes e comparar representações nas mesmas transições. Não se propõe uma nova arquitetura neural nem se reivindica novidade algorítmica estabelecida por revisão sistemática.

## 2 Trabalhos relacionados e posicionamento

Westrick e colaboradores analisaram trajetórias de memória e ADL após um primeiro diagnóstico de câncer no HRS, utilizando comportamentos anteriores ao diagnóstico e modelagem de trajetórias em grupos [2]. Aqui, o alvo é a entrevista seguinte, o subgrupo é definido pelo histórico disponível na origem e a avaliação compara previsões fora do conjunto de treinamento. Não estimamos o efeito de comportamentos ou tratamentos.

Mullins e colaboradores compararam relatos de câncer do HRS com registros Medicare e identificaram sensibilidade imperfeita e variação entre tipos de tumor [4]. Isso reforça a necessidade de interpretar o indicador como relato histórico, sem equipará-lo a diagnóstico clínico ativo. Não utilizamos vinculação ao Medicare, estágio ou localização tumoral.

Em relação a grafos dinâmicos [3], utilizamos uma sequência de redes por cortes discretos para construir atributos de um modelo logístico. Trata-se de uma abordagem baseada em atributos relacionais, não de uma rede neural de grafos. A descrição de população, processamento, avaliação e limitações busca transparência compatível com a motivação da diretriz TRIPOD+AI [5]; não foi realizada auditoria formal de conformidade integral com a diretriz.

## 3 Dados e tarefa preditiva

### 3.1 Fonte e reconstrução longitudinal

Utilizou-se o painel local derivado do RAND HRS Longitudinal File 1992–2022 V2 [1]. O painel funcional abrange ondas 3–16; a reconstrução dos históricos de condições é inicializada na onda 1. A inclusão das ondas anteriores evita tratar entrada no painel funcional como ausência de história clínica.

São consideradas hipertensão, diabetes, câncer, doença pulmonar, doença cardíaca, acidente vascular cerebral (AVC), condição psiquiátrica e artrite. O processamento interpreta perguntas e códigos por onda e atualiza a história para frente. Códigos desconhecidos e contestações permanecem identificados. Um estado mantido sem evidência atual recebe indicador de carregamento. A primeira observação positiva não é automaticamente uma data de início da doença.

O indicador de câncer deriva dos relatos CANCR e da informação sobre a pergunta aplicada. O subgrupo preditivo é definido por estado histórico positivo na entrevista de origem. Essa definição não exige câncer ativo e não representa uma coorte de incidência. Um novo relato observável, utilizado somente na auditoria de viabilidade, exige negativo utilizável na entrevista observada anterior, positivo explícito, ausência de positivo anteriormente registrado e datas crescentes.

### 3.2 Elegibilidade e desfecho

A unidade é uma transição pessoa–onda. A origem deve ser uma entrevista observada, com idade ao final da entrevista de pelo menos 50 anos e cinco respostas válidas negativas para dificuldade em banho, vestir-se, comer, deitar/levantar da cama e andar pelo quarto. Pelo menos um item positivo caracteriza dificuldade; combinações incompletas sem positivo permanecem desconhecidas.

O desfecho é alguma dificuldade ADL na onda imediatamente seguinte, com entrevista observada, datas crescentes e estado funcional conhecido. Óbito, não resposta e ADL desconhecida não são classificados como negativos. O horizonte é a próxima entrevista, não exatamente dois anos. Como uma pessoa sem dificuldade atual pode ter tido episódios anteriores, o alvo inclui possível recorrência após recuperação, e não exclusivamente primeiro episódio na vida.

### 3.3 Viabilidade do recorte de câncer

A auditoria identificou 6.317 transições observadas com histórico de câncer no treino, com 802 eventos, e 353 na validação, com 39 eventos. No recorte restrito a novos relatos observáveis havia apenas 37 transições e três eventos na validação, razão para mantê-lo descritivo.

Entre 857 origens elegíveis com histórico de câncer na janela da auditoria de validação, 353 tinham desfecho observado. Das 504 restantes, 435 correspondiam ao encerramento ou limite da janela; 69 incluíam não resposta e códigos de possível óbito a revisar. Assim, 504 não deve ser reportado como número de perdas de acompanhamento ou óbitos. A seleção por disponibilidade do desfecho permanece uma limitação.

## 4 Representações e avaliação

### 4.1 Histórico individual de referência

O modelo A utiliza idade, entrevista por representante, quatro atributos históricos por condição e calendário: 35 colunas candidatas. O modelo B acrescenta ADL na entrevista anterior e registro funcional positivo anterior conhecido, totalizando 37. Em análises auxiliares, C acrescenta cinco atributos de acompanhamento; D acrescenta carga de condições, persistência, novos registros e taxas, com 61 colunas candidatas no total. D não representa somente mudança, pois inclui carga contemporânea.

A análise geral anterior apresentou melhora de B sobre A no Brier (diferença −0,00397; IC95% −0,00606 a −0,00190). Isso motivou usar **B como referência comum** para testar grafos no subgrupo com câncer. A decisão foi informada por etapas exploratórias anteriores; não corresponde a protocolo confirmatório independente.

### 4.2 Redes e atributos relacionais

As condições são os oito nós; ADL é o alvo do modelo, não um nó. Existem 28 pares não ordenados. Em cada corte anual de janeiro de 2000 a janeiro de 2013, a referência utiliza domicílios de treino, entrevistas anteriores ao corte, idade ≥50 e a entrevista mais recente por pessoa. Não se condiciona a referência à disponibilidade do desfecho futuro. Foram estimadas redes móveis de 48 meses e acumuladas.

O peso é a associação phi entre estados binários. A seleção requer pelo menos 100 observações pareadas, cobertura de 50% e valor absoluto de phi ≥0,10. Esses limiares são escolhas operacionais, não fronteiras clínicas. Dados carregados sem evidência atual não são considerados estados observados para os produtos relacionais. Pares sem suporte ou estados desconhecidos permanecem ausentes; pares avaliáveis não selecionados recebem peso zero.

O atributo relacional de cada par é o produto dos estados individuais, multiplicado pelo peso selecionado na rede disponível até a origem. A versão estática usa sempre o corte de janeiro de 2000; as versões temporais usam o último corte disponível. Na validação, móvel e acumulada ficam congeladas em janeiro de 2013. Assim, testamos transferência de uma representação aprendida temporalmente, não atualização online ao longo da validação. A referência histórica pode incluir entrevistas passadas da própria pessoa de treino, sem consultar seu desfecho futuro.

{{TABLE_MODELS}}

Cada extensão relacional acrescenta 28 colunas candidatas à mesma referência B. Colunas constantes, ausentes e indicadores de ausência alteram a dimensão efetiva. A padronização pode absorver pesos constantes; phi não deve ser interpretado como importância clínica do preditor. O controle com todos os pares ajuda a distinguir informação de interação da seleção e ponderação por grafo.

### 4.3 Separação e ajuste

Foi preservada a partição determinística por domicílio de origem, com semente 2026 e proporções nominais 60/20/20, combinada com cortes de calendário. O treino exige desfecho até dezembro de 2012; a validação exige origem após dezembro de 2012 e desfecho até dezembro de 2016. Pessoas e domicílios de origem não se sobrepõem entre conjuntos, mas esse agrupamento não garante captura de todos os vínculos familiares posteriores.

O recorte comum utiliza origens desde janeiro de 2000. Foram mantidas 49.389 transições de treino geral e 2.358 de validação geral. O subgrupo observado de câncer tem 2.194 pessoas e 2.057 domicílios no treino; na validação, 345 pessoas e 325 domicílios. São 353 transições na validação porque uma pessoa pode contribuir mais de uma vez.

Todos os modelos foram ajustados no treino geral, não exclusivamente em pessoas com câncer. Usou-se regressão logística regularizada, C=1, otimizador lbfgs e limite de 2.000 iterações. Imputação pela mediana, indicadores de ausência e padronização foram aprendidos somente no treino. Avisos de não convergência interrompem a execução. As métricas dos modelos gerais foram reproduzidas antes da avaliação do subgrupo.

### 4.4 Métricas, incerteza e calibração

A comparação principal da extensão de grafos é rede móvel menos B no Brier, a média do erro quadrático das probabilidades. Valores negativos da diferença favorecem o candidato. Comparações com rede estática, todos os pares e rede acumulada são secundárias. Log loss, ROC-AUC e average precision (AP) complementam a descrição, sem substituir avaliação de utilidade clínica.

Os intervalos de confiança de 95% são percentis de 1.000 reamostragens pareadas de domicílios da validação, preservando suas transições. Modelos e redes permanecem ajustados: os intervalos não incorporam incerteza de reajuste ou de estimação da rede. Não há correção por multiplicidade. A calibração é apresentada em faixas fixas 0–5–10–20–40–100%, com contagens e médias; não houve recalibração ou seleção de limiar clínico.

O teste do piloto original já havia sido consultado em etapa anterior. As extensões de câncer não leem seus X/y e utilizam validação já explorada. Nenhuma análise deste artigo deve ser interpretada como avaliação confirmatória ou validação externa.

## 5 Resultados

### 5.1 Histórico funcional no subgrupo

Na validação com câncer, acrescentar histórico funcional ao modelo A reduziu o Brier de 0,09201 para 0,08836. A diferença B−A foi −0,00364, com IC95% de −0,01036 a +0,00263. O resultado pontual é favorável, mas não conclusivo na métrica principal. A AUC passou de 0,7304 para 0,7860; sua diferença apresentou IC95% de +0,0006 a +0,1129, um achado secundário exploratório sem ajuste por multiplicidade.

Os atributos adicionais de acompanhamento e doenças não demonstraram ganho incremental conclusivo. Diferença de significância entre a análise geral e o subgrupo não é evidência de interação com câncer. Não se fez um teste formal dessa interação.

### 5.2 Evolução das associações

Na rede móvel havia 12 arestas selecionadas em janeiro de 2000 e 16 em janeiro de 2013 (Figura 1). Câncer não tinha aresta selecionada no primeiro corte e tinha uma no último. Entre seus sete pares com outras condições, os 14 cortes produziram 98 pares–cortes avaliáveis. Apenas câncer–artrite foi selecionado, em 2012 (phi=0,10984) e 2013 (phi=0,10530).

[[FIGURE:01_redes|Figura 1. Redes móveis de multimorbidade em dois cortes, com posições fixas dos nós. O destaque visual do câncer não representa importância. Arestas são associações phi selecionadas na população de referência de treino, não conexões sociais ou efeitos causais. Fonte: arestas_temporais.csv, execução 00k.]]

A Figura 2 mostra também associações abaixo do limiar. Cruzar 0,10 não demonstra surgimento de uma relação clínica. As associações não foram ajustadas por idade, coorte ou outras condições, e as janelas sobrepostas não são observações independentes.

[[FIGURE:02_cancer_tempo|Figura 2. Associação phi entre câncer e outras condições por corte anual da janela móvel. Pontos indicam pares selecionados; a escala é comum aos anos. Os valores não são contribuições à previsão ADL. Fonte: arestas_temporais.csv, execução 00k.]]

### 5.3 Ganho incremental dos grafos

{{TABLE_METRICS}}

O Brier foi 0,08836 na referência B, 0,08885 com rede móvel, 0,08873 com rede estática e 0,08874 com rede acumulada. Todos os pares apresentou 0,08822, mas essa pequena diferença pontual também foi inconclusiva.

{{TABLE_CONTRASTS}}

A diferença principal, rede móvel menos B, foi +0,00049 (IC95% −0,00070 a +0,00171). Todos os seis intervalos de Brier incluíram zero (Figura 3). Não se demonstrou ganho nem equivalência; os resultados tampouco estabelecem inferioridade geral de grafos dinâmicos. No contraste principal, os intervalos de log loss, AUC e AP também incluíram zero.

[[FIGURE:03_comparacoes|Figura 3. Diferenças de Brier com IC95% por bootstrap de domicílios. Negativo favorece o candidato; destaque para a comparação principal. Intervalos condicionados aos modelos e redes ajustados, sem correção de multiplicidade. Fonte: comparacoes.csv, execução 00k.]]

### 5.4 Calibração descritiva

A frequência observada foi 11,05%. A previsão média foi 11,35% em B e 11,57% em B com rede móvel. A proximidade global não garante calibração nas diferentes faixas: em B, a faixa 20–40% reuniu 39 transições e 15 eventos; na rede móvel, 47 transições e 17 eventos. As faixas de maior probabilidade tinham poucas observações e devem ser interpretadas com cautela. Não foram calculados intervalos por faixa.

[[FIGURE:04_calibracao|Figura 4. Calibração por faixas fixas da referência funcional e da rede móvel. Diagonal indica igualdade entre previsão média e frequência observada; asterisco indica menos de 20 transições. Os pontos não têm IC. Fonte: calibracao.csv, execução 00k.]]

## 6 Discussão

O resultado central é que a estrutura associativa visualizada não se traduziu em ganho preditivo conclusivo além de uma referência com memória funcional. Essa distinção é relevante para o desenho de modelos temporais: um grafo pode ser útil para explorar coocorrências e, ainda assim, acrescentar pouca informação ao desfecho escolhido.

Existem explicações possíveis, não demonstradas por estes experimentos. O histórico individual já contém informação sobre as doenças; as associações diretas com câncer foram pouco selecionadas pelo limiar; a rede populacional pode não representar heterogeneidade clínica; e o congelamento limita adaptação durante a validação. O pequeno número de eventos também reduz precisão. Esses fatores motivam hipóteses futuras, não justificam procurar limiares favoráveis na mesma validação.

No subgrupo, o estado câncer é positivo por definição. Produtos câncer–outra condição podem se reduzir ao estado dessa outra condição, ponderado pela rede, embora o modelo tenha sido ajustado na população geral. A baixa novidade informacional dessas combinações é uma consideração de desenho, não uma prova de irrelevância clínica do câncer ou de suas comorbidades.

Para séries temporais, a contribuição está em tratar o HRS como um painel de sequências curtas, parcialmente observadas e irregularmente espaçadas, com estados, memórias e redes disponíveis em cada origem. O experimento não é previsão de uma única série longa, nem modelagem contínua de contatos entre pessoas.

Quanto à explicabilidade, as redes descrevem associações populacionais; a decomposição do logit do modelo descreve seu cálculo individual. Nenhuma das duas estabelece causalidade. O protótipo existente permite inspecionar trajetórias e contribuições, mas seu benefício para a compreensão e decisão de profissionais ainda precisa ser testado em estudo específico, mantendo informação e previsão comparáveis entre formatos.

## 7 Limitações e transparência

A validação foi reutilizada e as extensões decorreram de resultados anteriores. Há apenas 39 eventos no subgrupo, sem confirmação externa ou aplicação prospectiva. Os dados são relatos sujeitos a erro de classificação, mudanças de questionário e entrevistas por representante. A inicialização histórica não transforma relatos em diagnósticos verificados.

O horizonte varia entre entrevistas. Óbito e perdas podem selecionar quais transições têm desfecho observado; não foram aplicados pesos amostrais, ponderação por censura ou riscos competitivos. As frequências não são estimativas populacionais ponderadas. Datas de entrevista não equivalem à data de disponibilização pública dos dados. O desenho prospectivo da transformação reduz uso explícito do futuro, mas não elimina limitações retrospectivas da fonte.

Phi é uma associação não ajustada. Limiarização e padronização influenciam os atributos; ausências também podem produzir indicadores úteis ao modelo. O bootstrap mantém redes e modelos fixos. Não foram avaliados efeito de tratamento, tipo ou estágio tumoral, transporte para o Brasil, benefício líquido clínico ou compreensão por médicos.

O processamento foi local e a comunicação dos resultados utiliza agregados. Código de pesquisa e testes com dados artificiais são distintos dos resultados empíricos do painel. As informações institucionais sobre aprovação ética aplicável, contribuições de autoria, financiamento e conflitos de interesse devem ser completadas pelos autores antes de submissão externa; não se presume dispensa ética.

## 8 Conclusão

Foi implementada e executada uma comparação temporal auditável entre histórico funcional, interações entre doenças e atributos de grafos estáticos e temporais no HRS. No subgrupo com histórico de câncer, as representações por grafos não demonstraram melhora conclusiva do Brier além do histórico funcional. O estudo mostra a necessidade de separar interpretação visual de relações e evidência de ganho preditivo. O resultado orienta a formulação de novos experimentos com avaliação independente, sem atribuir valor clínico a associações ou a pequenas diferenças pontuais.

## Disponibilidade e reprodutibilidade

As etapas 00h–00k, seus parâmetros, versões e resultados agregados são documentados no material suplementar local. O ambiente empírico registrou Python 3.14.4, pandas 3.1.1, NumPy 2.5.5 e scikit-learn 1.9.1. A reprodução exige os artefatos locais autorizados; faixas antigas de dependências não constituem um lock desse ambiente. Arquivos de configuração registram hashes das entradas agregadas e módulos.

O repositório privado hrs-functional-trajectories contém uma versão anterior do código. A extensão aqui descrita ainda precisa ser sincronizada e identificada por commit antes de uma entrega externa. Não se afirma que o código atualizado esteja publicado ou que microdados possam ser redistribuídos.

## Referências

1. RAND HRS Team. RAND HRS Longitudinal File 2022 V2: Documentation. Outubro de 2026. [Produto e documentação oficial](https://hrsdata.isr.umich.edu/data-products/rand-hrs-longitudinal-file-2022).

2. Westrick AC, Langa KM, Kobayashi LC. The association of health behaviors prior to cancer diagnosis and functional aging trajectories after diagnosis. Preventive Medicine Reports. 2023;31:102083. Publicado online em 2022. Título abreviado. [doi:10.1016/j.pmedr.2022.102083](https://doi.org/10.1016/j.pmedr.2022.102083).

3. Gravina A, Bacciu D. Deep learning for dynamic graphs: models and benchmarks. IEEE Transactions on Neural Networks and Learning Systems. 2024. [doi:10.1109/TNNLS.2024.3379735](https://doi.org/10.1109/TNNLS.2024.3379735). Versão consultada: arXiv:2307.06104v4.

4. Mullins MA, Kler JS, Eastman MR, Kabeto M, Wallner LP, Kobayashi LC. Validation of self-reported cancer diagnoses using Medicare diagnostic claims in the U.S. Health and Retirement Study, 2000–2016. Cancer Epidemiology, Biomarkers & Prevention. 2022;31(1):287–292. [doi:10.1158/1055-9965.EPI-21-0835](https://doi.org/10.1158/1055-9965.EPI-21-0835).

5. Collins GS et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ. 2024;385:e078378. [doi:10.1136/bmj-2023-078378](https://doi.org/10.1136/bmj-2023-078378).
