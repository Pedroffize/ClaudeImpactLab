# Decisão de Subdivisão Espacial — Modelo Logit de Previsão de Roubo (CompStat-Rio)
*Autor:* Arthur · *Data:* 24/05/2026 · *Projeto:* claude_impact_lab_compstat_rio

---

## TL;DR da decisão

A unidade de previsão (micropolígono) será o **hexágono H3 resolução 9** (~0,1 km², aresta ≈ 175 m), aninhado dentro da **área de atuação da Força Municipal** (`nome_subar`), que entra como **efeito fixo** (polígono-mãe). O universo de células é definido pela cobertura H3 de cada área da FM acrescida de um **buffer de borda de 120 m**. O recorte temporal é a **semana ISO**, compatível com a cadência das reuniões de CompStat.

Esta decisão difere da premissa do arquivo `03_prompt_deep_research_logit_crime.md`, que assumia rótulo agregado por CISP (nível de bairro) por indisponibilidade de geocoding. **Os dados do projeto contradizem essa premissa:** as ocorrências de roubo estão georreferenciadas em coordenada exata, o que libera a granularidade fina que o briefing exige ("segmento de rua, horário e padrão de ocorrência").

---

## 1. O que os dados realmente são

Inspeção das bases em `dados/` (24/05/2026):

| Base | Registros | Geometria | Papel no modelo |
|---|---|---|---|
| `df_ocorrencias_tratado` | 115.354 (115.318 com coord. válida) | **POINT lat/lon** | **Rótulo** (roubo a transeunte, de celular, em coletivo; 2020–2024) |
| `cameras_areas_fm` | 985 | POINT, marcadas por área FM | Policiamento (câmeras CIVITAS, estático) |
| `fatores_urbanos` | 8.229 | coord. x/y + id_subarea | Desordem urbana (20 fatores) |
| `disk_denuncia` | 83.549 | lat/lon (vírgula decimal) | Dinâmica criminal qualitativa |
| `dominio_territorial` | 1.627 | POLYGON por facção | Contexto territorial |
| `sh_area_forca` | **8 polígonos** | POLYGON | **Polígono-mãe** (áreas de atuação da FM) |

**Pontos críticos confirmados:**

- **O rótulo é georreferenciado.** 115.318 de 115.354 roubos têm coordenada plausível no Rio. As ~36 linhas restantes têm latitude do tipo `-22901` (ponto decimal perdido) e são descartadas; ~140 registros têm o campo data corrompido (ex.: `26/03/1924`) e caem fora da janela 2020–2024.
- **As 8 áreas da FM são pequenas e densas.** Área entre 0,33 e 1,67 km² (média 1,05 km²). Concentram **9,1% de todos os roubos da cidade** — são, de fato, manchas criminais. O shapefile traz 8 das 22 áreas prioritárias, exatamente as que possuem RELINT em `relints/`.
- **Tudo é cruzável por hexágono.** Como todas as covariáveis têm coordenada (ou polígono), o spatial join ponto→hexágono e polígono→hexágono resolve a integração entre silos sem depender de chave administrativa.

---

## 2. Por que H3 resolução 9 (e não 7, 8 ou 10)

A escolha da resolução é um **trade-off entre granularidade operacional e densidade estatística**. Em um modelo de evento binário semanal, resolução fina demais gera um painel quase todo zero (separação, coeficientes instáveis, AUC-PR degenerada); resolução grossa demais destrói exatamente a informação que orienta o emprego do efetivo a pé.

Medição empírica da densidade do painel em cada resolução, usando o universo realista de hexágonos que efetivamente contêm roubos nas 8 áreas (262 semanas):

| Resolução | Área da célula | Hex cobrindo as áreas | % de hex-semanas positivas | Leitura |
|---|---|---|---|---|
| res 7 | ~5,16 km² | ~13 | ~60% | Grosseiro demais — célula > área da FM |
| res 8 | ~0,74 km² | ~37 | ~44% | Quase balanceado, mas ~5 hex/área |
| **res 9** | **~0,10 km²** | **~135** | **~25%** | **Melhor equilíbrio** |
| res 10 | ~0,015 km² | ~552 | ~6% | Esparso demais para logit semanal |

