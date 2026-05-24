"""One-shot patch: replace cell 30 of logit_compstat.ipynb with a simpler
map version (no custom filter panel, native LayerControl, inline-safe height).
"""
import json
from pathlib import Path

NB_PATH = Path(r"c:/Users/pedro/Documents/2026/ClaudeImpactLab/code/logit_compstat.ipynb")

NEW_SOURCE = '''# -- Mapa interativo: camada por horizonte + poligonos FM (LayerControl nativo) --
# Versao simplificada: sem painel customizado de filtros (que estava cobrindo
# o mapa no display inline do Jupyter). Use o controle nativo do folium no
# canto superior direito para alternar horizontes e ligar/desligar poligonos.

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from shapely.geometry import Point
from folium import Figure

cmap = plt.cm.YlOrRd

# Mapeia hex -> areas FM que o contem (apenas para enriquecer o tooltip)
hex_areas_map = {}
for _, hr in df_fm.iterrows():
    pt = Point(hr["lon_centroide"], hr["lat_centroide"])
    matching = [name for name, poly in fm_polygons.items() if poly.contains(pt)]
    if not matching:
        matching = [hr["area_fm"]]
    hex_areas_map[hr["hex_id"]] = matching

# Escala global de cores (compartilhada entre os horizontes)
all_probs = []
for s in HORIZONS:
    if s in pred_dfs:
        all_probs.extend(pred_dfs[s]["prob_crime"].tolist())
P_MIN, P_MAX = min(all_probs), max(all_probs)

# Mapa base
m = folium.Map(location=[-22.92, -43.28], zoom_start=12, tiles="CartoDB dark_matter")

# Uma FeatureGroup por horizonte; so a de s=1 fica visivel por padrao
for s in HORIZONS:
    if s not in pred_dfs:
        continue
    fg = folium.FeatureGroup(
        name=f"Hexes - horizonte T+{s}",
        show=(s == 1),
        overlay=False,  # comporta-se como base layer mutuamente exclusiva
    )
    df_s = pred_dfs[s].set_index("hex_id")
    for hex_id, row in df_s.iterrows():
        boundary = h3.cell_to_boundary(hex_id)
        poly_coords = [(lat, lon) for lat, lon in boundary]
        norm = (row["prob_crime"] - P_MIN) / (P_MAX - P_MIN + 1e-9)
        color_hex = mcolors.to_hex(cmap(norm))
        areas_str = ", ".join(hex_areas_map.get(hex_id, ["?"]))
        d1 = pretty_label(row.get("top_driver_1", ""))
        d2 = pretty_label(row.get("top_driver_2", ""))
        d3 = pretty_label(row.get("top_driver_3", ""))
        tooltip_html = (
            f"<b>Area(s):</b> {areas_str}<br>"
            f"<b>Horizonte T+{s}</b><br>"
            f"<b>P(crime):</b> {row['prob_crime']:.1%}<br>"
            f"<b>Decil:</b> {int(row.get('decil_risco', 0))}/10<br><br>"
            f"<b>Fatores que mais explicam:</b><br>"
            f"1. {d1} ({row['contrib_top1']:.1%})<br>"
            f"2. {d2} ({row['contrib_top2']:.1%})<br>"
            f"3. {d3} ({row['contrib_top3']:.1%})"
        )
        folium.Polygon(
            locations=poly_coords,
            color=color_hex, weight=0.5,
            fill=True, fill_color=color_hex, fill_opacity=0.7,
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
        ).add_to(fg)
    fg.add_to(m)

# Camada unica com todos os poligonos FM (visivel por padrao)
palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]
fg_polys = folium.FeatureGroup(name="Poligonos FM", show=True, overlay=True)
for i, (area_name, poly) in enumerate(fm_polygons.items()):
    color = palette[i % len(palette)]
    locations = [(lat, lon) for lon, lat in poly.exterior.coords]
    folium.Polygon(
        locations=locations,
        color=color, weight=2.5,
        fill=True, fill_color=color, fill_opacity=0.04,
        tooltip=f"Area FM: {area_name}",
        popup=folium.Popup(f"<b>{area_name}</b>", max_width=300),
    ).add_to(fg_polys)
fg_polys.add_to(m)

# Controle nativo do folium (canto superior direito, expandido)
folium.LayerControl(collapsed=False).add_to(m)

# Titulo e legenda compactos
title_html = """
<div style=\"position:absolute;top:10px;left:60px;z-index:1000;
            background:rgba(20,20,20,0.92);color:white;
            padding:8px 14px;border-radius:6px;border:1px solid #555;
            font-family:Arial,sans-serif;font-size:13px;
            box-shadow:0 2px 6px rgba(0,0,0,0.5);\">
  <b>CompStat-Rio - Mapa de Risco</b>
</div>
"""
legend_html = """
<div style=\"position:absolute;bottom:30px;left:10px;z-index:1000;
            background:rgba(20,20,20,0.92);color:white;
            padding:10px 14px;border-radius:6px;border:1px solid #555;
            font-family:Arial,sans-serif;font-size:11px;
            box-shadow:0 2px 6px rgba(0,0,0,0.5);\">
  <b>Risco de roubo - Logit L2</b><br>
  <span style=\"background:linear-gradient(to right,#ffffb2,#fd8d3c,#bd0026);
    display:inline-block;width:120px;height:10px;border-radius:3px;\"></span><br>
  Menor &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Maior
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))
m.get_root().html.add_child(folium.Element(legend_html))

out_path = OUTPUT_DIR / "mapa_interativo.html"
m.save(str(out_path))
print(f"Mapa interativo salvo -> {out_path}")
print(f"  - Horizontes: {[s for s in HORIZONS if s in pred_dfs]}")
print(f"  - Areas FM (poligonos): {len(fm_polygons)}")

# Display inline com altura maior para o iframe nao espremer o mapa
fig = Figure(width="100%", height=700)
fig.add_child(m)
fig
'''

nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
cell = nb["cells"][30]
assert cell["cell_type"] == "code", f"cell 30 nao e codigo: {cell['cell_type']}"
# split into list-of-lines (preserving trailing newlines except on last line)
lines = NEW_SOURCE.splitlines(keepends=True)
cell["source"] = lines
cell["outputs"] = []
cell["execution_count"] = None
NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("cell 30 substituida com sucesso")
print(f"linhas novas: {len(lines)}")
