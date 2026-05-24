# Briefing Estratégico: Claude Impact Lab – Rio de Janeiro
**Foco Temático: Segurança Pública**  
**Equipe: Desenvolvimento + Economia + Ciência de Dados**  
**Compilado em: 23 de maio de 2026**  
**Fonte: Agente de pesquisa Claude Code (34 min, 54 chamadas de ferramentas)**

---

## 1. O Hackathon em Resumo

**O que é:**  
O Claude Impact Lab é a marca de hackathons cívicos das Claude Communities, patrocinada pela Anthropic. A edição do Rio é a primeira edição brasileira, conectando construtores de IA com problemas reais de governos locais usando dados municipais abertos.  
*(Fonte: [Tempo Real RJ](https://temporealrj.com/rio-hackathon-claude-anthropic-ia/); [lu.ma/3i0rkczm](https://luma.com/3i0rkczm))*

**Data e local (CONFIRMADO):**
- Domingo, 24 de maio de 2026
- Porto Maravalley — Região Portuária, Rio de Janeiro
- Parceria com a Secretaria Municipal de Desenvolvimento Econômico

**Formato:**
- Hackathon de um dia inteiro
- Equipes de até 5 pessoas, multidisciplinares incentivadas
- Conduzido integralmente em português brasileiro
- Aberto a todos os perfis; não exige experiência prévia em programação ou IA

**Cronograma (estrutura confirmada para o formato):**
1. Kickoff — apresentação do desafio e dos dados
2. Construção — desenvolvimento com mentores disponíveis
3. Demos finais — apresentação para banca de líderes de IA e autoridades municipais
4. Premiação e networking

**Critérios de avaliação:**  
Divulgados no dia. Com base em San Diego, os eixos implícitos são: impacto no mundo real, execução técnica, criatividade e usabilidade. As melhores soluções serão doadas para a cidade.

**Organizadores:**
- Anfitrião principal: João Lisboa (co-fundador Taicor, Claude Community Ambassador Brasil)
- Co-anfitriões: Luiz Guilherme Gama, Hannah Rabe
- Patrocinadores: Visagio, VTex, Segura, Taicor, CCPar, Maravalley

> **⚠️ Inferência:** A edição San Diego premiou todos os participantes com US$ 50 em créditos de API e a equipe vencedora com US$ 500. Não há confirmação de premiação equivalente para o Rio.

---

## 2. Lições de Edições Anteriores

| Edição/Cidade | Projeto Destacado | Acessibilidade | Simplicidade | Visualização | Dados | Impacto Social | Viabilidade Técnica |
|---|---|---|---|---|---|---|---|
| San Diego (mar/2026) | Ferramenta de avaliação de localização de negócios usando dados municipais | Alta — para residentes e comerciantes comuns | Alta — interface conversacional sem jargão técnico | Média — foco em resultado acionável | Dados reais da cidade (alvará, zoneamento, incidentes) | Alta — resolve dor concreta de empreendedores | Alta — protótipo funcional em 1 dia |
| San Diego (mar/2026) | Sistema de rastreamento de qualidade da água | Baixa para leigos | Alta — alertas simples | Alta — mapa temporal | Dados públicos de monitoramento ambiental | Alta — saúde pública | Alta |
| San Diego (mar/2026) | Assistente de busca de alvarás e permissões | Alta — qualquer cidadão usa | Muito alta — chatbot em linguagem natural | Baixa | Registros de permissão municipais | Média-alta — reduz burocracia | Alta |
| Built with Opus 4.6 (global, 2025–2026) | CrossBeam — automação de revisão de alvarás de construção (CA) | Alta — construtor sem código | Muito alta — builder não escreveu código | N/A | Registros com 90%+ de rejeição | Muito alta — adoção municipal real (Buena Park) | Alta — 30h de construção |
| Built with Opus 4.6 (global, 2025–2026) | TARA — avaliação de infraestrutura via câmera de carro (Uganda) | Alta — dashcam comum | Alta — input simples, output estruturado | Alta — inclui equity scoring geográfico | Imagens + dados geoespaciais | Muito alta — elimina backlog de semanas em 5h | Alta |
| Hackathon Seg. Pública MJ (Brasil, mar/2025) | Mais Seguro — plataforma colaboração cidadão-polícia | Alta — app cidadão | Alta | Baixa | Dados de denúncias | Alta | Média |

*Fontes: [Luma San Diego](https://luma.com/6ok9h92y) · [LinkedIn Claude Impact Lab San Diego](https://www.linkedin.com/posts/claude_claude-impact-lab-san-diego-activity-7438290857453260800-MUCS) · [Claude Blog Opus 4.6](https://claude.com/blog/meet-the-winners-of-our-built-with-opus-4-6-claude-code-hackathon) · [MJ Hackathon Seg. Pública](https://www.gov.br/mj/pt-br/assuntos/noticias/vencedores-do-hackathon-de-seguranca-publica-sao-premiados-em-cerimonia-no-palacio-da-justica)*

---

## 3. Padrões dos Vencedores

- **Resolvem um problema que existia antes do hackathon** — o dado era público; a interface nunca havia existido. CrossBeam atacou 90% de rejeição de alvarás. TARA resolveu backlog real de avaliação de infraestrutura.
- **Entregam algo que funciona ao vivo** — a banca avalia o que vê funcionando, não o que imagina que poderia funcionar. Protótipo demonstrável é obrigatório.
- **Têm usuário final claro e identificável** — não "a população em geral", mas "o gestor que quer ver ocorrências em mapa" ou "o residente que quer saber se o bairro está seguro à noite".
- **Usam dados reais da cidade** — não datasets sintéticos ou nacionais genéricos. Conexão com o datalake municipal é critério diferenciador explícito.
- **São construídos por perfis não-técnicos ou multidisciplinares** — quatro dos cinco vencedores do Built with Opus 4.6 não eram programadores profissionais. A banca valoriza domínio do problema tanto quanto execução técnica.

---

## 4. Bases de Dados da Prefeitura do Rio para Segurança Pública

| Base | Órgão | Conteúdo | Granularidade | Atualização | Formato | Link |
|---|---|---|---|---|---|---|
| Chamados do 1746 | Escritório de Dados / Central 1746 | Solicitações de serviços desde 2011: categoria, tipo, endereço, status, data. Inclui chamados de iluminação, desordem urbana, Guarda Municipal | Por chamado individual com endereço | Diária | BigQuery — `datario.adm_central_atendimento_1746.chamado` | [Docs API](https://docs.dados.rio/api-reference/citizen/obter-chamados-do-1746-do-cidadão) |
| Bairros do Rio | IPP / Escritório de Dados | Polígonos geográficos dos bairros municipais | Por bairro | Estático | BigQuery — `datario.dados_mestres.bairro` | [GitHub desafio](https://github.com/prefeitura-rio/desafio-junior-data-scientist) |
| Logradouros georreferenciados | IPP | Endereços georreferenciados completos | Por logradouro | Regular | BigQuery / API REST | [Data.rio API](https://www.data.rio/datasets/PCRJ::logradouros/api) |
| CIVITAS | Casa Civil / SEOP | 1.500 radares, 3.800+ câmeras, 6,1M leituras de placas/dia, alertas, mapas de calor. Integra 20 secretarias + Disque Denúncia + 1746 + Fogo Cruzado | Tempo real | Contínua | **Sem API pública confirmada** — sistema operacional interno | [casacivil.prefeitura.rio/civitas](https://casacivil.prefeitura.rio/civitas/) |
| Iluminação Pública RIOLUZ | RIOLUZ | Pontos de iluminação, tipo de lâmpada, estado de conservação | Por ponto / logradouro | Não publicado | **Não confirmado como dataset aberto** — verificar no kickoff | [rioluz.prefeitura.rio](https://rioluz.prefeitura.rio/) |
| Guarda Municipal | SEOP / GM-Rio | 7.312 guardas, 35 unidades, 15 Inspetorias, 11 UPOs, 9 Grupos Especiais | Por unidade | Não publicado | **Não confirmado como dataset aberto** | [guardamunicipal.prefeitura.rio](https://guardamunicipal.prefeitura.rio/) |

**Complementos não-municipais (marcar explicitamente como complemento):**

| Base | Nota |
|---|---|
| Fogo Cruzado (OSC) — tiroteios geo-referenciados desde jul/2016, 40+ indicadores, pacotes Python/R crossfire | **[COMPLEMENTO — não municipal]** Requer autorização para API. CC license. 90+ pesquisas acadêmicas. |
| ISP Dados Abertos — ocorrências por AISP/CISP, homicídios, letalidade policial | **[COMPLEMENTO — estadual]** |

> **⚠️ Observação crítica:** Os dados municipais diretamente ligados a segurança (CIVITAS, GM-Rio, RIOLUZ) não têm API pública confirmada. O dado confirmado e aberto é o **1746**. Pergunte no kickoff quais datasets específicos serão liberados — é provável que dados inéditos sejam disponibilizados no evento.

---

## 5. Stack Técnica Viável em 24–48h

### O que cada ferramenta faz

**Datalake dados.rio + BigQuery**
- Acesso via Python (`google-cloud-bigquery`) ou SQL direto no console
- Tabela central: `datario.adm_central_atendimento_1746.chamado` — desde 2011, endereço + categoria + status
- JOIN com `datario.dados_mestres.bairro` para agregar por bairro e produzir mapas
- Query de 5 minutos: `SELECT subtipo, COUNT(*) as n, bairro FROM chamado GROUP BY 1,3` já produz heatmap de desordem
- Acesso gratuito com conta Google Cloud (sandbox BigQuery)

**Claude Code com Vertex AI** ([docs.dados.rio](https://docs.dados.rio/ferramentas/claude-code-usuario))
- Acesso via credencial `rj-ia-desenvolvimento` (solicitado via Discord #dev-ia da Prefeitura — confirmar disponibilidade para hackathon)
- Usos diretos: gerar código Python/SQL de análise em português, construir interface conversacional sobre BigQuery, documentar código, gerar narrativa dos resultados para demo
- Alternativa imediata: API Claude via chave Anthropic fornecida pela organização no evento

**Metabase** ([dados.rio/post/metabase](https://www.dados.rio/post/metabase-centralizando-analises-de-dados-na-prefeitura-do-rio))
- BI open-source conectado ao datalake
- Montar dashboards interativos sem código
- Entregável visual para banca: dashboard ao vivo com filtros por bairro e linha do tempo é mais convincente que notebook Jupyter

### Fluxo operacional sugerido (24h)

| Período | Tarefa |
|---|---|
| Hora 0–2 | Ingestão — BigQuery query no 1746, limpeza em pandas, categorias relevantes para segurança identificadas |
| Hora 2–5 | EDA espacial — JOIN com bairros, mapa de calor via folium/plotly |
| Hora 5–10 | Construção da app — Claude Code gera interface web ou chatbot conversacional sobre os dados |
| Hora 10–14 | Integração Fogo Cruzado — sobrepor tiroteios aos chamados 1746 |
| Hora 14–20 | Dashboard Metabase + narrativa da demo |
| Hora 20–24 | Ensaio da apresentação e refinamento |

---

## 6. O Que Já Existe — Iniciativas Correlatas e Lacunas

**CIVITAS (jun/2024 — Municipal)**  
Maior sistema de vigilância urbana do país: 3.800+ câmeras, 1.500 radares, 6,1M leituras de placas/dia, IA para reconhecimento facial, integra 20 secretarias. ([Prefeitura.rio](https://prefeitura.rio/cidade/prefeitura-do-rio-expande-civitas-que-tera-20-mil-cameras-ate-2028/))  
> Lacuna: Sistema fechado sem acesso público. Uma camada de transparência sobre o que o CIVITAS reporta — sem expor dados sensíveis — seria relevante e diferenciada.

**COR-Rio (Municipal)**  
Centro de monitoramento urbano 24h: câmeras, sensores, alertas climáticos, trânsito e segurança.  
> Lacuna: Dados operacionais não são públicos em tempo real para pesquisa cívica.

**Fogo Cruzado (OSC, desde 2016)**  
Maior banco de dados sobre violência armada da América Latina. 40+ indicadores geo-referenciados. Base de 90+ pesquisas acadêmicas. ([api.fogocruzado.org.br](https://api.fogocruzado.org.br/))  
> Lacuna: Dados ricos sem interface simples para gestores municipais ou cidadãos consultarem sem conhecimento técnico. Maioria dos usos é acadêmica.

**Leme Lab (parceiro da Prefeitura, desde 2024)**  
Laboratório de políticas públicas, assistência técnica em segurança municipal baseada em dados. Conduziu o primeiro RCT de hot spot policing no Paraná. ([lemelab.org](https://www.lemelab.org/en))  
> Lacuna: Análises para dentro da Prefeitura; sem ferramenta pública de monitoramento de impacto de intervenções.

**Central 1746 (Municipal, dados desde 2011)**  
Dados no datalake BigQuery, mais de 1.000 serviços.  
> Lacuna: Dados disponíveis mas sem ferramenta pública de consulta intuitiva para cidadão ou gestor acompanhar padrões de desordem urbana ao longo do tempo no próprio bairro.

---

## 7. Base na Literatura

### Achados robustos com evidência causal

**Iluminação pública reduz crimes (evidência forte)**
- **NYC RCT (Chalfin et al., 2019 / NBER WP 25798):** Único RCT em segurança pública urbana com iluminação. 80 projetos habitacionais do NYCHA randomizados. Resultado: redução de 36% nos crimes noturnos ao ar livre. ([NBER](https://www.nber.org/papers/w25798))
- **Mitre-Becerril (2025 / SSRN 5366693):** Retrofitting LED em Mesa, AZ — DiD escalonado com 8 anos de dados. Queda em furtos e pequenos delitos. ([SSRN](https://doi.org/10.2139/ssrn.5366693))
- **Arvate et al. (2018):** Programa Luz para Todos no Brasil — quasi-experimental por descontinuidade de elegibilidade. Aumentar cobertura elétrica de 0→100% associado a redução de ~92 homicídios/100k. ([Plataforma BID](https://plataformadeevidencias.iadb.org/en/casos-avaliados/light-all-program))
- **Campbell Collaboration / BID:** Meta-análise de 13 programas globais. Redução média de 21% no total de crimes com melhoria de iluminação. ([Comunitas](https://comunitas.org.br/o-poder-da-iluminacao-publica-na-reducao-da-violencia-e-na-construcao-de-cidades-mais-justas-2/))

**Hot spot policing (evidência robusta no Brasil)**
- **Revisão sistemática FGV/RAP (Vargas et al.):** 13.352 estudos analisados, 41 incluídos. 8 tipos de programas comprovadamente efetivos para reduzir homicídios no Brasil. Hot spot policing entre os mais robustos. ([RAP/FGV](https://periodicos.fgv.br/rap/article/view/83356))
- **Leme Lab RCT (Paraná, 2024–2025):** Primeiro RCT de hot spot policing no Brasil — 422 segmentos de rua randomizados. ([Leme Lab](https://www.lemelab.org/en))

**UPPs — evidência mista, efeito positivo no curto prazo**
- **DiD e controle sintético (FGV):** redução de homicídios, furtos e roubos nos territórios das UPPs com spillover para vizinhos (1999–2016). ([FGV RBE](https://periodicos.fgv.br/rbe/article/view/79962))
- Revisão sistemática (BIB-ANPOCS): queda em letalidade policial foi o impacto mais consistente.

### Métodos de avaliação causal aplicáveis

| Método | Quando usar | Exemplo aplicável ao Rio |
|---|---|---|
| DiD | Intervenção implementada em momentos diferentes em diferentes bairros | LED da RIOLUZ em alguns bairros → impacto nos chamados 1746 de desordem |
| RDD | Há limiar de elegibilidade arbitrário | Bairros acima/abaixo de índice de vulnerabilidade que receberam programa GM-Rio |
| Controle Sintético | Intervenção em poucos territórios | Impacto de UPP em bairro específico vs. bairros sintéticos |
| IV | Variável que afeta tratamento mas não resultado diretamente | Chuva como instrumento para patrulhamento |
| Hot spot mapping | Priorização (não causalidade) | Identificar blocos com alta concentração 1746 + Fogo Cruzado |

---

## 8. Propostas de Projeto

### Proposta 1 — MapaCarioca 1746: Painel de Desordem Urbana por Bairro ⭐ RECOMENDADA

**Problema:** O 1746 tem dados desde 2011 com endereço e categoria — mas não existe interface intuitiva que mostre, por bairro, quais chamados ligados a ordem pública são mais frequentes, em que horários e com que tendência. O dado existe; a interface nunca foi construída.

**Dados:** `datario.adm_central_atendimento_1746.chamado` + `datario.dados_mestres.bairro`. Filtro: iluminação pública, desordem, invasão de área, perturbação de sossego, grafite/pichação.

**Abordagem técnica:**
1. Query BigQuery agrega chamados por bairro × mês × subcategoria de desordem
2. Mapa coroplético interativo (folium ou Plotly) por bairro
3. Interface conversacional via Claude: usuário digita "como está a Tijuca nos últimos 3 meses?" → Claude gera SQL, executa via BigQuery API, retorna visualização + narrativa em português
4. Série temporal por bairro com decomposição sazonal simples

**Ferramentas do ecossistema:** BigQuery (dados), Claude API (interface conversacional + narrativa), Metabase (dashboard público para demo)

**Papel de cada competência:**
- Dev: integração BigQuery ↔ Claude API, deploy da interface web ou Streamlit
- Economia: definição das categorias de desordem relevantes, análise de série temporal, interpretação dos padrões (sazonalidade, efeito de eventos)
- Ciência de dados: agregação espacial, visualização, identificação de outliers e tendências

**Entregável demonstrável:** Dashboard ao vivo: mapa do Rio + linha do tempo por bairro + chatbot que responde perguntas em português. A banca digita qualquer bairro e vê os dados instantaneamente.

**Por que pontuaria alto:** Usa dados municipais reais do datalake; interface 100% em português acessível a qualquer cidadão; demonstrável ao vivo em segundos; resolve lacuna real; alta aderência ao padrão San Diego.

**Estratégia de identificação causal:** DiD para avaliar se mudanças na escala de patrulha da GM-Rio (ou instalação de LED pela RIOLUZ) afetam volume de chamados de desordem em bairros tratados vs. controle — a ferramenta gera os dados necessários para a análise ex-post.

---

### Proposta 2 — LuzCerta: Priorização de Iluminação Pública por Risco

**Problema:** Pesquisas causais estabelecem que iluminação reduz crimes. A RIOLUZ tem dados de pontos por logradouro. O 1746 registra "lâmpada apagada" com endereço preciso. Não existe ferramenta que cruze (a) pontos com defeito, (b) concentração de desordem nas mesmas quadras, e (c) priorize manutenção proativa pelo risco.

**Dados:** 1746 (tipo "iluminação pública") + Fogo Cruzado API [COMPLEMENTO] + `datario.dados_mestres.bairro` + dados RIOLUZ (a confirmar no kickoff)

**Abordagem técnica:**
1. Identificar logradouros com alta concentração de chamados de iluminação com defeito
2. Sobrepor com densidade de tiroteios do Fogo Cruzado (buffer de 500m)
3. Score de risco = f(chamados de iluminação recentes, densidade de tiroteios, horário noturno) por logradouro
4. Ranking de prioridade para RIOLUZ
5. Mapa interativo por bairro para gestor municipal

**Ferramentas do ecossistema:** BigQuery (chamados 1746), Fogo Cruzado API, Claude Code (análise espacial + score + narrativa), Metabase (mapa + ranking)

**Papel de cada competência:**
- Dev: integração Fogo Cruzado API + BigQuery, cálculo do score, interface
- Economia: design do score com fundamento na literatura (mecanismo iluminação → crime), interpretação dos coeficientes implícitos
- Ciência de dados: análise geoespacial, buffer analysis, normalização dos índices, visualização cartográfica

**Entregável demonstrável:** Mapa do Rio colorido por score de risco de iluminação + ranking dos Top 20 logradouros a priorizar.

**Estratégia de identificação causal:** DiD escalonado — RIOLUZ instala LEDs em grupos de logradouros em datas diferentes → comparar variação em chamados de desordem e registros Fogo Cruzado antes e depois do tratamento, controlando por sazonalidade e bairro.

---

### Proposta 3 — GuardaSmarter: Alocação Baseada em Dados para a GM-Rio

**Problema:** A GM-Rio tem 7.312 guardas e 35 unidades operacionais, mas não há ferramenta que mostre como os chamados de ordem pública se distribuem no tempo e no espaço por turno.

**Dados:** 1746 (categorias: perturbação de sossego, desordem, invasão, vandalismo) + `datario.dados_mestres.bairro` + dados GM-Rio de patrulhamento (a confirmar no kickoff)

**Abordagem técnica:**
1. Clustering espacio-temporal (DBSCAN ou K-means) em chamados de desordem por turno (manhã/tarde/noite) e dia da semana
2. Mapa de calor animado por hora do dia
3. Sugestão de alocação por turno
4. Simulação: "se realocarmos X guardas de Y para Z, qual % da demanda histórica seria coberto?"
5. Interface Claude: gestor descreve restrição em português e recebe sugestão de alocação

**Ferramentas do ecossistema:** BigQuery, Claude Code (clustering + interface em linguagem natural), Metabase (mapa de calor por turno + tabela de recomendação)

**Estratégia de identificação causal:** RCT natural — se a Prefeitura realocar guardas com base nas recomendações em algumas regiões mas não em outras, o comparativo antes-depois × tratado-controle produz um DiD válido.

---

### Proposta 4 — SentinelBairro: Assistente de Segurança para Presidentes de Bairro

**Problema:** Presidentes de associações de bairro e vereadores precisam entender o que acontece em segurança no seu território sem saber SQL ou BigQuery.

**Dados:** 1746 + Fogo Cruzado API [COMPLEMENTO] + `datario.dados_mestres.bairro`

**Abordagem técnica:**
1. Text-to-SQL: usuário digita em português → Claude traduz para query BigQuery → resultado retorna como texto + gráfico
2. Relatório semanal automático por bairro gerado pelo Claude
3. Alertas configuráveis: "me avise se chamados de iluminação no Catumbi subirem 20% esta semana"
4. Dashboard Metabase como painel visual complementar

**Entregável demonstrável:** Chatbot ao vivo — banca digita qualquer bairro do Rio e recebe resumo de segurança + gráfico de tendência + comparação com mês anterior.

---

### Proposta 5 — VioLens: Painel de Transparência sobre Violência Armada Municipal

**Problema:** O Fogo Cruzado tem dados ricos de tiroteios desde 2016, mas não há ferramenta que cruze com iniciativas da Prefeitura Municipal. A sobreposição revela se ações municipais estão sendo alocadas nos territórios de maior violência.

**Dados:** Fogo Cruzado API [COMPLEMENTO] + 1746 + `datario.dados_mestres.bairro` + dados CIVITAS/GM-Rio (a confirmar)

**Abordagem técnica:**
1. Download histórico Fogo Cruzado via `crossfire` (Python) para Rio de Janeiro (2016–2026)
2. Agregação por bairro × semestre → série temporal de tiroteios
3. Sobreposição com chamados 1746 de desordem → correlação espacial
4. Análise de convergência: bairros com alta violência armada recebem mais atenção municipal?
5. Painel de transparência: cidadão vê se a Prefeitura está priorizando os bairros certos

**Ferramentas do ecossistema:** Fogo Cruzado API + crossfire, BigQuery, Claude Code (correlação espacial + narrativa), Metabase (painel público de transparência)

**Estratégia de identificação causal:** IV — explorar variação exógena em cobertura do Fogo Cruzado para identificar efeito causal de visibilidade de dados sobre resposta da Prefeitura.

---

## 9. Recomendação Final

**Priorize a Proposta 1 — MapaCarioca 1746.**

É a proposta com maior probabilidade de sucesso dado o contexto. O dado central — `datario.adm_central_atendimento_1746.chamado` — é confirmado, público, acessível sem pré-autorização via BigQuery, disponível desde 2011, esquema documentado no GitHub da Prefeitura. Não depende de acesso a sistemas sensíveis (CIVITAS sem API pública) nem de autorização prévia (Fogo Cruzado requer cadastro). A interface conversacional em português via Claude + dashboard Metabase é demonstrável ao vivo em segundos para qualquer membro da banca, sem preparação técnica do avaliador. Atende ao padrão central dos vencedores: "o dado era público; a interface nunca existiu." Os três perfis têm papel claro e paralelo — dev faz a interface, economia define as categorias e interpreta os padrões, ciência de dados faz o mapa e a série temporal. Nenhum bloqueia o outro.

**Pivot imediato:** Se no kickoff a Prefeitura liberar dados de iluminação (RIOLUZ) ou patrulhamento (GM-Rio), mude para a **Proposta 2 (LuzCerta)** — mesma base técnica, maior impacto acionável e fundamentação causal mais forte. A Proposta 3 (GuardaSmarter) é segunda melhor opção se dados de patrulhamento forem liberados.

---

*Fontes principais: [Luma Rio](https://luma.com/3i0rkczm) · [Luma San Diego](https://luma.com/6ok9h92y) · [Claude Blog Opus 4.6](https://claude.com/blog/meet-the-winners-of-our-built-with-opus-4-6-claude-code-hackathon) · [dados.rio](https://www.dados.rio/datalake) · [docs.dados.rio Claude Code](https://docs.dados.rio/ferramentas/claude-code-usuario) · [CIVITAS](https://casacivil.prefeitura.rio/civitas/) · [Fogo Cruzado API](https://api.fogocruzado.org.br/) · [GitHub Prefeitura Rio](https://github.com/prefeitura-rio/desafio-junior-data-scientist) · [NBER WP 25798](https://www.nber.org/papers/w25798) · [RAP/FGV segurança](https://periodicos.fgv.br/rap/article/view/83356) · [Leme Lab](https://www.lemelab.org/en) · [FGV RBE UPP](https://periodicos.fgv.br/rbe/article/view/79962)*
