# CompStat-Rio — Inteligência Preditiva por Micropolígono

**Claude Impact Lab Hackathon · Rio de Janeiro · 24/05/2026**  
**Time:** Pedro Fize + Arthur + equipe  
**Cliente de referência:** Secretaria-Geral do CompStat / Prefeitura do Rio de Janeiro

---

## O que esta pasta contém

Esta pasta documenta e entrega a **camada analítica central do CompStat-Rio**: um modelo logit espacial que prevê probabilidade de roubo/furto por micropolígono para os próximos 1, 2 e 4 semanas, e um agente de IA que converte essas probabilidades em recomendações de ação por órgão municipal — sem depender de análise manual.

O sistema responde a três perguntas ao mesmo tempo: **onde** o risco é alto, **por que** ele é alto (decomposição causal), e **o que a Prefeitura pode fazer** dentro das restrições institucionais e geográficas de cada ponto.

---

## Estrutura de arquivos

```
DeepResearch/
│
├── README.md                          ← este arquivo
│
├── ── ESPECIFICAÇÃO DO MODELO ──
│
├── 03_prompt_deep_research_logit_crime.md
│   Especificação econométrica completa do modelo logit.
│   Contém: equação formal, grupos de variáveis, horizontes de previsão,
│   código de construção de features, critérios de validação e salvaguardas.
│
├── 04_agente_dashboard_policy.md
│   Instruções para o agente de recomendações de policy.
│   Contém: lógica de decomposição β·x, filtros semânticos por família de
│   coeficiente, mapeamento driver→órgão, regras de viabilidade institucional
│   e formato do card de output.
│
├── 05_decisao_subdivisao_espacial.md
│   Decisão técnica sobre a unidade geográfica do modelo (H3 resolução 9).
│   Contém: tabela comparativa de resoluções, estrutura de hierarquia
│   micropolígono/polígono-mãe, tratamento de borda com buffer 120 m,
│   código de spatial join e análise da exceção Campo Grande.
│
├── 06_prompt_claude_code_logit.md
│   Prompt de execução para o Claude Code rodar as 4 fases do pipeline
│   (exploração dos dados → construção do painel → estimação → predição).
│   Schema de todos os outputs obrigatórios.
│
├── ── BRIEFINGS DE PESQUISA ──
│
├── 01_briefing_claude_code.md
│   Briefing do hackathon: contexto do CompStat, bases municipais disponíveis,
│   5 propostas de projeto, estratégias de identificação causal.
│
├── 02_deep_research_gemini.md
│   Deep research do Gemini: ecossistema de dados públicos do Rio, casos
│   análogos internacionais (San Diego, Miami, CDMX, Little Haiti),
│   padrões transversais e recomendações táticas para o hackathon.
│
├── ── OUTPUTS DO MODELO ──  (pasta ../output/)
│
├── ../output/predicoes_t1.csv         ← probabilidades por hex, horizonte t+1
├── ../output/predicoes_t2.csv         ← idem, t+2
├── ../output/predicoes_t4.csv         ← idem, t+4
├── ../output/coeficientes_logit.csv   ← betas dos 3 modelos + odds ratios
├── ../output/metricas_validacao.csv   ← AUC-ROC, AUC-PR, PAI, Moran's I
├── ../output/painel_hex_semana_res9.csv ← painel completo hex × semana
├── ../output/top_drivers_por_area.csv ← top 3 drivers por hex e área
├── ../output/mapa_risco_t1.html       ← mapa coroplético interativo (Folium)
├── ../output/mapas_por_area/          ← 9 mapas individuais por área FM
│
└── dashboard_policy_t1.html          ← dashboard de recomendações de policy
                                         (gerado pelo agente do 04_md, t+1)
```

---

## O modelo preditivo

### Unidade de análise

Cada observação é um **micropolígono × semana**. O micropolígono é um hexágono H3 resolução 9 (~0,1 km², aresta ≈ 175 m — equivalente a um quarteirão denso), aninhado dentro de uma das **8 áreas de atuação da Força Municipal**. O universo é restrito a hexágonos dentro desses polígonos antes de qualquer estimação — dados externos à FM são descartados.

```
Área FM (polígono-mãe)  ←  efeito fixo α
    └── hexágono H3 res 9  ←  micropolígono h, unidade de previsão
            └── features em t  →  P(crime em t+s)
```

