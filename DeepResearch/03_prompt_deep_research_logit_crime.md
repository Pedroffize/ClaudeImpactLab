# Modelo Logit Espacial para Previsão de Roubo/Furto — Polígonos de Atuação da FM
**Versão 4 — Escopo restrito à FM, output como mapa de probabilidades por horizonte**  
**Atualizado: 24/05/2026**

---

## TL;DR

- **Escopo geográfico:** restrito aos micropolígonos dentro dos polígonos de atuação da **Força Municipal (FM)** — definição dos polígonos em MD separado
- **Variável dependente:** `P(roubo_furto_{h,t+s} = 1 | X_{h,t})` — probabilidade de ≥ 1 roubo ou furto no micropolígono $h$ no horizonte $t+s$, estimada com os dados mais recentes disponíveis em $t$
- **Horizontes:** s = 1 semana (operacional), s = 2 semanas, s = 4 semanas — estimados em modelos separados ou com dummy de horizonte
- **Output final:** mapa coroplético dos micropolígonos da FM colorido pela probabilidade predita, selecionável por horizonte (t+1, t+2, t+4)
- **Inputs:** histórico próprio do crime (lags 1–12 semanas), lag espacial dos vizinhos, desordem urbana via 1746, policiamento em t
- **Efeitos fixos** no nível do polígono-mãe da FM (bairro/setor), definido externamente

> **Nota:** A definição dos micropolígonos, grade H3 e spatial join estão documentados em MD separado. Este arquivo assume que o vetor de unidades geográficas $h$ — já filtrado para os polígonos da FM — está construído e disponível como DataFrame.

---

## 1. Mudança de Rótulo: de Tiroteio para Roubo/Furto

### Por que importa

O modelo anterior usava Fogo Cruzado como rótulo — eventos de disparo de arma de fogo. Roubo e furto têm dinâmica diferente:

| Dimensão | Tiroteio (Fogo Cruzado) | Roubo/Furto |
|---|---|---|
| Fonte de dados disponível no Rio | Fogo Cruzado (OSC) — alta qualidade, baixo volume (~2.500/ano na RMBH) | ISP-RJ (estadual) — BO de Polícia Civil por CISP/bairro; sem geocoding fino público | 
| Granularidade geográfica | Coordenada exata via app | Agregado por CISP (≈ bairro) |
| Frequência do evento | Raro (~0,7% das células-semana) | Moderado a alto — depende da área |
| Viés de sub-registro | Médio (visibilidade auditiva) | Alto em favelas, baixo em zonas comerciais |
| Relação com policiamento | Alta (36% em operações) | Moderada (efeito dissuasão documentado) |

> **⚠️ Problema crítico de dados:** O ISP-RJ não disponibiliza BOs geocodificados em nível de logradouro de forma aberta. Os dados públicos estão agregados por **CISP** (Circunscrição da Delegacia) — equivalente aproximado a bairro/conjunto de bairros. Isso limita a granularidade mínima do modelo ao **nível de bairro**, não ao hexágono H3 res 9 (a menos que dados finos sejam liberados no kickoff do hackathon).

**Solução prática:**
- **Nível do modelo:** H3 resolução 8 (~0,7 km²) ou bairro, não res 9, se o rótulo vier de CISP
- **Se dados geocodificados de BO forem liberados no kickoff:** migrar para H3 res 9 imediatamente
- **Alternativa de rótulo:** usar chamados 1746 de categoria "Roubo/Furto" se existirem — verificar no kickoff
- **Rótulo híbrido:** combinar chamados de "perturbação do sossego com violência" + dados ISP como proxy

---

## 2. Output: Mapa de Probabilidades por Horizonte

O output central do modelo é um **mapa coroplético** dos micropolígonos dentro dos polígonos de atuação da FM, onde cada célula é colorida pela probabilidade predita de roubo/furto no horizonte escolhido.

### Estrutura do output

