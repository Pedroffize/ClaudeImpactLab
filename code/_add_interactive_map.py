"""Adiciona uma célula final ao notebook com mapa interativo:
   - Filtro de horizonte (s=1, 2, 4) via radio button
   - Filtro de polígonos das áreas FM via checkboxes
   - Tudo num único HTML salvo em output/mapa_interativo.html
"""
import json
import uuid
from pathlib import Path

NB_PATH = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.load(open(NB_PATH, encoding="utf-8"))

cell_src = '''# ── Mapa interativo final: filtro de horizonte (s) + filtro de polígonos ─────
# Permite ao policy maker:
#   • Escolher horizonte s ∈ {1, 2, 4} via radio button (exclusivo)
#   • Filtrar quais áreas FM exibir via checkboxes (múltipla seleção)
#
# Implementação: folium.plugins.GroupedLayerControl agrupa as camadas e marca
# "Horizonte" como grupo exclusivo (radio) e "Áreas FM" como múltipla escolha.

from folium.plugins import GroupedLayerControl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

cmap = plt.cm.YlOrRd

# ── Escala global de cores (compartilhada entre os 3 horizontes) ─────────────
# Permite comparar visualmente "o risco é menor em T+4 vs T+1?"
all_probs = []
for s in HORIZONS:
    if s in pred_dfs:
        all_probs.extend(pred_dfs[s]["prob_crime"].tolist())
P_MIN = min(all_probs)
P_MAX = max(all_probs)

# Mapa centralizado na FM
m = folium.Map(location=[-22.92, -43.28], zoom_start=12, tiles="CartoDB dark_matter")

# ── Camadas de horizonte: uma FeatureGroup por s ─────────────────────────────
horizon_layers = {}
for s in HORIZONS:
    if s not in pred_dfs:
        continue
    df_s = pred_dfs[s]
    fg = folium.FeatureGroup(
        name=f"Horizonte s = {s} semana{'s' if s > 1 else ''}",
        show=(s == 1),  # s=1 default
        overlay=True,
    )

    for _, row in df_s.iterrows():
        boundary = h3.cell_to_boundary(row["hex_id"])
        poly_coords = [(lat, lon) for lat, lon in boundary]
        norm = (row["prob_crime"] - P_MIN) / (P_MAX - P_MIN + 1e-9)
        color_hex = mcolors.to_hex(cmap(norm))

        d1 = pretty_label(row.get("top_driver_1", ""))
        d2 = pretty_label(row.get("top_driver_2", ""))
        d3 = pretty_label(row.get("top_driver_3", ""))

        tooltip_html = (
            f"<b>Área:</b> {row['area_fm']}<br>"
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
            color=color_hex,
            weight=0.5,
            fill=True,
            fill_color=color_hex,
            fill_opacity=0.7,
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
        ).add_to(fg)

    fg.add_to(m)
    horizon_layers[s] = fg

# ── Camadas de polígonos por área FM (filtro por checkbox) ───────────────────
palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]
area_layers = {}
for i, (area_name, poly) in enumerate(fm_polygons.items()):
    color = palette[i % len(palette)]
    fg_area = folium.FeatureGroup(
        name=area_name,
        show=True,
        overlay=True,
    )
    exterior = list(poly.exterior.coords)
    locations = [(lat, lon) for lon, lat in exterior]
    folium.Polygon(
        locations=locations,
        color=color,
        weight=2.5,
        fill=True,
        fill_color=color,
        fill_opacity=0.04,
        tooltip=f"Área FM: {area_name}",
        popup=folium.Popup(f"<b>{area_name}</b>", max_width=300),
    ).add_to(fg_area)
    fg_area.add_to(m)
    area_layers[area_name] = fg_area

# ── GroupedLayerControl: horizonte exclusivo (radio), áreas múltipla (checkbox) ─
GroupedLayerControl(
    groups={
        "Horizonte (escolha 1)": list(horizon_layers.values()),
        "Áreas FM (filtre quais mostrar)": list(area_layers.values()),
    },
    exclusive_groups=["Horizonte (escolha 1)"],
    collapsed=False,
).add_to(m)

# ── Legenda e título ─────────────────────────────────────────────────────────
legend_html = """
<div style="position:fixed;bottom:40px;right:20px;z-index:1000;
            background:rgba(20,20,20,0.92);color:white;
            padding:14px 18px;border-radius:8px;border:1px solid #555;
            font-family:Arial,sans-serif;font-size:12px;max-width:280px;">
  <b>Risco de roubo — Logit L2</b><br><br>
  <span style="background:linear-gradient(to right,#ffffb2,#fd8d3c,#bd0026);
    display:inline-block;width:120px;height:10px;border-radius:3px"></span><br>
  Menor &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Maior<br><br>
  <b>Como usar:</b><br>
  • Escolha <b>Horizonte</b> (s = 1, 2 ou 4 semanas)<br>
  • Marque/desmarque <b>Áreas FM</b> para focar<br>
  • Passe o mouse sobre o hexágono para ver drivers<br><br>
  <i>Escala compartilhada entre horizontes</i>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

title_html = """
<div style="position:fixed;top:10px;left:60px;z-index:1000;
            background:rgba(20,20,20,0.92);color:white;
            padding:10px 18px;border-radius:8px;border:1px solid #555;
            font-family:Arial,sans-serif;font-size:14px;">
  <b>CompStat-Rio — Mapa Interativo de Risco</b><br>
  <span style="font-size:11px;color:#aaa;">
    Filtre o horizonte e as áreas usando o painel à direita
  </span>
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))

# Salva
out_path = OUTPUT_DIR / "mapa_interativo.html"
m.save(str(out_path))
print(f"Mapa interativo salvo → {out_path}")
print(f"  • Horizontes disponíveis: {list(horizon_layers.keys())}")
print(f"  • Áreas FM filtráveis: {len(area_layers)}")
m
'''

# Verifica se já existe um cell para o mapa interativo
existing_ids = [c["id"] for c in nb["cells"]]
target_id = "cell-23-interactive-map"

if target_id in existing_ids:
    idx = existing_ids.index(target_id)
    nb["cells"][idx]["source"] = cell_src.splitlines(keepends=True)
    nb["cells"][idx]["outputs"] = []
    nb["cells"][idx]["execution_count"] = None
    print(f"[{target_id}] célula existente atualizada")
else:
    new_cell = {
        "cell_type": "code",
        "execution_count": None,
        "id": target_id,
        "metadata": {},
        "outputs": [],
        "source": cell_src.splitlines(keepends=True),
    }
    nb["cells"].append(new_cell)
    print(f"[{target_id}] célula nova adicionada ao final")

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"Total de células: {len(nb['cells'])}")