A resolução 9 entrega ~17 hexágonos por área (granularidade de quarteirão/cluster de quarteirões) e uma taxa de positivos de ~25% no painel balanceado — longe do regime de evento raro que exigiria logit penalizado de Firth, e fino o suficiente para distinguir, dentro de "Presidente Vargas", o eixo da Uruguaiana do entorno da Central. É o nível que melhor aproxima o "segmento de rua" do briefing mantendo identificação estatística.

A resolução 10 (~aresta 65 m, praticamente um trecho de rua) é atraente conceitualmente, mas a 6% de positivos a maioria dos hexágonos nunca registra roubo em uma dada semana — o modelo viraria um classificador de "quase sempre zero". Fica como **camada de refino visual** (mapa de calor), não como unidade de estimação.

---

## 3. A hierarquia: micropolígono dentro do polígono-mãe

```
Área de atuação da FM  (nome_subar)          ← polígono-mãe = EFEITO FIXO α_a
        └── hexágonos H3 res 9               ← micropolígono = unidade de previsão
                └── covariáveis por semana t
```

O **efeito fixo de área da FM** absorve toda a heterogeneidade estável não observada do polígono-mãe — nível de circulação de pedestres, presença histórica de facção (cruzável com `dominio_territorial`), perfil socioeconômico, infraestrutura de transporte. Isso é o análogo, no logit, de um *within estimator*: os coeficientes das covariáveis passam a ser identificados pela variação **entre hexágonos da mesma área** e **ao longo do tempo**, não pela comparação entre áreas estruturalmente distintas (Campo Grande vs. Botafogo). Para um problema de segurança pública isso é decisivo, porque sem o efeito fixo o modelo confundiria "área perigosa" com "fator de risco do hexágono".

Há camadas administrativas alternativas nas bases (`aisp`/`risp` da polícia, `id_bairro`/`bairro_nome`, `id_subarea` em fatores). A área da FM é a escolha natural de polígono-mãe porque (i) é a unidade de **decisão operacional** do CompStat, (ii) é a unidade dos **RELINTs**, e (iii) é onde o efetivo de 600 agentes é efetivamente alocado. Bairro ou AISP entram, se necessário, apenas como nível adicional para áreas que cruzam fronteiras.

### Tratamento da borda

Como as áreas têm ~1 km², roubos a poucos metros da divisa caem em hexágonos cujo centro fica fora do polígono. Por isso o universo de células é a cobertura H3 da área **mais um buffer de 120 m**. Hexágonos capturados pelo buffer de duas áreas vizinhas são atribuídos à área de centroide mais próximo. Sem esse cuidado, perde-se sistematicamente o crime de fronteira — justamente onde patrulha de uma área "empurra" o crime para a adjacente (deslocamento espacial).

---

## 4. Heterogeneidade de volume entre áreas (o ponto de atenção)

A densidade varia muito entre as 8 áreas (res 9, com buffer):

| Área FM | hex res9 | roubos/semana | % hex-sem positivo |
|---|---:|---:|---:|
| Presidente Vargas – Campo de Santana – Central | 22 | 21,6 | 51,8% |
| Rodoviária – Terminal Gentileza – Leopoldina | 27 | 9,4 | 21,9% |
| Estações São Francisco Xavier – Afonso Pena | 21 | 7,1 | 25,7% |
| Praia de Botafogo – Marquês de Abrantes | 17 | 4,5 | 21,0% |
| Metrô Botafogo – São Clemente – Voluntários | 14 | 4,4 | 24,9% |
| Rio Sul | 10 | 2,5 | 20,4% |
| Jardim de Alah | 7 | 1,6 | 17,9% |
| Campo Grande – Estação de Trem – Calçadão | 17 | 1,3 | **7,2%** |

