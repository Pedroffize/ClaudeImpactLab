# Instruções para Agente: Dashboard de Recomendações de Policy por Micropolígono
**Versão 2 — Inclui perfil temporal de crime e ajuste de turno nas recomendações**

---

## Visão Geral

Este agente recebe como input o output do modelo logit (`df_pred` com probabilidades por micropolígono e horizonte) e os coeficientes estimados do modelo, e produz um **dashboard de recomendações de ação para a Prefeitura** — mostrando, para cada micropolígono de alto risco, por que o risco é alto e o que a Prefeitura pode fazer, considerando restrições geográficas e institucionais.

---

## Inputs que o Agente Recebe

### 1. Probabilidades do modelo (`df_pred`)
```
hex_id | geometry | id_poligono_fm | prob_t1 | prob_t2 | prob_t4
```

### 2. Coeficientes do logit por horizonte (`betas`)
```python
# Estrutura esperada:
betas = {
    1: pd.Series({'y_lag1': 1.82, 'n_ilum_4w': 0.43, 'n_situacao_rua_4w': 0.61,
                  'n_lixo_4w': 0.21, 'cobertura_moto_lag1': -0.38, ...}),
    2: pd.Series({...}),
    4: pd.Series({...}),
}
```

### 3. Atributos geográficos do micropolígono (`df_geo`)
```
hex_id | tipo_via | tem_morro | largura_calcada | densidade_pedestre |
tem_rua_adjacente | cobertura_vegetacao | nivel_iluminacao_atual
```
> Esses atributos determinam quais modalidades de policiamento são fisicamente viáveis.

### 4. Atributos institucionais do micropolígono (`df_institucional`)
```
hex_id | faccao_dominante | tipo_dominio | presenca_milicia |
eh_territorio_disputado | jurisdicao_primaria
```
> Esses atributos determinam restrições de policy — se o território é dominado por facção ou milícia, a ação municipal direta pode ser inviável ou insegura.

### 5. Dados recentes das variáveis de desordem (`df_desordem_recente`)
```
hex_id | n_ilum_4w | n_lixo_4w | n_situacao_rua_4w | n_obstaculo_4w |
n_vegetacao_4w | n_transito_4w | n_mobiliario_4w | [semana atual]
```
> Valores atuais das features — usados para contextualizar a recomendação ("há 7 chamados de iluminação apagada nos últimos 4 semanas neste micropolígono").

### 6. Histórico de ocorrências com hora (`df_ocorrencias_historico`)
```
hex_id | data | hora | tipo_crime | dia_semana
```
> Registros históricos de roubos/furtos **dentro dos polígonos da FM** com o campo de hora preenchido. Usado exclusivamente para calcular o perfil temporal descritivo de cada micropolígono — **não entra na estimação do logit**, apenas na camada de recomendação do agente.

```python
# Construir df_ocorrencias_historico a partir do df_ocorrencias_tratado
# já usado no logit — apenas filtrar por hex_id ∈ FM e extrair hora
df_ocorrencias_historico = (
    df_ocorrencias_tratado[df_ocorrencias_tratado['hex_id'].isin(fm_hexes)]
    [['hex_id', 'data', 'hora', 'tipo_crime']]
    .assign(
        dia_semana=lambda d: pd.to_datetime(d['data']).dt.day_name(),
        faixa_horaria=lambda d: pd.cut(
            d['hora'].astype(int),
            bins=[0, 6, 12, 18, 24],
            labels=['Madrugada (0–6h)', 'Manhã (6–12h)',
                    'Tarde (12–18h)', 'Noite (18–24h)'],
            right=False
        )
    )
)
```

---

## Lógica de Raciocínio do Agente

### Passo 1 — Selecionar micropolígonos de alto risco

Filtrar os micropolígonos com `prob_t1` acima do limiar operacional (default: top 10% ou prob_t1 > 0,30 — o que for mais restritivo). Ordenar por `prob_t1` decrescente.

```python
LIMIAR_PROB = 0.30
TOP_PCT = 0.10
threshold = max(LIMIAR_PROB, df_pred['prob_t1'].quantile(1 - TOP_PCT))
df_alto_risco = df_pred[df_pred['prob_t1'] >= threshold].sort_values('prob_t1', ascending=False)
```

### Passo 2 — Decompor a probabilidade em fatores explicativos

