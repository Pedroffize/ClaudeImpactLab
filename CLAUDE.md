# CompStat Rio: Plataforma de Inteligência Territorial

> **CLAUDE.md** | Arquivo mestre de contexto do projeto. Leia este arquivo inteiro no início de cada sessão antes de escrever ou alterar qualquer código.
> 
> **Projeto:** Claude Impact Lab. **Time:** 4 integrantes. **Cliente de referência:** Prefeitura do Rio de Janeiro (Secretaria-Geral do CompStat).
> 
> **Meta do entregável:** produto funcional e implantável. O critério de pronto é “a prefeitura conseguiria usar amanhã”.
> 
> **Status dos dados:** pendentes. Os dados reais serão enviados pelo Pedro. Até lá, desenvolver com dados sintéticos (ver seção 14).

-----

## 1. Visão geral em 30 segundos

O CompStat Rio é uma plataforma que cruza automaticamente múltiplas camadas de dados de segurança pública municipal, calcula um score de prioridade por trecho viário e gera um relatório de decisão que a equipe humana valida antes de agir. O sistema responde a quatro perguntas operacionais (onde, quando, como patrulhar e quais fatores urbanos resolver) e pré-popula uma matriz de responsabilização por órgão municipal.

A inteligência central está em sobrepor três camadas no mesmo ponto do mapa: onde o crime acontece, qual condição urbana o facilita e qual a dinâmica criminal por trás dele. Quando as três coincidem no mesmo segmento, o sistema marca um “bingo” e atribui prioridade máxima.

## 2. O problema

A operação atual do CompStat depende de cruzamento manual de dados para as 22 áreas monitoradas. Os três sintomas:

1. **Volume e silos.** Dados quantitativos (ocorrências), qualitativos (denúncias e relatórios), fatores urbanos e posições da Força Municipal vivem em sistemas isolados.
1. **Déficit de cruzamento.** Não existe um mecanismo que sobreponha automaticamente as camadas de informação (mancha criminal, dinâmica criminal e fatores urbanos).
1. **Fadiga humana.** A compilação mecânica de tabelas consome o tempo que deveria ir para interpretação e decisão estratégica das 22 áreas.

O produto ataca exatamente o passo de compilação e cruzamento, devolvendo tempo de análise à equipe.

## 3. Premissa do produto

A premissa que orienta toda a lógica: o ambiente urbano degradado é o facilitador estrutural da criminalidade oportunista. Iluminação deficiente, vegetação encobrindo postes, calçada obstruída e retenção de tráfego criam condições para furtos e roubos no espaço público. Por isso o produto trata fatores urbanos como variável de primeira classe, no mesmo nível das ocorrências criminais.

Cinco eixos sustentam o modelo:

1. Mapeamento sistemático de dados criminais (furtos e roubos por segmento e horário).
1. Foco territorial em 22 áreas prioritárias com base na mancha criminal.
1. Emprego estratégico da Força Municipal com planejamento operacional baseado em dados.
1. Mapeamento dos fatores urbanos de incidência criminal, com coordenação entre órgãos municipais.
1. Reuniões de tomada de decisão e responsabilização.

## 4. Glossário de domínio (LEIA ANTES DE CODAR)

O Claude Code não deve inferir o significado destes termos. Eles têm definição fixa neste projeto.

