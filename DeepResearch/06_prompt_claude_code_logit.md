# Prompt para Claude Code — Estimação do Modelo Logit CompStat-Rio

---

## Contexto e objetivo

Você vai implementar um modelo logit de previsão de roubo/furto por micropolígono para o projeto CompStat-Rio. Antes de escrever qualquer linha de código, leia com atenção os dois MDs abaixo e entenda completamente a lógica do modelo e das decisões já tomadas:

- `05_decisao_subdivisao_espacial.md` — define a unidade espacial (H3 res 9), o polígono-mãe (áreas da FM), o tratamento de borda (buffer 120 m), a hierarquia de efeitos fixos e as salvaguardas para áreas esparsas
- `03_prompt_deep_research_logit_crime.md` — define a especificação econométrica do logit, os grupos de variáveis (histórico, lag espacial, desordem urbana, policiamento), os horizontes (s = 1, 2, 4 semanas), o pipeline de estimação e as métricas de validação

Só comece a explorar os dados depois de ter entendido os dois MDs.

---

## Fase 1 — Exploração e entendimento dos dados

Antes de construir o painel, faça uma inspeção sistemática de **todas** as bases na pasta `dados/`. Para cada arquivo:

1. Leia as primeiras linhas e o schema completo (nomes de colunas, tipos, exemplos de valores)
2. Identifique o campo geográfico (lat/lon, geometry, x/y) e seu formato exato (separador decimal, projeção, etc.)
3. Identifique o campo temporal quando houver (formato da data, granularidade, intervalo coberto)
4. Verifique qualidade: nulos, coordenadas implausíveis, datas corrompidas
5. Documente como cada base se conecta às outras (por coordenada, por `id_subarea`, por `nome_subar`, ou por spatial join)

Ao final desta fase, escreva um bloco de comentários no código descrevendo o que cada base contém e como ela entra no modelo (rótulo / covariável de desordem / policiamento / contexto territorial / efeito fixo). Não avance para a Fase 2 sem ter esse mapeamento claro.

---

## Fase 2 — Construção do painel hex × semana

Siga exatamente as decisões do `05_decisao_subdivisao_espacial.md`:

1. **Universo de células:** gere os hexágonos H3 resolução 9 que cobrem cada uma das 8 áreas da FM (`sh_area_forca`), com buffer de 120 m. Use projeção UTM-23S (EPSG:31983) para o buffer métrico, depois converta de volta para WGS-84 antes do `h3.polyfill_geojson`. Hexágonos capturados pelo buffer de duas áreas vizinhas são atribuídos à área cujo centroide H3 está mais próximo.

2. **Filtro obrigatório:** todo registro de qualquer base que não esteja dentro dos polígonos da FM (após o spatial join por `hex_id`) deve ser removido antes da estimação. Nenhum dado fora da FM entra no modelo.

3. **Rótulo:** use as ocorrências de roubo georreferenciadas (`df_ocorrencias_tratado`). Descarte registros com coordenada implausível (latitude tipo `-22901`, sem ponto decimal) e datas fora da janela 2020–2024. O rótulo é binário: `y = 1` se houve ≥ 1 roubo no hexágono na semana ISO, `y = 0` caso contrário.

4. **Lags do rótulo:** para cada hex × semana, calcule `y_lag1`, `y_lag2`, `y_lag4`, `y_lag12` e `n_roubos_12w` (contagem acumulada nas últimas 12 semanas).

5. **Lag espacial:** `W_y_lag1` = média de `y_lag1` dos vizinhos H3 ring-1 que também estão dentro da FM. Vizinhos fora da FM recebem valor 0 (não são excluídos do cálculo da média, mas contribuem com zero).

6. **Covariáveis de desordem urbana:** agregue `fatores_urbanos` por hex × semana. Para cada fator relevante (iluminação, lixo, vegetação, obstáculos, situação de rua, trânsito, mobiliário — confira os nomes exatos das colunas no arquivo), calcule a contagem nas últimas 4 semanas (`_4w`). Se o arquivo tiver granularidade diferente de semanal, agregue para a semana ISO correspondente antes de calcular os lags.

7. **Covariáveis de policiamento:** agregue `cameras_areas_fm` por hex (contagem de câmeras no hex e no ring-1). Se houver outras variáveis de policiamento disponíveis nas bases, identifique-as na Fase 1 e inclua aqui.

8. **Disk-denúncia:** verifique na Fase 1 se `disk_denuncia` tem campo temporal e como agregar por hex × semana. Se a agregação for possível, inclua como covariável adicional. Se não for, documente por que foi excluído.

9. **Domínio territorial:** faça spatial join de `dominio_territorial` (polígonos por facção) com os hexágonos da FM. Gere uma variável categórica ou dummies indicando o contexto territorial de cada hex (sem domínio / facção X / milícia / disputado). Essa variável é estática (não varia por semana).

10. **Sazonalidade:** adicione `week_sin = sin(2π × semana_iso / 52)`, `week_cos = cos(2π × semana_iso / 52)` e `is_holiday_week` (feriados nacionais e municipais do Rio).

11. **Efeito fixo:** adicione a coluna `area_fm` (`nome_subar`) — será convertida em dummies na estimação.

12. **Área esparsa:** verifique a taxa de positivos de Campo Grande. Se for < 10%, rode o painel dessa área separadamente com resolução 8 (`run(res=8)`) e empilhe com o restante antes da estimação.

