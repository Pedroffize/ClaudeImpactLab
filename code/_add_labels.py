"""Adiciona dicionário FEATURE_LABELS + função pretty_label() em cell-02-config
e aplica em cf987706 (tabela), 7ec058e2 (mapas por área) e cell-22-risk-map.
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.load(open(NB_PATH, encoding="utf-8"))
cell_map = {c["id"]: i for i, c in enumerate(nb["cells"])}


# ─────────────────────────────────────────────────────────────────────────────
# 1) Append dictionary + pretty_label to cell-02-config
# ─────────────────────────────────────────────────────────────────────────────
config_addition = '''

# ── Dicionário de rótulos legíveis para policy makers ────────────────────────
# Converte nomes técnicos das features (n_fat_calcada, y_lag1, …) em descrições
# em português natural usadas nos mapas, popups e tabelas de drivers.

FEATURE_LABELS = {
    # Histórico do próprio hex
    "y_lag1":         "Houve crime na semana anterior",
    "y_lag2":         "Houve crime há 2 semanas",
    "y_lag4":         "Houve crime há 4 semanas",
    "y_lag12":        "Houve crime há 12 semanas",
    "n_crimes_12w":   "Crimes acumulados nas últimas 12 semanas",
    # Lag espacial
    "W_y_lag1":       "Crime na vizinhança imediata (semana anterior)",
    # Fatores urbanos (mapeados em cell-10-fatores)
    "n_fat_total":    "Fatores urbanos: total na área",
    "n_fat_ilum":     "Iluminação deficiente",
    "n_fat_vegetac":  "Vegetação obstruindo",
    "n_fat_lixo":     "Lixo / entulho acumulado",
    "n_fat_calcada":  "Calçada obstruída",
    "n_fat_transito": "Retenção de tráfego",
    "n_fat_mobil":    "Mobiliário urbano comprometido",
    "n_fat_sitrua":   "Situação de rua",
    # Policiamento
    "n_cameras":       "Câmeras no segmento",
    "n_cameras_ring1": "Câmeras na vizinhança imediata",
    # Sazonalidade temporal
    "week_sin":         "Sazonalidade semanal (ciclo anual)",
    "week_cos":         "Sazonalidade semanal (ciclo anual)",
    "is_holiday_week":  "Semana de feriado",
    # Denúncias
    "n_dd_lag1":      "Denúncias na semana anterior",
}

# Prefixos: tratamento dinâmico (orcrim_<faccao>, fe_area_<nome>)
def pretty_label(feat_name: str) -> str:
    """Retorna rótulo legível para um nome técnico de feature."""
    if feat_name in FEATURE_LABELS:
        return FEATURE_LABELS[feat_name]
    if feat_name.startswith("orcrim_"):
        faccao = feat_name.removeprefix("orcrim_")
        if faccao.lower() in ("sem domínio", "sem dominio"):
            return "Sem domínio territorial identificado"
        return f"Domínio territorial: {faccao}"
    if feat_name.startswith("fe_area_"):
        return "Efeito fixo da área FM"
    # Fallback: retorna o nome cru
    return feat_name
'''

# Append (não substituir) ao cell-02-config preservando o conteúdo existente
existing = nb["cells"][cell_map["cell-02-config"]]["source"]
if isinstance(existing, list):
    existing_str = "".join(existing)
else:
    existing_str = existing

# Evita duplicar se já estiver lá
if "FEATURE_LABELS" not in existing_str:
    new_src = existing_str.rstrip() + "\n" + config_addition
    nb["cells"][cell_map["cell-02-config"]]["source"] = new_src.splitlines(keepends=True)
    print("[cell-02-config] dicionário FEATURE_LABELS adicionado")
else:
    print("[cell-02-config] dicionário já presente, pulando")


# ─────────────────────────────────────────────────────────────────────────────
# 2) Update cf987706 (tabela) — aplica pretty_label nos drivers
# ─────────────────────────────────────────────────────────────────────────────
table_cell_src = '''# ── Top hexes de maior risco por área FM + drivers explicativos ──────────────
# Para cada área da Força Municipal, identifica os N hexes com maior P(crime T+1)
# e lista os top 3 drivers (variáveis com maior contribuição |β·x|) desses hexes.

TOP_N_POR_AREA = 5  # quantos hexes mostrar por área

if 1 in pred_dfs:
    df_pred1 = pred_dfs[1].copy()

    # Ordena por probabilidade dentro de cada área e pega os top N
    df_top = (
        df_pred1.sort_values(["area_fm", "prob_crime"], ascending=[True, False])
                .groupby("area_fm", group_keys=False)
                .head(TOP_N_POR_AREA)
                .copy()
    )

    # Ranking dentro da área (1 = maior risco)
    df_top["rank_area"] = (
        df_top.groupby("area_fm")["prob_crime"]
              .rank(ascending=False, method="first")
              .astype(int)
    )

    # Aplica pretty_label nos drivers para apresentação ao policy maker
    df_top["driver_1_label"] = df_top["top_driver_1"].apply(pretty_label)
    df_top["driver_2_label"] = df_top["top_driver_2"].apply(pretty_label)
    df_top["driver_3_label"] = df_top["top_driver_3"].apply(pretty_label)

    cols_show = [
        "area_fm", "rank_area", "hex_id", "prob_crime", "decil_risco",
        "driver_1_label", "contrib_top1",
        "driver_2_label", "contrib_top2",
        "driver_3_label", "contrib_top3",
    ]
    df_top_show = df_top[cols_show].copy()
    df_top_show["prob_crime"]   = (df_top_show["prob_crime"]   * 100).round(1)
    df_top_show["contrib_top1"] = (df_top_show["contrib_top1"] * 100).round(1)
    df_top_show["contrib_top2"] = (df_top_show["contrib_top2"] * 100).round(1)
    df_top_show["contrib_top3"] = (df_top_show["contrib_top3"] * 100).round(1)
    df_top_show = df_top_show.rename(columns={
        "prob_crime":     "P(crime)%",
        "driver_1_label": "Driver 1",
        "contrib_top1":   "contrib1_%",
        "driver_2_label": "Driver 2",
        "contrib_top2":   "contrib2_%",
        "driver_3_label": "Driver 3",
        "contrib_top3":   "contrib3_%",
    })

    print(f"Top {TOP_N_POR_AREA} hexes por área FM (horizonte T+1):")
    display(df_top_show.set_index(["area_fm", "rank_area"]))

    # Salva CSV e LaTeX com rótulos legíveis
    df_top_show.to_csv(OUTPUT_DIR / "top_drivers_por_area.csv", index=False)
    try:
        df_top_show.to_latex(
            OUTPUT_DIR / "top_drivers_por_area.tex",
            index=False, float_format="%.1f"
        )
    except Exception as e:
        print(f"(LaTeX export pulado: {e})")

    print(f"\\nSalvo: output/top_drivers_por_area.csv")
else:
    print("pred_dfs[1] indisponível — execute a Fase 4 antes")
'''
nb["cells"][cell_map["cf987706"]]["source"] = table_cell_src.splitlines(keepends=True)
nb["cells"][cell_map["cf987706"]]["outputs"] = []
nb["cells"][cell_map["cf987706"]]["execution_count"] = None
print("[cf987706] tabela atualizada com pretty_label")


# ─────────────────────────────────────────────────────────────────────────────
# 3) Update 7ec058e2 (mapas por área) — pretty_label no popup
# ─────────────────────────────────────────────────────────────────────────────
maps_cell_src = '''# ── Mapas individuais por área FM (HTML) ─────────────────────────────────────
# Gera um HTML separado para cada área da Força Municipal com:
#   • Contorno do polígono da área (linha grossa)
#   • Hexágonos H3 coloridos por P(crime T+1)
#   • Marcadores destacando os top hexes com drivers em LINGUAGEM NATURAL

import re
import unicodedata
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def slugify(text: str) -> str:
    """Converte nome da área em slug seguro para arquivo."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_str = nfkd.encode("ASCII", "ignore").decode("ASCII")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_str).strip("_").lower()
    return slug[:60]