- **CompStat:** modelo de gestão baseado em reuniões periódicas de monitoramento, prestação de contas e decisão por dados. Origem no NYPD (Nova York). A versão carioca é municipal e integra diferentes órgãos da prefeitura, com foco em furtos e roubos no espaço público.
- **FM (Força Municipal):** força de segurança municipal do Rio. Atua no ordenamento urbano e na proteção do espaço público. É o ator operacional que recebe rota, horário e modalidade de patrulhamento.
- **Mancha criminal:** concentração geográfica de ocorrências (dados Lat/Long), com horários de pico e densidade de roubos e furtos.
- **Fatores urbanos:** condições ambientais que facilitam o crime oportunista. Exemplos: iluminação deficiente, obstrução de calçada, vegetação encobrindo iluminação, mobiliário urbano, retenção de tráfego. O escopo inicial é de 20 fatores.
- **Dinâmica criminal:** o “como” e o “quem” do crime. Inclui modus operandi, perfis de vítimas, rotas de fuga, pontos de receptação, uso de arma branca e controle territorial.
- **Disque Denúncia (DD):** canal de denúncias. Dado em texto livre, com valor para entender dinâmica criminal, rotinas e suspeitos.
- **RELINT:** Relatório de Inteligência produzido pela FM. Texto livre, qualitativo. Valor para modus operandi, rotas de fuga e domínio territorial.
- **ORCRIM:** Organização Criminosa. Aparece na camada de controle territorial.
- **Polígonos FM:** áreas operacionais delimitadas da Força Municipal. Formato geoespacial (Shapefile ou GeoJSON). Definem o patrulhamento prioritário.
- **Bingo:** termo do produto para o ponto de interseção máxima entre as três camadas (mancha criminal, fator urbano e dinâmica criminal) no mesmo segmento viário. Quanto mais camadas coincidem, maior o score.
- **Score de prioridade:** nota de 0 a 10 atribuída a um trecho crítico, proporcional ao número e ao peso das coincidências detectadas. Toda nota precisa de justificativa legível.
- **Matriz de responsabilização:** tabela que vincula cada problema a um órgão municipal responsável, com prazo e indicador. Preenchida na reunião e cobrada na seguinte. Após 90 dias, aplica-se protocolo de revisão para definir permanência ou saída do território.
- **Subprefeituras:** responsáveis por mapear e resolver fatores urbanos.
- **SEOP:** órgão de ordenamento público citado nas ações de rua (confirmar nomenclatura exata com o cliente).
- **Secretaria-Geral do CompStat:** prepara as reuniões, que são presididas pelo Prefeito.
- **22 áreas:** unidades territoriais monitoradas, divididas entre as Bases Litorânea, Oeste e Norte, com expansão faseada.

## 5. Conceito central: o “bingo” espacial e qualitativo

A regra de ouro do produto. Três camadas são modeladas sobre o mesmo mapa:

1. **Mancha Criminal:** horários de pico e alta densidade de roubos e furtos (dados Lat/Long).
1. **Fator Urbano:** iluminação deficiente, obstrução de calçada, retenção de tráfego.
1. **Dinâmica Criminal:** rota de fuga, receptação ativa, criminalidade oportunista, uso de arma branca.

Quando as camadas se sobrepõem no mesmo segmento viário, o sistema dispara um “bingo”. A regra de pontuação: o score aumenta proporcionalmente ao número de camadas sobrepostas naquele segmento. O resultado vai direto ao mapa como identificador visual de coincidência.

Exemplo de saída esperada: “Score 8.5/10. Trecho X possui roubos noturnos, poste apagado e rota de fuga citada em RELINT.”

## 6. Arsenal de dados: as 5 fontes de ingestão

|# |Fonte                |Tipo                |Formato técnico      |Valor analítico                                       |
|--|---------------------|--------------------|---------------------|------------------------------------------------------|
|01|Ocorrências Criminais|Quantitativo        |CSV ou API (Lat/Long)|Heatmaps e análise temporal de furtos e roubos        |
|02|Polígonos FM         |Geoespacial         |Shapefile ou GeoJSON |Delimitação de patrulhamento prioritário              |
|03|Fatores Urbanos      |Quali e geo         |Estruturado          |Mapeamento de iluminação, vegetação, mobiliário urbano|
|04|Disque Denúncia      |Quantitativo e texto|Texto livre          |Dinâmica criminal, rotinas, suspeitos                 |
|05|RELINTs (FM)         |Qualitativo         |Texto livre          |Modus operandi, rotas de fuga, domínio territorial    |

As fontes 04 e 05 são texto não estruturado e exigem o pipeline de LLM. As fontes 01 a 03 alimentam diretamente a camada geoespacial.

## 7. Motor de IA

O motor tem duas partes que rodam em sequência.

### 7.1 Parte 1: extração e estruturação

**Requisito:** a plataforma lê o texto bruto (Disque Denúncia e RELINTs) e analisa a dinâmica criminal predominante de forma autônoma.

Entrada: documento não estruturado. Saída: JSON estruturado com cinco campos.

1. **Modalidade criminal:** predominância na área analisada.
1. **Modus operandi:** forma de abordagem, perfis de vítimas, uso de cobertura.
1. **Rotas de fuga:** vias de escoamento rápido de bens.
1. **Pontos de receptação:** locais ativos de repasse.
1. **Controle territorial:** influência de organizações criminosas (ORCRIM).

Implementação: usar Claude com structured output ou tool use para garantir JSON válido. Toda extração deve registrar a fonte de origem (DD ou RELINT) para rastreabilidade.

### 7.2 Parte 2: interseção e score geoespacial

**Requisito:** o sistema sobrepõe polígonos operacionais, câmeras, crimes e fatores urbanos para calcular a prioridade.

Saídas:

1. **Score de prioridade:** ranqueamento automático de trechos críticos. Mais coincidências, maior o peso.
1. **Justificativa algorítmica:** texto legível explicando a nota (exemplo do bingo na seção 5).
1. **Sinalização visual:** identificadores de coincidência gerados direto no mapa.