O painel tem **34.584 observações** (132 hexágonos × 262 semanas ISO), com taxa de positivos de ~25% — longe do regime de evento raro, o que garante identificação estável do logit.

### Equação formal

Para cada horizonte $s \in \{1, 2, 4\}$ semanas, um modelo separado estima:

$$\Pr\!\left(y_{h,\,t+s}=1 \;\middle|\; X_{h,t}\right) \;=\; \Lambda\!\left(\; \alpha_{b(h)} \;+\; \underbrace{\sum_{k}\,\beta_k^{(s)}\,y_{h,t-k}}_{\text{histórico próprio}} \;+\; \underbrace{\gamma^{(s)}\,[Wy_t]_h}_{\text{lag espacial}} \;+\; \underbrace{\delta^{(s)\prime}\,Z^{\text{desordem}}_{h,t}}_{\text{desordem urbana}} \;+\; \underbrace{\phi^{(s)\prime}\,P_{h,t}}_{\text{policiamento}} \;+\; \underbrace{\theta^{(s)\prime}\,D_t}_{\text{sazonalidade}} \;\right)$$

onde $\Lambda(\cdot) = \frac{e^x}{1+e^x}$ é a função logística.

**Variável dependente:** $y_{h,t+s} = \mathbf{1}\{\geq 1 \text{ roubo ou furto em } h \text{ na semana } t+s\}$

**Modelos separados por horizonte** porque o coeficiente de `y_lag1` domina em $s=1$ (near-repeat) e perde peso relativo para desordem urbana e policiamento em $s=4$ — impor restrições comuns seria perda de informação (Johnson & Bowers 2004; Mohler et al. 2015).

### Grupos de variáveis

| Grupo | Variáveis | Interpretação |
|---|---|---|
| **Histórico próprio** | `y_lag1`, `y_lag2`, `y_lag4`, `y_lag12`, `n_crimes_12w` | Near-repeat (janela curta) vs. hotspot crônico (janela longa) |
| **Lag espacial** | `W_y_lag1` = média dos `y_lag1` dos vizinhos ring-1 dentro da FM | Spillover de crime entre hexágonos adjacentes |
| **Desordem urbana** | `n_fat_ilum`, `n_fat_vegetac`, `n_fat_lixo`, `n_fat_calcada`, `n_fat_transito`, `n_fat_mobil`, `n_fat_sitrua` | Contagem de chamados por categoria nos últimos 4 semanas |
| **Policiamento** | `n_cameras`, `n_cameras_ring1` | Câmeras CIVITAS no hex e no ring-1 (proxy de cobertura) |
| **Sazonalidade** | `week_sin`, `week_cos`, `is_holiday_week` | Ciclo anual (Fourier) e feriados |
| **Efeito fixo** | `fe_area_*` (dummies de área FM) | Nível médio de risco da área — contexto, não driver acionável |
| **Domínio territorial** | `orcrim_CV`, `orcrim_TCP`, `orcrim_Milícia`, `orcrim_Sem domínio` | Facção/milícia dominante — filtra viabilidade de intervenção |

### Estimação e validação

- **Estimador:** `sklearn.LogisticRegression(penalty='l2', C=1.0, class_weight='balanced', solver='liblinear')`
- **Validação temporal** (nunca split aleatório — painel tem dependência serial): treino até semana T-4, validação T-3..T-1, teste em T
- **Resultados no conjunto de teste:**

| Horizonte | AUC-ROC | AUC-PR | PAI top-10% | Moran's I resíduos |
|---|---|---|---|---|
| t+1 | 0,728 | 0,371 | 3,5× | 0,135 (p=0,014) |
| t+2 | 0,753 | 0,387 | 3,5× | 0,117 (p=0,017) |
| t+4 | 0,709 | 0,379 | 3,5× | 0,143 (p=0,005) |

AUC-PR de ~0,37 com taxa de positivos de ~11% no teste — bem acima do baseline naïve (~0,11). PAI de 3,5× significa que os 10% de hexágonos mais arriscados concentram 35% dos roubos — sinal de que o modelo identifica manchas reais, não artefatos.

---

## Do modelo ao dashboard: o pipeline de policy

O modelo entrega probabilidades. O agente (especificado em `04_agente_dashboard_policy.md`) converte essas probabilidades em **recomendações de ação por órgão municipal**. O fluxo tem seis passos:

```
┌──────────────────────────────────────────────────────────────────┐
│                    DADOS BRUTOS (pasta dados/)                   │
│  ocorrências georreferenciadas · fatores urbanos · câmeras       │
│  domínio territorial · disk-denúncia                             │
└───────────────────────┬──────────────────────────────────────────┘
                        │ Spatial join → H3 res 9 → painel hex×semana
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│              MODELO LOGIT (3 horizontes separados)               │
│  Pr(crime_{h,t+s} | X_{h,t}) para s ∈ {1, 2, 4}               │
│  Output: predicoes_t1/t2/t4.csv + coeficientes_logit.csv        │
└───────────────────────┬──────────────────────────────────────────┘
                        │ Top 10% por prob_t1 (threshold ≈ 78%)
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│           PASSO 1 — SELEÇÃO DE MICROPOLÍGONOS CRÍTICOS          │
│  Filtra hexágonos acima do limiar operacional                    │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│           PASSO 2 — DECOMPOSIÇÃO DO RISCO (β · x)               │
│                                                                  │
│  contrib_j = β̂_j · x_j                                          │
│  share_j   = |contrib_j| / Σ_k |contrib_k|                      │
│                                                                  │
│  Filtros semânticos aplicados:                                   │
│  • fe_area_* → rebaixado para "contexto de área" (não acionável) │
│  • n_cameras_ring1 > 0 → "câmera existente, revisar ângulo"     │
│  • y_lag*/n_crimes_12w → classifica como near-repeat / crônico / │
│    spillover → define prazo de intervenção                       │
│  • n_fat_total dominante sem sub-fator → desordem difusa →      │
│    varredura multi-órgão                                         │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│           PASSO 3 — PERFIL TEMPORAL (ocorrências reais)         │
│  Para cada hex, busca ocorrências no raio de ~500 m e calcula:  │
│  • Faixa de pico (manhã / tarde / noite / madrugada)            │
│  • Dia de pico da semana                                         │
│  • % noturno (18h–06h)                                           │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│        PASSO 4 — RESTRIÇÕES INSTITUCIONAIS (orcrim)             │
│  CV / TCP → coordenação estadual (PMERJ/SESP)                   │
│  Milícia → protocolo de segurança SEOP para campo               │
│  Sem domínio → ação municipal direta liberada                    │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│          PASSO 5 — RECOMENDAÇÃO DE POLICY POR ÓRGÃO             │
│                                                                  │
│  Driver → Órgão → Ação → Prazo → Evidência científica           │
│  ─────────────────────────────────────────────────────          │
│  n_fat_ilum    → RioLuz     → reparo de postes                  │
│  n_fat_vegetac → Comlurb    → poda                              │
│  n_fat_lixo    → Comlurb    → coleta                            │
│  n_fat_transito→ GM-Rio     → fiscalização estacionamento        │
│  n_fat_sitrua  → SMAS       → abordagem social                  │
│  n_fat_calcada → Seconserva → reparo de calçadas                │
│  y_lag1 ativo  → GM-Rio     → moto-patrulha imediata            │
│  W_y_lag1 alto → GM-Rio     → ampliar perímetro                 │
│  n_crimes_12w  → estrutural → intervenção combinada             │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│              OUTPUT: dashboard_policy_t1.html                    │
│  16 cards · 5 áreas FM · decisão humana antes de qualquer ação  │
└──────────────────────────────────────────────────────────────────┘
```

### O que o dashboard entrega por micropolígono

Cada card contém:

- **Probabilidades nos 3 horizontes** — t+1, t+2, t+4
- **Por que o risco é alto** — top 3 drivers com share percentual e recomendação de ação por órgão
- **Quando o crime ocorre** — faixa de pico, dia da semana, % noturno calculados a partir das ocorrências reais
- **Policiamento recomendado** — modalidade (moto-patrulha, viatura, a pé) com justificativa e prazo
- **Restrições institucionais** — jurisdição (municipal ou estadual coordenado) baseada no domínio territorial
- **Auditoria das interpretações** — quais regras semânticas foram aplicadas, para o gestor ajustar o modelo mental

---

## Dados de entrada (pasta `../dados/`)