Para cada micropolígono de alto risco, calcular a **contribuição marginal de cada variável** para a probabilidade predita. A contribuição de cada feature $x_j$ é:

$$\text{contrib}_j = \hat{\beta}_j \cdot x_j$$

Normalizar pelo valor absoluto da soma para obter participação relativa:

$$\text{share}_j = \frac{|\hat{\beta}_j \cdot x_j|}{\sum_k |\hat{\beta}_k \cdot x_k|}$$

Identificar os **3 maiores fatores** (`top_drivers`) ordenados por `share_j` decrescente.

```python
def decompose_risk(hex_id, betas_s1, df_features):
    row = df_features.loc[hex_id]
    contribs = betas_s1 * row[betas_s1.index]
    shares = contribs.abs() / contribs.abs().sum()
    top_drivers = shares.nlargest(3)
    return top_drivers  # {feature: share}
```

> **Importante:** reportar separadamente fatores com beta positivo (aumentam risco) dos com beta negativo (reduzem risco). Um beta negativo significativo em `cobertura_moto_lag1` indica que policiamento motorizado já presente está associado a menor risco — reforçar essa presença pode ser a recomendação.

### Passo 3 — Calcular perfil temporal descritivo do micropolígono

Para cada micropolígono de alto risco, calcular estatísticas descritivas sobre **quando** os crimes historicamente ocorrem — por faixa horária e por dia da semana. Esse perfil é independente do logit; ele descreve o padrão observado nos dados brutos e serve para calibrar **em que turno** e **em que dia** a recomendação de policiamento deve ser concentrada.

```python
def compute_temporal_profile(hex_id, df_ocorrencias_historico, min_obs=10):
    """
    Calcula o perfil temporal de crimes para um micropolígono.
    Retorna None se houver menos de min_obs registros com hora válida.
    """
    df_hex = df_ocorrencias_historico[df_ocorrencias_historico['hex_id'] == hex_id].copy()

    if len(df_hex) < min_obs:
        return None  # histórico insuficiente — não gerar perfil

    # Distribuição por faixa horária
    faixas = df_hex['faixa_horaria'].value_counts(normalize=True).sort_index()

    # Distribuição por dia da semana
    dias = df_hex['dia_semana'].value_counts(normalize=True)

    # Pico horário: faixa com maior concentração
    faixa_pico = faixas.idxmax()
    pct_pico = faixas.max()

    # Pico de dia: dia com maior concentração
    dia_pico = dias.idxmax()
    pct_dia_pico = dias.max()

    # Concentração noturna: % de crimes entre 18h e 6h
    noturno = df_hex['hora'].astype(int)
    pct_noturno = ((noturno >= 18) | (noturno < 6)).mean()

    return {
        'n_registros': len(df_hex),
        'faixa_pico': faixa_pico,
        'pct_faixa_pico': pct_pico,
        'dia_pico': dia_pico,
        'pct_dia_pico': pct_dia_pico,
        'pct_noturno': pct_noturno,
        'distribuicao_faixas': faixas.to_dict(),
        'distribuicao_dias': dias.to_dict(),
    }
```

#### Como o perfil temporal ajusta as recomendações

O perfil temporal não substitui a recomendação baseada nos betas — ele a **especializa no tempo**. A lógica de ajuste é:

```python
FAIXA_TO_TURNO_GM = {
    'Madrugada (0–6h)':  'Turno noturno da GM-Rio (escala 22h–6h)',
    'Manhã (6–12h)':     'Turno matutino da GM-Rio (escala 6h–14h)',
    'Tarde (12–18h)':    'Turno vespertino da GM-Rio (escala 14h–22h)',
    'Noite (18–24h)':    'Turno noturno da GM-Rio (escala 14h–22h / 22h–6h)',
}

def adjust_policy_by_time(policy_base, temporal_profile):
    """
    Recebe a recomendação base (gerada pelos betas) e o perfil temporal,
    e retorna a recomendação ajustada com especificação de turno e dia.
    """
    if temporal_profile is None:
        return {**policy_base, 'ajuste_temporal': 'Histórico insuficiente — sem ajuste de turno'}

    faixa = temporal_profile['faixa_pico']
    pct   = temporal_profile['pct_faixa_pico']
    dia   = temporal_profile['dia_pico']
    turno = FAIXA_TO_TURNO_GM[faixa]
    noturno = temporal_profile['pct_noturno']

    ajuste = (
        f"{pct:.0%} dos crimes ocorrem na faixa '{faixa}' "
        f"(pico no {dia}). "
        f"Concentrar presença no {turno}. "
    )

    # Ajuste específico para iluminação: se crime é majoritariamente noturno,
    # reforça urgência do reparo de iluminação
    if noturno > 0.60 and 'n_ilum_4w' in policy_base.get('top_drivers', []):
        ajuste += (
            f"{noturno:.0%} dos crimes ocorrem à noite — "
            "reparo de iluminação tem impacto direto neste micropolígono "
            "(Chalfin et al. 2019: RCT NYC, -36% crimes noturnos com iluminação)."
        )

    # Ajuste para policiamento a pé: se pico é manhã/tarde em área movimentada,
    # reforça viatura em vez de a pé (maior rotatividade)
    if faixa in ['Manhã (6–12h)', 'Tarde (12–18h)']:
        ajuste += " Horário de alta circulação — policiamento a pé tem maior efeito dissuasório visível."

    return {**policy_base, 'ajuste_temporal': ajuste}
```