if 1 in pred_dfs:
    df_pred1 = pred_dfs[1].copy()
    cmap = plt.cm.YlOrRd

    map_dir = OUTPUT_DIR / "mapas_por_area"
    map_dir.mkdir(exist_ok=True)

    print(f"Gerando mapas individuais em {map_dir}/...\\n")

    saved = []
    for area_name, poly in fm_polygons.items():
        df_area = df_pred1[df_pred1["area_fm"] == area_name].copy()
        if df_area.empty:
            print(f"  [skip] {area_name[:60]}: sem hexes preditos")
            continue

        cx, cy = poly.centroid.x, poly.centroid.y
        m = folium.Map(location=[cy, cx], zoom_start=15, tiles="CartoDB dark_matter")

        p_min = df_area["prob_crime"].min()
        p_max = df_area["prob_crime"].max()

        # ─── Contorno do polígono da área ───
        exterior = list(poly.exterior.coords)
        locations = [(lat, lon) for lon, lat in exterior]
        folium.Polygon(
            locations=locations,
            color="#4ecdc4",
            weight=3,
            fill=False,
            tooltip=f"Área FM: {area_name}",
        ).add_to(m)

        # ─── Hexes coloridos por risco ───
        hex_layer = folium.FeatureGroup(name="Hexes — risco T+1", show=True)
        for _, row in df_area.iterrows():
            boundary = h3.cell_to_boundary(row["hex_id"])
            poly_coords = [(lat, lon) for lat, lon in boundary]
            norm = (row["prob_crime"] - p_min) / (p_max - p_min + 1e-9)
            color_hex = mcolors.to_hex(cmap(norm))
            folium.Polygon(
                locations=poly_coords,
                color=color_hex,
                weight=0.5,
                fill=True,
                fill_color=color_hex,
                fill_opacity=0.7,
                tooltip=f"P(crime T+1): {row['prob_crime']:.1%}",
            ).add_to(hex_layer)
        hex_layer.add_to(m)

        # ─── Marcadores nos top hexes (popup em linguagem natural) ───
        top_layer = folium.FeatureGroup(name=f"Top {TOP_N_POR_AREA} hexes — drivers", show=True)
        df_area_top = df_area.nlargest(TOP_N_POR_AREA, "prob_crime")
        for rank, (_, row) in enumerate(df_area_top.iterrows(), start=1):
            lat_c, lon_c = h3.cell_to_latlng(row["hex_id"])
            # Traduz cada driver técnico → texto legível
            d1 = pretty_label(row["top_driver_1"])
            d2 = pretty_label(row["top_driver_2"])
            d3 = pretty_label(row["top_driver_3"])
            popup_html = (
                f"<b>#{rank} — P(crime T+1): {row['prob_crime']:.1%}</b><br>"
                f"Decil: {int(row.get('decil_risco', 0))}/10<br><br>"
                f"<b>Fatores que mais explicam:</b><br>"
                f"1. {d1} ({row['contrib_top1']:.1%})<br>"
                f"2. {d2} ({row['contrib_top2']:.1%})<br>"
                f"3. {d3} ({row['contrib_top3']:.1%})"
            )
            folium.CircleMarker(
                location=[lat_c, lon_c],
                radius=10,
                color="#ffffff",
                weight=2,
                fill=True,
                fill_color="#bd0026",
                fill_opacity=0.95,
                tooltip=f"#{rank} — {row['prob_crime']:.1%}",
                popup=folium.Popup(popup_html, max_width=340),
            ).add_to(top_layer)
        top_layer.add_to(m)

        # Título no canto superior esquerdo
        title_html = (
            f'<div style="position:fixed;top:10px;left:50px;z-index:1000;'
            f'background:rgba(20,20,20,0.9);color:white;padding:8px 14px;'
            f'border-radius:6px;font-family:Arial;font-size:13px;max-width:60%;">'
            f'<b>{area_name}</b><br>Risco T+1 — Logit L2'
            f'</div>'
        )
        m.get_root().html.add_child(folium.Element(title_html))

        folium.LayerControl(collapsed=False).add_to(m)

        slug = slugify(area_name)
        fname = f"mapa_risco_t1_{slug}.html"
        m.save(str(map_dir / fname))
        saved.append(fname)
        print(f"  OK {fname}")

    print(f"\\nTotal: {len(saved)} mapas salvos em output/mapas_por_area/")