Esta parte é geometria, não LLM. A recomendação técnica está na seção 11: modelar como query espacial em PostGIS.

## 8. As 4 perguntas do CompStat e as respostas algorítmicas

O produto existe para automatizar a resposta destas quatro perguntas.

|Pergunta do CompStat                                                                   |Resposta algorítmica                                                                            |
|---------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
|Qual deve ser a rota da FM com base nos locais de maior incidência criminal?           |Sugestão preditiva de rota baseada em mapa de calor, considerando que dados reais são restritos.|
|Qual deve ser o horário de patrulhamento da FM com base no horário de maior incidência?|Análise temporal automatizada para sugerir alocação otimizada de horário.                       |
|Qual deve ser o modelo de emprego da FM com base na dinâmica criminal?                 |Prescrição de modalidade (moto, viatura, a pé) cruzada com modus operandi.                      |
|Como os órgãos devem resolver os fatores urbanos relevantes?                           |Match automático entre fator identificado e órgão municipal responsável.                        |

## 9. Entregáveis do produto

### 9.1 Relatório automatizado: os 6 módulos

1. **Resumo Executivo:** respostas geradas por IA para as 4 perguntas.
1. **Mapa de Calor:** concentração de ocorrências sobreposta aos Polígonos FM.
1. **Análise Temporal:** distribuição e identificação de horários de pico.
1. **Dinâmica Criminal:** conteúdo sintético gerado via LLM a partir de RELINTs e Disque Denúncia.
1. **Fatores Urbanos:** fatores de incidência mapeados pelas Subprefeituras.
1. **Painel de coincidências e Plano de Ação:** tabela de “bingos” priorizada e matriz de responsabilização pré-populada, aguardando validação humana final.

### 9.2 Output visual: espaço e tempo

- **Visão espacial integrada:** gerar dinamicamente manchas de calor sobre trechos críticos e plotar rotas operacionais e câmeras.
- **Visão temporal integrada:** gerar matrizes de pico automaticamente, por exemplo identificar sobreposições às 19h de quartas-feiras.

## 10. O ciclo operacional (o loop do produto)

O produto opera em integração contínua, em cinco passos:

1. **Ingestão:** atualização periódica das fontes (ocorrências, Disque Denúncia, fatores urbanos).
1. **Motor IA:** cruzamento, síntese, geração de bingos e rascunho de área.
1. **Refino Humano:** revisão e validação pela equipe CompStat. Passo obrigatório.
1. **Decisão:** apresentação, cobrança e formalização de compromissos na reunião semanal.
1. **Ação Urbana:** execução na rua (poda, patrulha, ordenamento) e atualização de status.

O resultado final esperado: análise automatizada das 22 áreas a cada ciclo semanal, alocação precisa da Força Municipal amparada por inteligência qualitativa, e governança baseada em evidências.

## 11. Arquitetura recomendada (stack a decidir pelo time)

A stack ainda não foi fechada. Esta é a recomendação para discussão. Ela prioriza um time que dirige agentes de IA mais do que escreve código de baixo nível, e um produto que precisa estar implantável rápido.

- **Frontend:** React + Vite + TypeScript.
- **Mapas:** MapLibre GL JS ou Leaflet, com Turf.js para geometria no cliente quando necessário.
- **Backend e dados:** Supabase (Postgres com extensão PostGIS). Auth e Storage já vêm embutidos.
- **Motor LLM:** Claude API (Anthropic). Claude faz a extração estruturada de DD e RELINTs e a síntese dos módulos do relatório. Usar structured output ou tool use para JSON confiável.
- **Ingestão:** Supabase Edge Functions (Deno e TypeScript) para parsing de CSV e GeoJSON. Um pequeno serviço Python pode entrar se o parsing de Shapefile exigir.
- **Hospedagem:** Vercel para o front, Supabase para o back.

**Insight de arquitetura que define o projeto:** o score do “bingo” é, no fundo, uma query geoespacial. Com PostGIS, modele cada camada como geometria (pontos para crimes, polígonos para áreas e fatores, linhas para segmentos viários) e calcule as interseções com funções nativas (`ST_Intersects`, `ST_DWithin`, `ST_Buffer`). O score de um segmento vira uma função do número e do peso de camadas que coincidem nele. Isso evita reimplementar geometria à mão e deixa o motor da Parte 2 enxuto.

## 12. Convenções de código e colaboração (4 integrantes)