#### Estatísticas descritivas a exibir no dashboard

Para cada micropolígono de alto risco com histórico suficiente (≥ 10 registros com hora), exibir:

- **Faixa horária de maior risco:** nome da faixa + percentual (ex: "Noite (18–24h) — 48% dos crimes")
- **Dia da semana de maior risco:** nome do dia + percentual (ex: "Sexta-feira — 22% dos crimes")
- **Concentração noturna:** % de crimes entre 18h e 6h (ex: "71% dos crimes ocorrem no período noturno")
- **Gráfico de barras simples** (ASCII ou HTML) com a distribuição por faixa horária:

```
Distribuição horária histórica (hex_id: 89a8...)
Madrugada (0–6h)  ████░░░░░░  18%
Manhã    (6–12h)  ██░░░░░░░░   9%
Tarde   (12–18h)  ████░░░░░░  22%
Noite   (18–24h)  ███████░░░  51%
```

---

### Passo 5 — Traduzir fatores em linguagem natural

Mapear cada feature para uma descrição em português compreensível para gestores não-técnicos:

```python
FEATURE_LABELS = {
    'y_lag1':               'Histórico recente de crimes na área (semana passada)',
    'W_y_lag1':             'Histórico recente de crimes em áreas vizinhas',
    'n_ilum_4w':            'Iluminação pública com defeito (chamados RioLuz)',
    'n_lixo_4w':            'Acúmulo de lixo e entulho (chamados Comlurb)',
    'n_vegetacao_4w':       'Vegetação obstruindo iluminação ou passeio (chamados Comlurb)',
    'n_obstaculo_4w':       'Obstáculos no passeio — comércio irregular, mobiliário (chamados SEOP)',
    'n_situacao_rua_4w':    'Concentração de pessoas em situação de rua (chamados SMAS)',
    'n_transito_4w':        'Pontos de retenção de trânsito — estacionamento irregular (chamados GM-Rio)',
    'n_mobiliario_4w':      'Mobiliário urbano obstruindo visibilidade (chamados Seconserva)',
    'cobertura_moto_lag1':  'Cobertura de rota de moto-patrulha GM-Rio (semana anterior)',
    'n_cameras_ring':       'Cobertura de câmeras CIVITAS na área',
    'radar_velocidade_ring':'Presença de radar de velocidade',
    'n_manutencao_rioluz_t':'Manutenção de iluminação realizada recentemente (RioLuz)',
}
```

### Passo 6 — Determinar viabilidade das modalidades de policiamento

Para cada micropolígono, verificar quais das três modalidades de policiamento são fisicamente viáveis, com base nos atributos geográficos:

```python
def get_viable_policing(geo):
    """
    geo: linha do df_geo para o hex_id
    Retorna dict {modalidade: viavel (bool), motivo (str)}
    """
    result = {}

    # Viatura
    result['viatura'] = {
        'viavel': geo['tem_rua_adjacente'] and geo['largura_calcada'] >= 4.0,
        'motivo': (
            'Via acessível a veículos'
            if geo['tem_rua_adjacente'] and geo['largura_calcada'] >= 4.0
            else 'Sem acesso viário (morro, beco ou calçada sem rua adjacente)'
        )
    }

    # Moto-patrulha
    result['moto'] = {
        'viavel': not geo['tem_morro'] or geo['largura_calcada'] >= 2.0,
        'motivo': (
            'Acesso por moto viável'
            if not geo['tem_morro'] or geo['largura_calcada'] >= 2.0
            else 'Acesso por moto inviável (morro íngreme ou caminho estreito)'
        )
    }

    # Polícia a pé
    result['pe'] = {
        'viavel': True,  # sempre fisicamente viável — restrição é operacional/segurança
        'motivo': (
            'Alta densidade de pedestres — policiamento a pé tem alta visibilidade'
            if geo['densidade_pedestre'] == 'alta'
            else 'Policiamento a pé viável'
        )
    }

    return result
```