else:
    print("pred_dfs[1] indisponível — execute a Fase 4 antes")
'''
nb["cells"][cell_map["7ec058e2"]]["source"] = maps_cell_src.splitlines(keepends=True)
nb["cells"][cell_map["7ec058e2"]]["outputs"] = []
nb["cells"][cell_map["7ec058e2"]]["execution_count"] = None
print("[7ec058e2] mapas por área atualizados com pretty_label")


# ─────────────────────────────────────────────────────────────────────────────
# 4) Update cell-22-risk-map — pretty_label no tooltip global
# ─────────────────────────────────────────────────────────────────────────────
risk_map_src = '''# ── Mapa de risco — predições T+1 sobre hexágonos FM ─────────────────────────

if 1 in pred_dfs:
    df_plot = pred_dfs[1].copy()

    m = folium.Map(location=[-22.92, -43.28], zoom_start=13, tiles="CartoDB dark_matter")

    # Colormap (amarelo → vermelho escuro) para risco dos hexes
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    cmap = plt.cm.YlOrRd

    prob_min = df_plot["prob_crime"].min()
    prob_max = df_plot["prob_crime"].max()

    # ─── Camada 1: contorno das áreas FM (polígonos reconstruídos via convex hull + buffer 120m) ───
    area_layer = folium.FeatureGroup(name="Áreas FM (contorno)", show=True)
    palette = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]
    for i, (area_name, poly) in enumerate(fm_polygons.items()):
        color = palette[i % len(palette)]
        exterior = list(poly.exterior.coords)
        locations = [(lat, lon) for lon, lat in exterior]
        folium.Polygon(
            locations=locations,
            color=color,
            weight=2.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.05,
            tooltip=f"Área FM: {area_name}",
            popup=folium.Popup(f"<b>{area_name}</b>", max_width=300),
        ).add_to(area_layer)
    area_layer.add_to(m)

    # ─── Camada 2: hexágonos H3 coloridos pelo risco T+1 ───
    hex_layer = folium.FeatureGroup(name="Hexágonos FM — Risco T+1", show=True)
    for _, row in df_plot.iterrows():
        boundary = h3.cell_to_boundary(row["hex_id"])
        polygon_coords = [(lat, lon) for lat, lon in boundary]
        norm = (row["prob_crime"] - prob_min) / (prob_max - prob_min + 1e-9)
        color_hex = mcolors.to_hex(cmap(norm))

        # Traduz drivers técnicos em linguagem natural
        top1 = pretty_label(row.get("top_driver_1", ""))
        top2 = pretty_label(row.get("top_driver_2", ""))

        folium.Polygon(
            locations=polygon_coords,
            color=color_hex,
            weight=0.5,
            fill=True,
            fill_color=color_hex,
            fill_opacity=0.7,
            tooltip=(
                f"Área: {row['area_fm']}<br>"
                f"P(crime T+1): {row['prob_crime']:.1%}<br>"
                f"Decil risco: {row.get('decil_risco', 'n/a')}/10<br>"
                f"Fator 1: {top1}<br>"
                f"Fator 2: {top2}"
            ),
        ).add_to(hex_layer)
    hex_layer.add_to(m)

    # Legenda
    legend_html = """
    <div style="position:fixed;bottom:40px;right:20px;z-index:1000;
                background:rgba(20,20,20,0.9);color:white;
                padding:12px 16px;border-radius:8px;border:1px solid #555;
                font-family:Arial,sans-serif;font-size:12px;">
      <b>Risco de roubo — T+1</b><br><br>
      <span style="background:linear-gradient(to right,#ffffb2,#fd8d3c,#bd0026);
        display:inline-block;width:100px;height:10px;border-radius:3px"></span><br>
      Menor &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Maior<br><br>
      Unidade: hexágono H3 res 9 (~0,1 km²)<br>
      Modelo: Logit L2 — apenas áreas FM<br>
      Contornos coloridos: áreas da Força Municipal
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(str(OUTPUT_DIR / "mapa_risco_t1.html"))
    print("Mapa salvo → output/mapa_risco_t1.html")
    m
'''
nb["cells"][cell_map["cell-22-risk-map"]]["source"] = risk_map_src.splitlines(keepends=True)
nb["cells"][cell_map["cell-22-risk-map"]]["outputs"] = []
nb["cells"][cell_map["cell-22-risk-map"]]["execution_count"] = None
print("[cell-22-risk-map] tooltip atualizado com pretty_label")


with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("\nDone. Re-rode cell-02-config para carregar o dicionário,")
print("depois cell-22-risk-map, cf987706 e 7ec058e2.")