- **Idioma:** código, variáveis e funções em inglês. Labels de interface e termos de domínio em português.
- **Git:** uma branch por feature (`feature/nome-curto`). Todo PR revisado por pelo menos um outro integrante antes do merge.
- **Commits:** padrão convencional (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`).
- **Segredos:** nunca commitar chaves. Usar `.env` local e `.env.example` versionado. Variáveis esperadas: `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
- **Divisão sugerida das frentes (ajustável pelo Pedro):**
  - Frente A: ingestão de dados e modelagem do schema.
  - Frente B: motor LLM (extração da Parte 1 e síntese do relatório).
  - Frente C: motor geoespacial (PostGIS, query de bingo e score).
  - Frente D: frontend e visualização (mapa, matriz temporal, relatório, tela de refino).
- **Testes:** ao tocar em lógica de score ou geometria, escrever um teste com dado mock antes de considerar a tarefa concluída.

## 13. Guardrails de IA responsável (CRÍTICO)

Este projeto é de segurança pública. As regras abaixo não são opcionais e devem ser respeitadas em todo o código e em toda saída gerada.

- **Decisão final sempre humana.** O passo de Refino Humano do ciclo é obrigatório. O sistema produz rascunho, score e justificativa. A equipe CompStat valida antes de qualquer ação na rua.
- **Foco no ambiente, não no indivíduo.** O produto prioriza fatores urbanos (iluminação, poda, ordenamento) e alocação de patrulha. As recomendações tratam de condições do espaço público e de crime patrimonial, não de identificação ou vigilância de pessoas.
- **Texto livre é indício, não fato.** Disque Denúncia e RELINTs contêm informação sensível e não verificada. A IA deve sinalizar incerteza e citar a fonte de cada conclusão.
- **Nunca inventar dado.** Se uma camada estiver ausente ou vazia, o sistema declara a ausência. Um score gerado com dado insuficiente deve ser marcado como baixa confiança.
- **Evitar viés de realimentação.** Priorizar sempre as mesmas áreas pode gerar mais patrulha, mais registro e score artificialmente mais alto. Documentar essa limitação e considerar normalização por exposição.
- **Privacidade e LGPD.** Minimizar dado pessoal. O produto trabalha com agregados territoriais sempre que possível.
- **Transparência.** Toda priorização precisa de uma justificativa legível por humano que explique o porquê do score.

## 14. Comandos e setup do projeto

A preencher quando a stack estiver fechada e o repositório criado. Sugestão inicial para a stack recomendada:

```bash
# instalar dependências
npm install

# ambiente de desenvolvimento
npm run dev

# build de produção
npm run build

# testes
npm run test
```

Enquanto os dados reais não chegam, gerar dados sintéticos para as 5 fontes (ocorrências com Lat/Long fictícias, polígonos GeoJSON de exemplo, fatores urbanos mock, e textos de DD e RELINT fictícios) para destravar o desenvolvimento das frentes B, C e D.

## 15. Dados (pendente de ingestão)

Quando o Pedro enviar os dados reais, atualizar esta seção com:

- Esquema de cada uma das 5 fontes (colunas, tipos, exemplos).
- Volume e período coberto.
- Mapeamento de cada coluna para as camadas do modelo (mancha, fator urbano, dinâmica).
- Observações de qualidade (campos faltantes, formatos inconsistentes).

Até a chegada dos dados, qualquer suposição de schema deve ser confirmada antes de virar código.

## 16. Estado atual e próximos passos

- [ ] Fechar a stack (recomendação na seção 11).
- [ ] Criar repositório e estrutura base do projeto.
- [ ] Gerar dados sintéticos para as 5 fontes.
- [ ] Prototipar a query de “bingo” no PostGIS com dados mock.
- [ ] Pipeline Claude de extração de DD e RELINT em JSON estruturado.
- [ ] Frontend com mapa, manchas de calor e matriz temporal.
- [ ] Geração do relatório de 6 módulos.
- [ ] Tela de refino humano e matriz de responsabilização.
- [ ] Receber e modelar os dados reais (atualizar seção 15).

-----

## Como o Claude Code deve trabalhar neste repositório

1. Leia este CLAUDE.md inteiro antes de agir.
1. Antes de implementar uma feature, identifique em qual das quatro frentes ela se encaixa (seção 12).
1. Não assuma esquema de dados que ainda não foi definido. Pergunte (ver seções 15 e 13).
1. Prefira soluções diretas e bem documentadas. O time dirige agentes de IA e não é majoritariamente full-stack, então evite abstrações pesadas sem necessidade.
1. Ao mexer em lógica de score ou geometria, escreva um teste com dado mock.
1. Respeite todos os guardrails da seção 13 em qualquer código ou saída.
1. Comente decisões de arquitetura relevantes no próprio código.