> **Nota para o agente:** a viabilidade física é condição necessária, mas não suficiente. A Seção 5 trata das restrições institucionais que podem tornar qualquer modalidade inviável independentemente da geografia.

### Passo 7 — Verificar restrições institucionais

```python
def get_institutional_constraints(inst):
    """
    inst: linha do df_institucional para o hex_id
    Retorna dict com restrições e recomendação de jurisdição.
    """
    constraints = []
    jurisdicao = 'municipal'  # default

    if inst['faccao_dominante'] and not pd.isna(inst['faccao_dominante']):
        constraints.append(
            f"Território sob influência de {inst['faccao_dominante']} — "
            "ação municipal direta requer coordenação com Segurança Pública estadual (PMERJ/SESP)"
        )
        jurisdicao = 'estadual_coordenado'

    if inst['presenca_milicia']:
        constraints.append(
            "Presença de milícia documentada — intervenções de infraestrutura (iluminação, limpeza) "
            "devem ser coordenadas com SEOP e ter protocolo de segurança para equipes de campo"
        )
        jurisdicao = 'estadual_coordenado'

    if inst['eh_territorio_disputado']:
        constraints.append(
            "Território em disputa — risco elevado para agentes municipais; "
            "priorizar ações não-ostensivas (manutenção de infraestrutura, SMAS)"
        )

    if not constraints:
        constraints.append("Sem restrições institucionais identificadas — ação municipal direta viável")

    return {'restricoes': constraints, 'jurisdicao': jurisdicao}
```

### Passo 8 — Gerar recomendação de policy com ajuste temporal

Com base nos top drivers, viabilidade e restrições, o agente gera uma recomendação estruturada:

```python
DRIVER_TO_POLICY = {
    'n_ilum_4w': {
        'orgao': 'RioLuz',
        'acao': 'Priorizar reparo de postes apagados nos logradouros do micropolígono',
        'prazo': 'Curto prazo (1–2 semanas)',
        'evidencia': 'Chalfin et al. 2019: iluminação reduz crimes noturnos em 36% (RCT NYC)',
    },
    'n_lixo_4w': {
        'orgao': 'Comlurb',
        'acao': 'Aumentar frequência de coleta e remoção de entulho na área',
        'prazo': 'Curto prazo',
        'evidencia': 'Wheeler 2018: desordem física associada a maior incidência criminal',
    },
    'n_vegetacao_4w': {
        'orgao': 'Comlurb',
        'acao': 'Realizar poda de vegetação que obstrui iluminação e visibilidade do passeio',
        'prazo': 'Curto prazo',
        'evidencia': 'CPTED: visibilidade natural reduz oportunidade criminal',
    },
    'n_obstaculo_4w': {
        'orgao': 'SEOP',
        'acao': 'Fiscalizar e remover estruturas irregulares e comércio irregular no passeio',
        'prazo': 'Médio prazo',
        'evidencia': 'CPTED: obstáculos reduzem "capable guardianship" (Cohen & Felson 1979)',
    },
    'n_situacao_rua_4w': {
        'orgao': 'SMAS',
        'acao': 'Intensificar abordagem social e oferta de acolhimento na área',
        'prazo': 'Médio prazo',
        'evidencia': 'O\'Brien & Sampson 2015: desordem social prediz violência futura',
    },
    'n_transito_4w': {
        'orgao': 'GM-Rio',
        'acao': 'Intensificar fiscalização de estacionamento irregular e pontos de retenção',
        'prazo': 'Curto prazo',
        'evidencia': 'CPTED: pontos de retenção criam oportunidade para abordagem',
    },
    'n_mobiliario_4w': {
        'orgao': 'Seconserva',
        'acao': 'Avaliar reposicionamento ou remoção de mobiliário urbano que obstrói visibilidade',
        'prazo': 'Médio prazo',
        'evidencia': 'CPTED: natural surveillance reduz oportunidade criminal',
    },
    'y_lag1': {
        'orgao': 'GM-Rio / PMERJ (coordenado)',
        'acao': 'Aumentar presença ostensiva na área — histórico recente indica padrão near-repeat',
        'prazo': 'Imediato',
        'evidencia': 'Mohler et al. 2011/2015: near-repeat tem janela de 1–4 semanas',
    },
    'W_y_lag1': {
        'orgao': 'GM-Rio',
        'acao': 'Monitorar spillover de crimes de áreas vizinhas — ampliar perímetro de patrulha',
        'prazo': 'Imediato',
        'evidencia': 'Johnson & Bowers 2004: risco near-repeat se propaga espacialmente',
    },
}
```