Salve o painel como `painel_hex_semana_res9.csv`.

---

## Fase 3 — Estimação do logit por horizonte

Estime **três modelos separados**, um para cada horizonte s ∈ {1, 2, 4}:

- A variável dependente do modelo s é `y` deslocado s semanas à frente: o modelo aprende com os dados até a semana t para prever t+s
- As features são sempre construídas em t (sem vazamento de informação futura)
- Efeitos fixos de `area_fm` via one-hot encoding (`drop='first'` para evitar multicolinearidade)
- Use `sklearn.LogisticRegression(penalty='l2', C=1.0, class_weight='balanced', solver='liblinear', max_iter=1000)` como estimador base
- Validação temporal: treine até a semana T-4, valide em T-3..T-1, teste em T. Nunca use split aleatório — o painel tem dependência temporal
- Calcule para cada modelo: AUC-ROC, AUC-PR, PAI (top 10%) e Moran's I dos resíduos. Se AUC-PR < 0,10 ou Moran's I > 0,10 (p<0,01), aplique as salvaguardas da Seção 9 do `03_prompt_deep_research_logit_crime.md` antes de prosseguir
- Se necessário para inferência com erros-padrão clusterizados por `area_fm`, use também `statsmodels.Logit` com `cov_type='cluster'`

---

## Fase 4 — Predição com dados mais recentes

Após a estimação, use os três modelos para gerar probabilidades na **semana mais recente disponível nos dados** (semana T):

```
Para cada micropolígono h ∈ FM:
    prob_t1[h] = P(y_{h, T+1} = 1 | X_{h, T})   ← modelo s=1
    prob_t2[h] = P(y_{h, T+2} = 1 | X_{h, T})   ← modelo s=2
    prob_t4[h] = P(y_{h, T+4} = 1 | X_{h, T})   ← modelo s=4
```

---

## Outputs obrigatórios

Gere **um CSV por horizonte** com as seguintes colunas:

### `predicoes_t1.csv`, `predicoes_t2.csv`, `predicoes_t4.csv`

| Coluna | Descrição |
|---|---|
| `hex_id` | Identificador H3 do micropolígono |
| `area_fm` | Nome da área da FM (`nome_subar`) |
| `lat_centroide` | Latitude do centroide H3 |
| `lon_centroide` | Longitude do centroide H3 |
| `prob_crime` | Probabilidade predita de ≥ 1 roubo/furto no horizonte s |
| `decil_risco` | Decil da probabilidade (1 = menor risco, 10 = maior risco) dentro das áreas da FM |
| `y_lag1` | Valor do lag 1 usado na predição (houve crime na semana passada?) |
| `top_driver_1` | Nome da variável com maior contribuição para a probabilidade alta (`beta_j * x_j`) |
| `top_driver_2` | Segunda maior contribuição |
| `top_driver_3` | Terceira maior contribuição |
| `contrib_top1` | Share da contribuição do top_driver_1 (% do total absoluto) |
| `contrib_top2` | Share do top_driver_2 |
| `contrib_top3` | Share do top_driver_3 |
| `[todas as features usadas no modelo]` | Valores das features na semana T para rastreabilidade |

### `coeficientes_logit.csv`

Um único arquivo com os coeficientes dos três modelos:

| Coluna | Descrição |
|---|---|
| `feature` | Nome da variável |
| `beta_s1` | Coeficiente do modelo s=1 |
| `beta_s2` | Coeficiente do modelo s=2 |
| `beta_s4` | Coeficiente do modelo s=4 |
| `se_s1` | Erro-padrão clusterizado (se disponível) |
| `se_s2` | Idem |
| `se_s4` | Idem |
| `odds_ratio_s1` | `exp(beta_s1)` |
| `odds_ratio_s2` | `exp(beta_s2)` |
| `odds_ratio_s4` | `exp(beta_s4)` |

### `metricas_validacao.csv`

| Coluna | Descrição |
|---|---|
| `horizonte` | s = 1, 2 ou 4 |
| `auc_roc` | AUC-ROC no conjunto de teste |
| `auc_pr` | AUC-PR no conjunto de teste |
| `pai_top10` | PAI nos top 10% hexágonos de maior risco |
| `morans_i` | Moran's I dos resíduos |
| `morans_p` | p-valor do Moran's I |
| `n_train` | Observações no treino |
| `n_test` | Observações no teste |
| `taxa_positivos_train` | % de positivos no treino |
| `taxa_positivos_test` | % de positivos no teste |

---

## Regras de qualidade

- **Nunca use dados fora dos polígonos da FM.** Qualquer hex sem `area_fm` válido é excluído antes da estimação e das predições.
- **Nunca vaze informação futura nas features.** Todas as covariáveis usadas para prever t+s são construídas com dados até t.
- **Documente cada decisão não-trivial** com um comentário no código explicando por que foi feita (ex.: por que vizinhos fora da FM recebem zero e não NaN, por que usar `drop='first'` no one-hot, etc.).
- **Se uma base não conseguir ser integrada** por problema de formato, coordenada ou schema inesperado, documente o problema em um bloco de comentários e prossiga sem ela — não trave o pipeline.
- **Se AUC-PR < 0,10 em qualquer horizonte**, aplique a salvaguarda correspondente da Seção 9 do `03_prompt_deep_research_logit_crime.md` e registre qual salvaguarda foi ativada em `metricas_validacao.csv`.