```
Para cada micropolígono h ∈ FM e cada horizonte s ∈ {1, 2, 4} semanas:
    → P(crime_{h, t+s} = 1 | X_{h,t})   # estimado com dados até t (semana atual)
```

O usuário seleciona o horizonte (t+1, t+2, t+4) e o mapa atualiza as cores. Micropolígonos fora dos polígonos da FM são excluídos do dataset antes da estimação — não aparecem no mapa.

### Exemplo de visualização (folium/pydeck)

```python
import folium
import pandas as pd

def plot_risk_map(df_pred, horizon=1, top_pct=0.25):
    """
    df_pred: DataFrame com colunas [hex_id, geometry, prob_t1, prob_t2, prob_t4]
    horizon: 1, 2 ou 4
    Plota mapa coroplético dos micropolígonos da FM colorido por prob_t{horizon}.
    """
    col = f'prob_t{horizon}'
    m = folium.Map(location=[-22.91, -43.17], zoom_start=12, tiles='CartoDB dark_matter')

    folium.Choropleth(
        geo_data=df_pred.__geo_interface__,
        data=df_pred,
        columns=['hex_id', col],
        key_on='feature.properties.hex_id',
        fill_color='YlOrRd',
        fill_opacity=0.75,
        line_opacity=0.1,
        legend_name=f'P(roubo/furto) — t+{horizon} semana(s)',
        nan_fill_color='transparent',
    ).add_to(m)

    # Destacar top 25% de risco
    threshold = df_pred[col].quantile(1 - top_pct)
    high_risk = df_pred[df_pred[col] >= threshold]
    folium.GeoJson(
        high_risk.__geo_interface__,
        style_function=lambda x: {'color': 'red', 'weight': 1.5, 'fillOpacity': 0}
    ).add_to(m)

    return m
```

### Pipeline de predição com dados recentes

```python
def predict_current_risk(model_t1, model_t2, model_t4,
                          df_features_fm, reference_week):
    """
    Dado o DataFrame de features dos micropolígonos da FM
    na semana de referência (semana mais recente disponível),
    retorna probabilidades para t+1, t+2, t+4.
    """
    X = build_feature_matrix(df_features_fm, reference_week)  # ver Seção 6

    df_pred = df_features_fm[['hex_id', 'geometry', 'id_poligono_fm']].copy()
    df_pred['prob_t1'] = model_t1.predict_proba(X)[:, 1]
    df_pred['prob_t2'] = model_t2.predict_proba(X)[:, 1]
    df_pred['prob_t4'] = model_t4.predict_proba(X)[:, 1]

    return df_pred
```

---

## 3. Especificação Formal do Modelo

### Restrição de escopo

O dataset é filtrado **antes** da estimação para incluir apenas micropolígonos $h \in \mathcal{FM}$, onde $\mathcal{FM}$ é o conjunto de micropolígonos que intersectam os polígonos de atuação da FM (definido em MD separado):

```python
df = df[df['id_poligono_fm'].notna()]  # apenas micropolígonos dentro da FM
```

### Variável dependente por horizonte

$$y_{h,t+s} = \mathbb{1}\{\text{≥ 1 roubo ou furto em } h \text{ na semana } t+s\}, \quad s \in \{1, 2, 4\}$$

Um modelo separado é estimado para cada horizonte $s$. As features são sempre construídas em $t$ (semana mais recente com dados disponíveis).

### Modelo logit para cada horizonte s

