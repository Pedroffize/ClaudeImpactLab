"""Adiciona ao notebook logit_compstat.ipynb:
  1) Tabela top-N hexes por área FM com drivers (cf987706)
  2) Mapas HTML individuais por polígono FM (7ec058e2)
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.load(open(NB_PATH, encoding="utf-8"))
cell_map = {c["id"]: i for i, c in enumerate(nb["cells"])}

# ─────────────────────────────────────────────────────────────────────────────
# Cell cf987706 — Tabela top hexes por área FM
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

    # Seleciona colunas para exibição
    cols_show = [
        "area_fm", "rank_area", "hex_id", "prob_crime", "decil_risco",
        "top_driver_1", "contrib_top1",
        "top_driver_2", "contrib_top2",
        "top_driver_3", "contrib_top3",
    ]
    df_top_show = df_top[cols_show].copy()
    df_top_show["prob_crime"]   = (df_top_show["prob_crime"]   * 100).round(1)
    df_top_show["contrib_top1"] = (df_top_show["contrib_top1"] * 100).round(1)
    df_top_show["contrib_top2"] = (df_top_show["contrib_top2"] * 100).round(1)
    df_top_show["contrib_top3"] = (df_top_show["contrib_top3"] * 100).round(1)
    df_top_show = df_top_show.rename(columns={
        "prob_crime":   "P(crime)%",
        "contrib_top1": "contrib1_%",
        "contrib_top2": "contrib2_%",
        "contrib_top3": "contrib3_%",
    })

    print(f"Top {TOP_N_POR_AREA} hexes por área FM (horizonte T+1):")
    display(df_top_show.set_index(["area_fm", "rank_area"]))

    # Salva CSV e LaTeX
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

# ─────────────────────────────────────────────────────────────────────────────
# Cell 7ec058e2 — Mapas individuais por área FM
# ─────────────────────────────────────────────────────────────────────────────
maps_cell_src = '''# ── Mapas individuais por área FM (HTML) ─────────────────────────────────────
# Gera um HTML separado para cada área da Força Municipal com:
#   • Contorno do polígono da área (linha grossa)
#   • Hexágonos H3 coloridos por P(crime T+1)
#   • Marcadores destacando os top hexes com drivers no popup

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

    # Diretório de saída
    map_dir = OUTPUT_DIR / "mapas_por_area"
    map_dir.mkdir(exist_ok=True)

    print(f"Gerando mapas individuais em {map_dir}/...\\n")

    saved = []
    for area_name, poly in fm_polygons.items():
        df_area = df_pred1[df_pred1["area_fm"] == area_name].copy()
        if df_area.empty:
            print(f"  [skip] {area_name[:60]}: sem hexes preditos")
            continue

        # Centroide do polígono para centralizar o mapa
        cx, cy = poly.centroid.x, poly.centroid.y  # (lon, lat)

        m = folium.Map(location=[cy, cx], zoom_start=15, tiles="CartoDB dark_matter")

        # Escala local de cores (cada área tem sua própria normalização)
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

        # ─── Marcadores nos top hexes (com drivers no popup) ───
        top_layer = folium.FeatureGroup(name=f"Top {TOP_N_POR_AREA} hexes — drivers", show=True)
        df_area_top = df_area.nlargest(TOP_N_POR_AREA, "prob_crime")
        for rank, (_, row) in enumerate(df_area_top.iterrows(), start=1):
            lat_c, lon_c = h3.cell_to_latlng(row["hex_id"])
            popup_html = (
                f"<b>#{rank} — P(crime T+1): {row['prob_crime']:.1%}</b><br>"
                f"Decil: {int(row.get('decil_risco', 0))}/10<br><br>"
                f"<b>Drivers:</b><br>"
                f"1. {row['top_driver_1']} ({row['contrib_top1']:.1%})<br>"
                f"2. {row['top_driver_2']} ({row['contrib_top2']:.1%})<br>"
                f"3. {row['top_driver_3']} ({row['contrib_top3']:.1%})"
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
                popup=folium.Popup(popup_html, max_width=320),
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

        # Salva HTML
        slug = slugify(area_name)
        fname = f"mapa_risco_t1_{slug}.html"
        m.save(str(map_dir / fname))
        saved.append(fname)
        print(f"  OK {fname}")

    print(f"\\nTotal: {len(saved)} mapas salvos em output/mapas_por_area/")
else:
    print("pred_dfs[1] indisponível — execute a Fase 4 antes")
'''

# Apply: split into lines (preserving newlines) for Jupyter source format
def to_source_lines(s: str) -> list:
    lines = s.splitlines(keepends=True)
    # Last line may not have newline if s doesn't end with \n
    return lines

nb["cells"][cell_map["cf987706"]]["source"] = to_source_lines(table_cell_src)
nb["cells"][cell_map["cf987706"]]["outputs"] = []
nb["cells"][cell_map["cf987706"]]["execution_count"] = None

nb["cells"][cell_map["7ec058e2"]]["source"] = to_source_lines(maps_cell_src)
nb["cells"][cell_map["7ec058e2"]]["outputs"] = []
nb["cells"][cell_map["7ec058e2"]]["execution_count"] = None

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

# Verify
for cid in ["cf987706", "7ec058e2"]:
    src = "".join(nb["cells"][cell_map[cid]]["source"])
    print(f"{cid}: {len(src)} chars | chr() leftover = {'chr(' in src}")
print("Done.")