| Arquivo | Registros | Papel |
|---|---|---|
| `df_ocorrencias_tratado - Extração 1 .csv` | 115.354 | **Rótulo do modelo** — roubos/furtos 2020–2024 georreferenciados |
| `fatores_urbanos.csv` | 8.229 | **Desordem urbana** — 20 tipos de ocorrências por coordenada e id_subarea |
| `cameras_areas_fm.csv` | 985 | **Policiamento passivo** — câmeras CIVITAS por área FM |
| `dominio_territorial - Extração 1.csv` | 1.627 | **Contexto territorial** — polígonos por facção (CV, TCP, Milícia) |
| `disk_denuncia.csv` | 83.549 | **Proxy de demanda** — n_dd_lag1 no modelo |
| `CPSR_2020_2022_2024.xlsx` | — | Dados complementares de segurança pública |
| `Dicionário de dados.xlsx` | — | Metadados e descrição das colunas |

---

## Outputs gerados (pasta `../output/`)

| Arquivo | Conteúdo |
|---|---|
| `predicoes_t1/t2/t4.csv` | Probabilidade predita por hexágono + top 3 drivers + todas as features |
| `coeficientes_logit.csv` | β, odds ratio e erro-padrão para os 3 modelos |
| `metricas_validacao.csv` | AUC-ROC, AUC-PR, PAI, Moran's I por horizonte |
| `painel_hex_semana_res9.csv` | Painel completo hex × semana (base de estimação) |
| `top_drivers_por_area.csv` | Top 5 hexágonos por área + top 3 drivers em linguagem natural |
| `mapa_risco_t1.html` | Mapa coroplético interativo (Folium) |
| `mapas_por_area/` | 9 mapas individuais por área FM |
| `dashboard_policy_t1.html` | **Dashboard de recomendações de policy** (este arquivo) |

---

## Guardrails de IA responsável

Este sistema opera em segurança pública. As seguintes restrições são inegociáveis:

**Decisão final sempre humana.** O dashboard é um rascunho de análise. A equipe CompStat valida antes de qualquer ação de campo.

**Foco no ambiente, não no indivíduo.** O modelo trata de condições do espaço público (iluminação, calçada, vegetação) e alocação de patrulha — não de identificação de pessoas.

**Nunca inventar dado.** Se uma base estiver ausente, o sistema declara a ausência. Scores com dado insuficiente são marcados como baixa confiança.

**Transparência obrigatória.** Todo card inclui uma seção de auditoria mostrando quais regras foram aplicadas e por quê — para que o gestor possa discordar e ajustar.

**Viés de realimentação documentado.** Concentrar patrulha nos mesmos hexágonos pode inflar registros artificialmente. O modelo normaliza por exposure e os coeficientes de câmera/policiamento têm sinal esperado negativo — sinal de que o modelo detecta dissuasão, não só registro.

---

## Como rodar o pipeline do zero

```bash
# 1. Estimar o modelo logit (fases 1–3 do 06_prompt_claude_code_logit.md)
#    Rodar com Claude Code passando o 06_md como prompt + dados/

# 2. Gerar o dashboard de policy
cd output_dir/
python3 dashboard_agent.py
# → salva dashboard_policy_t1.html em DeepResearch/
```

Os parâmetros principais estão no topo do `dashboard_agent.py`:
- `LIMIAR_PROB = 0.30` — probabilidade mínima para entrar no dashboard
- `TOP_PCT = 0.10` — percentil mínimo (o mais restritivo dos dois é usado)
- `radius_deg = 0.005` — raio de busca de ocorrências para perfil temporal (~500 m)

---

## Referências

- Cohen & Felson (1979). Routine Activity Theory. *American Sociological Review* 44(4).
- Johnson & Bowers (2004). The burglary as clue to the future. *Security Journal*.
- Mohler et al. (2011/2015). Self-exciting point process modeling / Randomized controlled field trial. *JASA*.
- Wheeler (2018). 311 calls and crime. *Crime & Delinquency* 64(14).
- Chalfin et al. (2019). Reducing crime through environmental design. NBER WP 25798.
- Caplan & Kennedy (2016). *Risk Terrain Modeling*. Rutgers.
- O'Brien & Sampson (2015). Public and private spheres of neighborhood disorder. *JRCD* 52(4).
- Weisburd (2015). The law of crime concentration. *Criminology* 53(2).
- Chainey, Tompson & Uhlig (2008). The utility of hotspot mapping. *Security Journal*.