---

## Formato do Output: Dashboard por Micropolígono

Para cada micropolígono de alto risco, o agente gera um card estruturado. O conjunto de cards forma o dashboard.

### Estrutura do card

```
┌─────────────────────────────────────────────────────────────────┐
│ MICROPOLÍGONO [hex_id]  —  [nome do bairro / polígono FM]       │
│ Probabilidade de roubo/furto: t+1: XX% | t+2: XX% | t+4: XX%  │
├─────────────────────────────────────────────────────────────────┤
│ POR QUE O RISCO É ALTO                                          │
│  1. [Fator 1] — XX% da explicação                               │
│     "Há N chamados de [categoria] nos últimos 4 semanas"        │
│  2. [Fator 2] — XX% da explicação                               │
│  3. [Fator 3] — XX% da explicação                               │
├─────────────────────────────────────────────────────────────────┤
│ QUANDO O CRIME OCORRE (perfil histórico)                        │
│  Faixa de maior risco: [faixa] — XX% dos crimes                 │
│  Dia de maior risco:   [dia]   — XX% dos crimes                 │
│  Crimes noturnos (18h–6h): XX%                                  │
│                                                                 │
│  Madrugada (0–6h)  ████░░░░░░  XX%                             │
│  Manhã    (6–12h)  ██░░░░░░░░  XX%                             │
│  Tarde   (12–18h)  ████░░░░░░  XX%                             │
│  Noite   (18–24h)  ███████░░░  XX%                             │
├─────────────────────────────────────────────────────────────────┤
│ RESTRIÇÕES                                                      │
│  Geográficas: [viatura ✓/✗ | moto ✓/✗ | a pé ✓/✗] + motivo   │
│  Institucionais: [restrição se houver]                          │
│  Jurisdição recomendada: Municipal / Estadual coordenado        │
├─────────────────────────────────────────────────────────────────┤
│ RECOMENDAÇÕES DE AÇÃO                                           │
│  [Para cada top driver com policy disponível:]                  │
│  • Órgão: [nome]                                                │
│  • Ação: [descrição]                                            │
│  • Prazo: [curto/médio/imediato]                                │
│  • Evidência: [referência]                                      │
│  [Modalidade de policiamento viável + turno ajustado:]          │
│  • [viatura / moto / a pé] — [justificativa geográfica]        │
│    → Concentrar no [turno GM-Rio] às [dia(s) de pico]          │
└─────────────────────────────────────────────────────────────────┘
```

### Implementação do card em Python