Seis das oito áreas ficam na faixa confortável de 18–26% de positivos. **Campo Grande** (7,2%, 1,3 roubo/semana) é o caso-limite. Três salvaguardas, na ordem de preferência:

1. **Resolução adaptativa por área:** manter res 9 globalmente, mas estimar Campo Grande (e eventualmente Jardim de Alah) em **res 8**. O pipeline aceita `res` como parâmetro; basta rodar as duas resoluções e empilhar os painéis. É a opção mais limpa e preserva comparabilidade dentro de cada área.
2. **Horizonte de 2 semanas** para as áreas esparsas, dobrando a contagem de eventos por célula-período.
3. **Logit penalizado (Firth)** se mesmo assim houver separação em hexágonos sem nenhum evento — reduz o viés de amostra pequena nos coeficientes.

A regra prática de acionamento dessas salvaguardas (AUC-PR < 0,10, Moran's I residual etc.) já está na Seção 9 do `03_prompt_deep_research_logit_crime.md` e continua válida.

---

## 5. Dimensão temporal: semana + faixa horária

O rótulo permanece **semanal** (semana ISO), coerente com a cadência das reuniões de CompStat e com a literatura (`y_{h,t+1} = 1{≥1 roubo no hex h na semana t+1}`).

O briefing, porém, é explícito sobre **horário** ("mapeamento por segmento de rua, *horário* e padrão") e sobre decisão de **modalidade e turno** do efetivo (moto/viatura/a pé). O campo `hora` existe nas ocorrências. Recomenda-se, como segunda camada, **estratificar por faixa horária** (madrugada / manhã / tarde / noite) — seja como variável de composição do hexágono (ex.: % de roubos noturnos no histórico), seja como um segundo modelo hex × semana × faixa. Isso conecta a previsão à recomendação de turno de patrulhamento, que é um dos entregáveis do desafio. Mantido fora do recorte-base para não fragmentar demais o painel já na primeira versão.

---

## 6. Implementação

O arquivo `construir_painel_espacial.py` (nesta pasta) implementa exatamente esta decisão e foi executado com sucesso sobre os dados reais:

```
painel: 34.584 linhas | 132 hexágonos × 262 semanas | taxa de positivos: 25,2%
```

O módulo é parametrizado por `res`, então trocar a resolução (ex.: `run(res=8)` para Campo Grande) não exige reescrever o pipeline. Ele entrega o painel balanceado hex × semana com:

- Rótulo `y`
- Contagem `n_roubos`
- Efeito fixo `area_fm`
- Lags próprios (1, 2, 4, 12 semanas)
- Janela móvel de 12 semanas
- **Lag espacial** `W_y_lag1` (média dos vizinhos H3 ring-1)
- `n_cameras` e `n_fatores` por hexágono

As demais covariáveis (`disk_denuncia`, `dominio_territorial`) entram pelo mesmo padrão de spatial join já estabelecido no código.

**Saída:** `painel_hex_semana_res9.csv`, pronto para alimentar o `CrimeLogitModel` da Seção 7 do `03_prompt_deep_research_logit_crime.md`.

### Como indexar cada base ao hexágono

```python
import h3
import geopandas as gpd
import pandas as pd

# ── Ponto → hexágono (ocorrências, câmeras, fatores urbanos, disk_denuncia) ──
def point_to_hex(lat, lon, res=9):
    """Converte coordenada para hex_id H3."""
    return h3.geo_to_h3(float(lat), float(lon), res)

# Aplicar em qualquer base com lat/lon
df['hex_id'] = df.apply(lambda r: point_to_hex(r['latitude'], r['longitude']), axis=1)

# ── Polígono → hexágonos (dominio_territorial, sh_area_forca) ──
def polygon_to_hexes(geojson_polygon, res=9, buffer_m=120):
    """
    Retorna todos os hex_ids que cobrem o polígono,
    acrescido de buffer_m metros na borda.
    """
    import shapely.geometry as sg
    from pyproj import Transformer

    # Reprojetar para UTM-23S para buffer métrico
    t_fwd = Transformer.from_crs("EPSG:4326", "EPSG:31983", always_xy=True)
    t_inv = Transformer.from_crs("EPSG:31983", "EPSG:4326", always_xy=True)

    poly = sg.shape(geojson_polygon)
    coords_utm = [t_fwd.transform(x, y) for x, y in poly.exterior.coords]
    poly_utm = sg.Polygon(coords_utm).buffer(buffer_m)
    coords_wgs = [t_inv.transform(x, y) for x, y in poly_utm.exterior.coords]
    poly_buffered = sg.Polygon(coords_wgs)

    geojson_buffered = sg.mapping(poly_buffered)
    return list(h3.polyfill_geojson(geojson_buffered, res))

# Gerar universo de hexágonos da FM com buffer
fm_hexes = []
for _, area in sh_area_forca.iterrows():
    hexes = polygon_to_hexes(area.geometry.__geo_interface__, res=9, buffer_m=120)
    fm_hexes += [{'hex_id': h, 'area_fm': area['nome_subar']} for h in hexes]
df_fm_hexes = pd.DataFrame(fm_hexes).drop_duplicates('hex_id')

# Resolver conflito de borda: hex em duas áreas → atribuir à mais próxima
# (já resolvido no construir_painel_espacial.py pelo centroide H3 mais próximo)

# ── Lag espacial: vizinhos ring-1 dentro da FM ──
def compute_spatial_lag(df_panel, y_col='y', hex_col='hex_id', fm_hexes_set=None):
    """
    Para cada hex_id e semana, calcula média de y dos vizinhos ring-1
    que também estão dentro da FM.
    """
    fm_set = fm_hexes_set or set(df_panel[hex_col].unique())

    def ring1_mean(hex_id, week_data):
        neighbors = h3.k_ring(hex_id, 1) - {hex_id}
        neighbors_in_fm = neighbors & fm_set
        if not neighbors_in_fm:
            return 0.0
        vals = week_data.reindex(list(neighbors_in_fm), fill_value=0)[y_col]
        return vals.mean()

    results = []
    for week, grp in df_panel.groupby('semana_iso'):
        week_indexed = grp.set_index(hex_col)
        for hex_id in grp[hex_col]:
            results.append({
                hex_col: hex_id,
                'semana_iso': week,
                'W_y_lag1': ring1_mean(hex_id, week_indexed)
            })
    return pd.DataFrame(results)
```

---

## 7. Resumo das escolhas

| Dimensão | Decisão | Justificativa central |
|---|---|---|
| Micropolígono | H3 res 9 (~0,1 km²) | Melhor trade-off densidade × granularidade (25% positivos) |
| Polígono-mãe | Área de atuação da FM (efeito fixo) | Unidade operacional/RELINT; absorve heterogeneidade estável |
| Universo de células | Cobertura H3 + buffer 120 m | Captura crime de borda em áreas de ~1 km² |
| Recorte temporal | Semana ISO (+ faixa horária opcional) | Cadência do CompStat; horário pedido no briefing |
| Áreas esparsas | res 8 / horizonte 2 sem / Firth | Campo Grande a 7,2% de positivos |
| Rótulo | Roubo georreferenciado, não CISP | Dados do projeto têm coordenada exata |

---

## 8. Relação com os outros arquivos do projeto

| Arquivo | O que este MD atualiza |
|---|---|
| `03_prompt_deep_research_logit_crime.md` | Substitui a premissa de rótulo agregado por CISP; confirma granularidade H3 res 9; valida salvaguardas de Seção 9 |
| `04_agente_dashboard_policy.md` | Confirma que `id_poligono_fm` = `nome_subar`; `df_geo` pode ser enriquecido com atributos de `fatores_urbanos` e `dominio_territorial` via spatial join por `hex_id` |
| `construir_painel_espacial.py` | Implementação desta decisão — saída `painel_hex_semana_res9.csv` é o input do `CrimeLogitFM.fit()` |