$$\Pr(y_{h,t+s}=1 \mid X_{h,t}) = \Lambda\!\left( \alpha_{b(h)} + \underbrace{\sum_{k} \beta_k^{(s)}\, y_{h,t-k}}_{\text{histórico próprio}} + \underbrace{\gamma^{(s)}\, [Wy_t]_h}_{\text{lag espacial}} + \underbrace{\delta^{(s)'} Z^{\text{desordem}}_{h,t}}_{\text{desordem urbana}} + \underbrace{\phi^{(s)'} P_{h,t}}_{\text{policiamento em t}} + \underbrace{\theta^{(s)'} D_t}_{\text{temporal}} \right)$$

onde:
- $\Lambda(\cdot)$ = função logística
- $\alpha_{b(h)}$ = efeito fixo do polígono-mãe da FM ao qual o micropolígono $h$ pertence
- $y_{h,t-k}$ = ocorrência do crime no próprio micropolígono nas semanas $t-1, t-2, t-4, t-12$
- $[Wy_t]_h$ = média dos $y_t$ dos vizinhos imediatos de $h$ (ring-1), **apenas vizinhos também dentro da FM**
- $Z^{\text{desordem}}_{h,t}$ = vetor de variáveis de desordem urbana via 1746 (ver Seção 4)
- $P_{h,t}$ = vetor de variáveis de policiamento no período t (ver Seção 5)
- $D_t$ = dummies temporais (semana do ano em sin/cos, feriado, mês)
- Os coeficientes $\beta^{(s)}, \gamma^{(s)}, \delta^{(s)}, \phi^{(s)}, \theta^{(s)}$ variam por horizonte — modelos estimados separadamente

### Por que modelos separados por horizonte e não um único modelo?

A literatura near-repeat (Johnson & Bowers 2004; Mohler et al. 2011) mostra que o **decaimento temporal do risco** é não-linear e horizonte-específico: o coeficiente de `y_lag1` tem peso muito maior em s=1 do que em s=4, onde variáveis estruturais (desordem, policiamento) ganham peso relativo. Estimar um modelo único com dummy de horizonte impõe restrições paramétricas desnecessárias. O custo computacional de três logits é trivial.

---

## 4. Variáveis de Desordem Urbana (inputs Z)

Baseado na imagem dos fatores relevantes para o crime e nos órgãos responsáveis por resolvê-los:

| Variável | Construção a partir do 1746 | Órgão responsável | Referência na literatura |
|---|---|---|---|
| `n_ilum_apagada_4w` | Contagem de chamados tipo "Iluminação Pública – lâmpada apagada" nas 4 semanas anteriores, no hex ou no ring-1 | **RioLuz** — manutenção de postes | Wheeler 2018; Chalfin et al. 2019 (NBER WP 25798) — redução de 36% crimes noturnos com iluminação |
| `n_lixo_entulho_4w` | Chamados de "Limpeza Urbana – lixo/entulho" nas 4 semanas | **Comlurb** — retirada de lixo e entulho | Wheeler 2018 — efeito (+) pequeno mas robusto |
| `n_vegetacao_obst_4w` | Chamados de "Vegetação – poda obstruindo iluminação/passeio" nas 4 semanas | **Comlurb** — podas | Inferência de RTM (Caplan & Kennedy 2016) — obstrução visual aumenta oportunidade |
| `n_obstaculo_calcada_4w` | Chamados de "Obstáculo no passeio" (calçada estreita, comércio irregular, mobiliário) nas 4 semanas | **SEOP** — remoção de estruturas irregulares | RTM — obstáculos reduzem "capable guardian" (Cohen & Felson 1979) |
| `n_situacao_rua_4w` | Chamados relacionados a pessoas em situação de rua nas 4 semanas | **SMAS** — ações de abordagem e assistência | O'Brien & Sampson 2015 — indicador de desordem social |
| `n_retencao_transito_4w` | Chamados de "Trânsito – ponto de retenção / estacionamento irregular" nas 4 semanas | **GM-Rio** — fiscalização | Inferência de CPTED (Crime Prevention Through Environmental Design) |
| `n_esconderijo_mobiliario_4w` | Chamados de "Mobiliário urbano obstruindo visibilidade" nas 4 semanas | **Seconserva** — alternativas de mitigação | CPTED — natural surveillance |

### Como adicionar variáveis de desordem dinamicamente

```python
# Dicionário de categorias 1746 → nome da variável
CATEGORIAS_DESORDEM = {
    'Iluminação Pública': 'n_ilum',
    'Limpeza Urbana': 'n_lixo',
    'Vegetação': 'n_vegetacao',
    'Obstáculo no Passeio': 'n_obstaculo',
    'Situação de Rua': 'n_situacao_rua',
    'Retenção de Trânsito': 'n_transito',
    'Mobiliário Urbano': 'n_mobiliario',
}

def build_desordem_features(df_1746, hex_col='hex_id', date_col='data_inicio',
                             tipo_col='tipo', lags_weeks=[1, 2, 4]):
    """
    Agrega chamados 1746 por hex × semana para cada categoria,
    gerando features defasadas para o modelo.
    """
    features = {}
    for categoria, nome in CATEGORIAS_DESORDEM.items():
        df_cat = df_1746[df_1746[tipo_col].str.contains(categoria, na=False)]
        weekly = (df_cat.groupby([hex_col, pd.Grouper(key=date_col, freq='W')])
                       .size().reset_index(name='count'))
        for lag in lags_weeks:
            weekly[f'{nome}_{lag}w'] = weekly.groupby(hex_col)['count'].shift(lag)
        features[nome] = weekly
    return features
```

---

## 5. Variáveis de Policiamento em t (inputs P)

Esta é a principal adição ao modelo padrão da literatura. O objetivo é incluir a **presença/intensidade de policiamento no período t** como preditor do crime em t+1, capturando tanto o efeito dissuasão quanto a endogeneidade (mais policiamento em áreas de risco).

### Variáveis sugeridas e fontes

| Variável | Descrição | Fonte | Sinal esperado | Endogeneidade |
|---|---|---|---|---|
| `n_cameras_ring` | Número de câmeras CIVITAS ativas no hex e ring-1 | CIVITAS (confirmar no kickoff se dados forem liberados) | (-) dissuasão | Baixa — câmeras são fixas |
| `cobertura_moto_t` | Indicador binário ou intensidade de rota de moto-patrulha GM-Rio no hex na semana t | GM-Rio (a confirmar no kickoff) | (-) dissuasão, mas (+) detectabilidade | **Alta** — rotas vão para áreas de risco |
| `n_abordagens_gm_t` | Contagem de ações da GM-Rio no hex na semana t | GM-Rio operacional (a confirmar) | Ambíguo | **Alta** |
| `n_acoes_seop_t` | Remoções de estruturas irregulares pela SEOP no hex | SEOP / 1746 status "concluído" | (-) via redução de obstáculos | Baixa-média |
| `n_podas_comlurb_t` | Podas realizadas pela Comlurb no hex | Comlurb / 1746 status "concluído" | (-) via melhora de visibilidade | Baixa |
| `n_manutencao_rioluz_t` | Postes reparados pela RioLuz no hex | RioLuz / 1746 status "concluído" | (-) via iluminação | Baixa |
| `radar_velocidade_ring` | Presença de radar de velocidade no hex ou ring-1 | CIVITAS | (-) via redução velocidade/fuga | Baixa — fixo |

### Como extrair policiamento a partir do 1746 (proxy)

Mesmo que dados operacionais de GM-Rio e CIVITAS não estejam disponíveis, é possível construir proxies de policiamento a partir do próprio 1746:

```python
# Proxy de policiamento: chamados com status "Concluído" pela GM-Rio
# indicam presença de agente no local
df_gm = df_1746[
    (df_1746['orgao_responsavel'].str.contains('GM-Rio|Guarda Municipal', na=False)) &
    (df_1746['status'] == 'Fechado')
]

# Proxy de câmera: usar dados públicos do OpenStreetMap (câmeras de segurança)
# via overpass API como fallback se CIVITAS não for liberado
import overpy
api = overpy.Overpass()
result = api.query("""
    [out:json];
    node["man_made"="surveillance"](-23.08,-43.80,-22.74,-43.09);
    out body;
""")
```

### Tratamento da endogeneidade do policiamento

O policiamento em t é endógeno ao crime esperado em t: mais patrulha vai para onde se espera mais crime. Isso viola a hipótese de exogeneidade das covariáveis no logit e pode enviesar os coeficientes de $P_{h,t}$.

**Estratégias de mitigação:**

1. **Incluir como controle, não como causa**: reportar coeficiente de policiamento como "associação condicional", não como efeito causal
2. **Variável instrumental (IV)**: usar variação exógena no policiamento — ex: escala de guarnições por turno determinada administrativamente, não pelo risco observado
3. **Efeito fixo de hex**: absorve a tendência estável de policiamento por área (hexágonos sempre mais patrulhados vs. menos)
4. **Defasar policiamento**: usar $P_{h,t-1}$ em vez de $P_{h,t}$ para reduzir simultaneidade

```python
# Versão com policiamento defasado (menos endógeno)
df['cobertura_moto_lag1'] = df.groupby('hex_id')['cobertura_moto_t'].shift(1)

# Versão com efeito fixo de hex (absorve padrão estável)
# implementar como dummy de hex_id no vetor X
```

---

## 6. Estrutura Completa do Vetor de Features

```python
FEATURES = {
    # Grupo 1: Histórico próprio do crime
    'historico': ['y_lag1', 'y_lag2', 'y_lag4', 'y_lag12', 'n_crimes_12w'],
    
    # Grupo 2: Lag espacial
    'espacial': ['W_y_lag1', 'W_y_lag2'],
    
    # Grupo 3: Desordem urbana via 1746 (defasadas 1–4 semanas)
    'desordem': [
        'n_ilum_4w',           # iluminação apagada (RioLuz)
        'n_lixo_4w',           # lixo/entulho (Comlurb)
        'n_vegetacao_4w',      # vegetação obstruindo (Comlurb)
        'n_obstaculo_4w',      # obstáculos no passeio (SEOP)
        'n_situacao_rua_4w',   # situação de rua (SMAS)
        'n_transito_4w',       # retenção de trânsito (GM-Rio)
        'n_mobiliario_4w',     # mobiliário obstruindo visibilidade (Seconserva)
    ],
    
    # Grupo 4: Policiamento em t (ou t-1 se endógeno)
    'policiamento': [
        'n_cameras_ring',          # câmeras CIVITAS (fixo)
        'radar_velocidade_ring',   # radares (fixo)
        'cobertura_moto_lag1',     # rota moto-patrulha (defasada)
        'n_manutencao_rioluz_t',   # postes reparados (proxy de presença)
        'n_acoes_seop_lag1',       # remoções SEOP (defasada)
    ],
    
    # Grupo 5: Temporal
    'temporal': [
        'week_sin', 'week_cos',    # sazonalidade semanal
        'is_holiday_week',         # feriado
        'month',                   # mês
    ],
    
    # Grupo 6: Efeitos fixos (one-hot)
    'fixed_effects': ['bairro_fe'],  # dummies de polígono-mãe
}
```

---

## 7. Implementação Modular — Três Modelos por Horizonte, Escopo FM

```python
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

class CrimeLogitFM:
    """
    Modelo logit para previsão de roubo/furto nos micropolígonos da FM.
    - Escopo restrito: apenas micropolígonos com id_poligono_fm preenchido
    - Um modelo por horizonte s ∈ {1, 2, 4} semanas
    - Adicione grupos de features via add_feature_group() sem reescrever o pipeline
    """

    HORIZONS = [1, 2, 4]  # semanas

    def __init__(self, feature_groups=None):
        self.feature_groups = feature_groups or FEATURES
        self.models = {}  # {s: pipeline}

    def _build_pipeline(self):
        numeric_cols = [f for g in ['historico', 'espacial', 'desordem',
                                     'policiamento', 'temporal']
                          for f in self.feature_groups.get(g, [])]
        cat_cols = self.feature_groups.get('fixed_effects', [])

        preprocessor = ColumnTransformer([
            ('num', 'passthrough', numeric_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols)
        ])
        return Pipeline([
            ('prep', preprocessor),
            ('logit', LogisticRegression(
                penalty='l2', C=1.0,
                class_weight='balanced',
                solver='liblinear',
                max_iter=1000
            ))
        ]), numeric_cols, cat_cols

    def fit(self, df):
        """
        df deve conter:
          - id_poligono_fm: não-nulo apenas para micropolígonos dentro da FM
          - crime_t{s}: variável dependente para cada horizonte s
          - todas as features definidas em self.feature_groups
        """
        df_fm = df[df['id_poligono_fm'].notna()].copy()

        for s in self.HORIZONS:
            y_col = f'crime_t{s}'
            assert y_col in df_fm.columns, f"Coluna {y_col} não encontrada"

            pipeline, numeric_cols, cat_cols = self._build_pipeline()
            X = df_fm[numeric_cols + cat_cols].fillna(0)
            y = df_fm[y_col]

            pipeline.fit(X, y)
            self.models[s] = (pipeline, numeric_cols, cat_cols)
            print(f"Modelo s={s} treinado | n={len(y)} | positivos={y.sum()} ({y.mean():.2%})")

        return self

    def predict_map(self, df_current):
        """
        df_current: features dos micropolígonos FM na semana mais recente (t).
        Retorna DataFrame com colunas [hex_id, geometry, prob_t1, prob_t2, prob_t4].
        """
        df_fm = df_current[df_current['id_poligono_fm'].notna()].copy()
        result = df_fm[['hex_id', 'geometry', 'id_poligono_fm']].copy()

        for s in self.HORIZONS:
            pipeline, numeric_cols, cat_cols = self.models[s]
            X = df_fm[numeric_cols + cat_cols].fillna(0)
            result[f'prob_t{s}'] = pipeline.predict_proba(X)[:, 1]

        return result

    def add_feature_group(self, group_name, feature_list):
        """Adiciona um grupo novo de variáveis sem alterar os modelos já treinados."""
        self.feature_groups[group_name] = feature_list
        return self
```

### Uso típico

```python
# 1. Carregar dados históricos (micropolígonos FM × semanas)
df_hist = load_panel_fm()  # retorna painel longo com crime_t1, crime_t2, crime_t4 e features

# 2. Treinar os três modelos
model = CrimeLogitFM()
model.fit(df_hist)

# 3. Predição com dados mais recentes
df_now = load_current_week_fm()  # features da semana atual para todos os micros da FM
df_pred = model.predict_map(df_now)

# 4. Plotar mapa por horizonte
plot_risk_map(df_pred, horizon=1)   # próxima semana
plot_risk_map(df_pred, horizon=2)   # em 2 semanas
plot_risk_map(df_pred, horizon=4)   # em 4 semanas
```

---

## 8. Validação e Métricas

```python
from sklearn.metrics import roc_auc_score, average_precision_score
import pysal.explore.esda as esda

def evaluate_model(model, X_test, y_test, hex_weights):
    probs = model.predict_proba(X_test)
    
    metrics = {
        'AUC_ROC': roc_auc_score(y_test, probs),
        'AUC_PR': average_precision_score(y_test, probs),  # mais informativo p/ evento raro
        'PAI': compute_pai(y_test, probs, top_pct=0.10),   # ver abaixo
    }
    
    # Diagnóstico espacial: Moran's I dos resíduos
    residuals = y_test - probs
    mi = esda.Moran(residuals.values, hex_weights)
    metrics['MoranI_residuals'] = mi.I
    metrics['MoranI_pvalue'] = mi.p_sim
    
    return metrics

def compute_pai(y_true, y_proba, top_pct=0.10):
    """
    Prediction Accuracy Index (Chainey et al. 2008):
    % eventos capturados nas top_pct áreas de risco ÷ top_pct
    Valores > 5 são considerados muito bons na literatura.
    """
    n = len(y_true)
    n_top = int(n * top_pct)
    top_idx = np.argsort(y_proba)[::-1][:n_top]
    captured = y_true.iloc[top_idx].sum()
    total_events = y_true.sum()
    if total_events == 0:
        return 0
    return (captured / total_events) / top_pct
```

---

## 9. Thresholds para Ajuste do Modelo

| Condição | Ação |
|---|---|
| AUC PR < 0,10 | Reduzir granularidade para H3 res 7 (~5 km²) ou nível de bairro; ampliar horizonte para 2 semanas |
| Moran's I residual > 0,10 (p<0,01) | Adicionar lag espacial de segundo grau `W²y` ou efeitos fixos de RA |
| Coeficiente de policiamento positivo e significativo | Reportar endogeneidade; usar versão defasada ou IV |
| Desbalanceamento > 99% zeros | Manter `class_weight='balanced'`; considerar logit de Firth via `logistf` (R) ou implementação manual |
| Features 1746 com p > 0,10 consistente | Reportar efeito pequeno — coerente com Wheeler 2018; destacar que modelo ainda é útil via histórico próprio |

---

## 10. Framing Ético e de Apresentação

**O que é:** Sistema de alerta de risco de roubo/furto por microárea, baseado em dados abertos municipais e histórico civil de ocorrências, com auditoria de viés geográfico.

**O que não é:** Ferramenta de alocação policial automatizada. Nenhum output do modelo deve ser usado para decidir patrulhamento sem revisão humana.

**Por que usar chamados 1746 como input e não como rótulo:**
- Chamados de serviços urbanos são gerados pelo cidadão, não pela patrulha → menor viés de feedback
- O rótulo ideal são registros de ocorrência da Polícia Civil (ISP), geocodificados — confirmar disponibilidade no kickoff

**Auditoria obrigatória antes da demo:**
```python
# Verificar se micropolígonos de alto risco concentram população vulnerável
df_risco = df.assign(decil_risco=pd.qcut(df['prob_pred'], 10, labels=False))
audit = (df_risco.groupby('decil_risco')
                 .agg(pct_pop_negra=('pct_pop_negra', 'mean'),
                      n_hex=('hex_id', 'count'))
                 .reset_index())
print(audit)  # Se decil 9 tiver pct_pop_negra >> outros decis, reportar honestamente
```

---

## 11. Fontes e Referências

- **Wheeler, A. P. (2018).** "The Effect of 311 Calls for Service on Crime in D.C. at Microplaces." *Crime & Delinquency* 64(14):1882–1903.
- **O'Brien, D. T. & Sampson, R. J. (2015).** "Public and Private Spheres of Neighborhood Disorder." *Journal of Research in Crime and Delinquency* 52(4):486–510.
- **Mohler et al. (2011).** "Self-Exciting Point Process Modeling of Crime." *JASA* 106(493):100–108.
- **Mohler et al. (2015).** RCT PredPol. *JASA* 110(512):1399–1411.
- **Caplan, Kennedy & Miller (2011).** Risk Terrain Modeling. *Justice Quarterly* 28(2):360–381.
- **Chalfin et al. (2019).** Iluminação e crime. NBER WP 25798.
- **Lum & Isaac (2016).** Feedback runaway. *Significance* 13(5):14–19.
- **Ensign et al. (2018).** Runaway feedback loops. *PMLR* 81:160–171.
- **Chainey, Tompson & Uhlig (2008).** PAI. *Security Journal* 21:4–28.
- **Cohen & Felson (1979).** Routine Activity Theory. *American Sociological Review* 44(4):588–608.
- **Cameron & Miller (2015).** Cluster-robust SE. *Journal of Human Resources* 50(2):317–372.
- **ISP-RJ:** [ispdados.rj.gov.br](http://www.ispdados.rj.gov.br/)
- **dados.rio BigQuery:** `datario.adm_central_atendimento_1746.chamado`
- **H3:** [h3geo.org](https://h3geo.org/) | `pip install h3`