```python
def generate_card(hex_id, df_pred, betas, df_features, df_geo, df_inst,
                  df_labels, df_ocorrencias_historico):
    row_pred  = df_pred.loc[hex_id]
    top_drivers = decompose_risk(hex_id, betas[1], df_features)
    policing    = get_viable_policing(df_geo.loc[hex_id])
    constraints = get_institutional_constraints(df_inst.loc[hex_id])
    bairro      = df_labels.loc[hex_id, 'nome_bairro']

    # Perfil temporal descritivo (independente do logit)
    temporal_profile = compute_temporal_profile(hex_id, df_ocorrencias_historico)

    # Recomendações base (pelos betas) ajustadas pelo perfil temporal
    drivers_com_policy = []
    for feat, share in top_drivers.items():
        policy_base = DRIVER_TO_POLICY.get(feat, None)
        if policy_base:
            policy_ajustada = adjust_policy_by_time(
                {**policy_base, 'top_drivers': list(top_drivers.keys())},
                temporal_profile
            )
        else:
            policy_ajustada = None

        drivers_com_policy.append({
            'feature':      feat,
            'label':        FEATURE_LABELS.get(feat, feat),
            'share':        f'{share:.0%}',
            'valor_atual':  df_features.loc[hex_id, feat],
            'policy':       policy_ajustada,
        })

    card = {
        'hex_id':           hex_id,
        'bairro':           bairro,
        'prob_t1':          row_pred['prob_t1'],
        'prob_t2':          row_pred['prob_t2'],
        'prob_t4':          row_pred['prob_t4'],
        'top_drivers':      drivers_com_policy,
        'temporal_profile': temporal_profile,   # ← novo
        'policing_viability': policing,
        'constraints':      constraints,
    }
    return card


def generate_dashboard(df_pred, betas, df_features, df_geo, df_inst,
                        df_labels, df_ocorrencias_historico,
                        horizon=1, top_n=10):
    """
    Gera lista de cards ordenados por probabilidade decrescente
    para os top_n micropolígonos de maior risco.
    """
    col = f'prob_t{horizon}'
    top_hexes = df_pred.nlargest(top_n, col)['hex_id'].tolist()

    dashboard = [
        generate_card(h, df_pred, betas, df_features, df_geo, df_inst,
                      df_labels, df_ocorrencias_historico)
        for h in top_hexes
    ]
    return dashboard
```

---

## Sugestões para Melhorar as Instruções (auto-crítica)

As seguintes lacunas precisam ser resolvidas antes de usar este MD como instrução definitiva para o agente:

**1. Dados geográficos (`df_geo`) precisam de fonte concreta**
Os atributos `tem_morro`, `largura_calcada`, `densidade_pedestre` não têm fonte aberta confirmada. Opções:
- OpenStreetMap via `overpy` ou `osmnx` para tipo de via e geometria
- Modelo digital de elevação (MDE) do IBGE para declividade
- Confirmar no kickoff se a Prefeitura tem camada de tipologia viária

**2. Dados institucionais (`df_institucional`) são sensíveis**
Mapas de domínio territorial (facção/milícia) não são dados abertos. Fontes possíveis:
- Fogo Cruzado tem campo `type_of_operation` que inclui facção envolvida — pode ser agregado por micropolígono
- NEV-USP, GENI-UFF e Disque Denúncia têm mapas não-públicos
- Alternativa segura para o hackathon: usar proxy de "área de risco institucional" baseado em histórico de tiroteios com presença de agente policial (Fogo Cruzado campo `presence_of_agents`)

**3. Decomposição de risco via contribuições lineares é uma aproximação**
A contribuição $\hat{\beta}_j \cdot x_j$ no espaço linear do logit não é a contribuição na probabilidade (escala não-linear). Para uma decomposição mais precisa, usar efeitos marginais:
```python
# Efeito marginal de x_j na probabilidade predita:
p = model.predict_proba(X)[:, 1]
marginal_j = beta_j * p * (1 - p)  # derivada da logística
```

**4. O limiar de alto risco (0,30 ou top 10%) precisa ser calibrado**
Com taxa base de ~0,7% de células-semana (dado de tiroteios — roubo/furto é mais frequente, taxa a confirmar), um limiar de 0,30 pode ser alto ou baixo demais. Recomendar: plotar histograma de `prob_t1` após estimação e escolher limiar no cotovelo da distribuição.

**5. Feedback loop entre recomendação e próxima estimação**
Se a Prefeitura agir com base no dashboard (ex: RioLuz repara iluminação), o modelo na semana seguinte vai captar essa mudança nos chamados 1746 — e possivelmente reduzir a probabilidade predita. Isso é o comportamento desejado, mas precisa ser comunicado na apresentação como evidência de efetividade, não como "o modelo errou".

---

## Referências

- Cohen & Felson (1979). Routine Activity Theory. *American Sociological Review* 44(4).
- Wheeler (2018). 311 Calls and Crime. *Crime & Delinquency* 64(14).
- Chalfin et al. (2019). Iluminação e crime. NBER WP 25798.
- Mohler et al. (2011/2015). Near-repeat e PredPol. *JASA*.
- Johnson & Bowers (2004). Near-repeat burglary. *Security Journal*.
- Caplan & Kennedy (2016). Risk Terrain Modeling.
- O'Brien & Sampson (2015). 311 e desordem social. *JRCD* 52(4).
