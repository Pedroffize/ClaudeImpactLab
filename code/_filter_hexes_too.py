"""Reestrutura cell-23-interactive-map:
   - Hex pertence a TODAS as áreas FM cujo polígono buffered o contém
   - Filtro de área controla tanto polígono quanto hexes internos
   - Controle customizado HTML+JS (substitui GroupedLayerControl)
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.load(open(NB_PATH, encoding="utf-8"))
cell_map = {c["id"]: i for i, c in enumerate(nb["cells"])}

cell_src = '''# ── Mapa interativo final: filtro de horizonte (s) + filtro de polígonos ─────
# UX:
#   • Radio (escolha 1): horizonte s ∈ {1, 2, 4}
#   • Checkboxes: quais áreas FM exibir (polígono + hexes internos)
#   • Hex que cai dentro de 2 polígonos FM aparece se PELO MENOS UM dos
#     polígonos pais estiver marcado.

import re
import unicodedata
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from shapely.geometry import Point

def slugify(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_str = nfkd.encode("ASCII", "ignore").decode("ASCII")
    return re.sub(r"[^a-zA-Z0-9]+", "_", ascii_str).strip("_").lower()[:60]

cmap = plt.cm.YlOrRd

# ── 1. Mapeia hex → conjunto de áreas FM que o contêm (poligonos com buffer) ─
# Um hex pode pertencer a MAIS DE UMA área se cair na sobreposição dos buffers.
hex_areas_map = {}  # {hex_id: [area_name, ...]}
for _, hr in df_fm.iterrows():
    pt = Point(hr["lon_centroide"], hr["lat_centroide"])
    matching = [name for name, poly in fm_polygons.items() if poly.contains(pt)]
    if not matching:
        matching = [hr["area_fm"]]  # fallback (não deve ocorrer)
    hex_areas_map[hr["hex_id"]] = matching

multi = sum(1 for v in hex_areas_map.values() if len(v) > 1)
print(f"Hexes mapeados: {len(hex_areas_map):,} | em múltiplas áreas: {multi}")

# ── 2. Escala global de cores (compartilhada entre os 3 horizontes) ──────────
all_probs = []
for s in HORIZONS:
    if s in pred_dfs:
        all_probs.extend(pred_dfs[s]["prob_crime"].tolist())
P_MIN = min(all_probs)
P_MAX = max(all_probs)

# ── 3. Cria mapa base (sem LayerControl — usaremos controle customizado) ─────
m = folium.Map(location=[-22.92, -43.28], zoom_start=12, tiles="CartoDB positron")

# ── 4. Camadas: uma FeatureGroup por (s, area_fm) ────────────────────────────
# Cada hex é replicado em todas as áreas a que pertence
hex_layers = {s: {} for s in HORIZONS}  # {s: {area_name: feature_group}}
area_order = list(fm_polygons.keys())

for s in HORIZONS:
    if s not in pred_dfs:
        continue
    df_s = pred_dfs[s].set_index("hex_id")

    for area_name in area_order:
        fg = folium.FeatureGroup(
            name=f"hex_s{s}_{slugify(area_name)}",
            show=False,        # ligado dinamicamente pelo JS
            overlay=True,
        )

        # Filtra hexes que pertencem a essa área (membership pode ser múltipla)
        hexes_da_area = [h for h, areas in hex_areas_map.items() if area_name in areas]
        for hex_id in hexes_da_area:
            if hex_id not in df_s.index:
                continue
            row = df_s.loc[hex_id]
            boundary = h3.cell_to_boundary(hex_id)
            poly_coords = [(lat, lon) for lat, lon in boundary]
            norm = (row["prob_crime"] - P_MIN) / (P_MAX - P_MIN + 1e-9)
            color_hex = mcolors.to_hex(cmap(norm))

            d1 = pretty_label(row.get("top_driver_1", ""))
            d2 = pretty_label(row.get("top_driver_2", ""))
            d3 = pretty_label(row.get("top_driver_3", ""))

            tooltip_html = (
                f"<b>Área:</b> {area_name}<br>"
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
        hex_layers[s][area_name] = fg

# ── 5. Camadas de polígonos por área FM ──────────────────────────────────────
palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]
poly_layers = {}
for i, (area_name, poly) in enumerate(fm_polygons.items()):
    color = palette[i % len(palette)]
    fg_poly = folium.FeatureGroup(
        name=f"poly_{slugify(area_name)}",
        show=False,         # JS controla
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
    ).add_to(fg_poly)
    fg_poly.add_to(m)
    poly_layers[area_name] = fg_poly

# ── 6. Controle customizado: HTML (radio + checkboxes) ───────────────────────
area_checkboxes = "\\n".join(
    f'  <label style="display:block;"><input type="checkbox" class="area-cb" '
    f'data-slug="{slugify(a)}" checked> {a}</label>'
    for a in area_order
)
control_html = f"""
<div id="ctl" style="position:fixed;top:80px;right:10px;z-index:1000;
     background:rgba(255,255,255,0.97);color:#222;padding:14px 18px;
     border-radius:8px;border:1px solid #bbb;font-family:Arial,sans-serif;
     font-size:12px;max-width:320px;max-height:75vh;overflow-y:auto;
     box-shadow:0 2px 8px rgba(0,0,0,0.15);">
  <b>Horizonte (escolha 1)</b><br>
  <label style="display:block;"><input type="radio" name="horizon" value="1" checked> 1 semana à frente</label>
  <label style="display:block;"><input type="radio" name="horizon" value="2"> 2 semanas à frente</label>
  <label style="display:block;"><input type="radio" name="horizon" value="4"> 4 semanas à frente</label>
  <br>
  <b>Áreas FM (filtre)</b><br>
  <button id="btn-all" style="margin:4px 4px 8px 0;font-size:11px;">Todas</button>
  <button id="btn-none" style="margin:4px 0 8px 0;font-size:11px;">Nenhuma</button><br>
{area_checkboxes}
</div>
"""

# ── 7. JS: bind layers and react to user input ───────────────────────────────
# Constrói o mapping JS {s: {slug: feature_group_var}}
def js_obj_layers(layer_dict):
    parts = []
    for s, area_d in layer_dict.items():
        inner = ",".join(f'"{slugify(a)}": {fg.get_name()}' for a, fg in area_d.items())
        parts.append(f"{s}: {{{inner}}}")
    return "{" + ",".join(parts) + "}"

def js_obj_polys(poly_dict):
    inner = ",".join(f'"{slugify(a)}": {fg.get_name()}' for a, fg in poly_dict.items())
    return "{" + inner + "}"

js_code = f"""
(function() {{
  var hexLayers  = {js_obj_layers(hex_layers)};
  var polyLayers = {js_obj_polys(poly_layers)};
  var mapRef     = {m.get_name()};

  function refresh() {{
    var s = parseInt(document.querySelector('input[name="horizon"]:checked').value);
    var selected = Array.from(document.querySelectorAll('input.area-cb:checked'))
                        .map(function(c) {{ return c.dataset.slug; }});

    // Esconde tudo
    Object.keys(hexLayers).forEach(function(h) {{
      Object.keys(hexLayers[h]).forEach(function(a) {{
        if (mapRef.hasLayer(hexLayers[h][a])) mapRef.removeLayer(hexLayers[h][a]);
      }});
    }});
    Object.keys(polyLayers).forEach(function(a) {{
      if (mapRef.hasLayer(polyLayers[a])) mapRef.removeLayer(polyLayers[a]);
    }});

    // Mostra apenas (s atual) ∩ (áreas marcadas)
    selected.forEach(function(a) {{
      if (hexLayers[s] && hexLayers[s][a]) mapRef.addLayer(hexLayers[s][a]);
      if (polyLayers[a])                   mapRef.addLayer(polyLayers[a]);
    }});
  }}

  document.querySelectorAll('input[name="horizon"]')
          .forEach(function(r) {{ r.addEventListener('change', refresh); }});
  document.querySelectorAll('input.area-cb')
          .forEach(function(c) {{ c.addEventListener('change', refresh); }});

  document.getElementById('btn-all').addEventListener('click', function() {{
    document.querySelectorAll('input.area-cb').forEach(function(c) {{ c.checked = true; }});
    refresh();
  }});
  document.getElementById('btn-none').addEventListener('click', function() {{
    document.querySelectorAll('input.area-cb').forEach(function(c) {{ c.checked = false; }});
    refresh();
  }});

  // Estado inicial
  refresh();
}})();
"""

# Título + legenda
title_html = """
<div style="position:fixed;top:10px;left:60px;z-index:1000;
            background:rgba(255,255,255,0.97);color:#222;
            padding:10px 18px;border-radius:8px;border:1px solid #bbb;
            font-family:Arial,sans-serif;font-size:14px;
            box-shadow:0 2px 8px rgba(0,0,0,0.15);">
  <b>CompStat-Rio — Mapa Interativo de Risco</b><br>
  <span style="font-size:11px;color:#666;">
    Hexes pertencem a todas as áreas que os contêm; filtre à direita
  </span>
</div>
"""

legend_html = """
<div style="position:fixed;bottom:30px;right:20px;z-index:1000;
            background:rgba(255,255,255,0.97);color:#222;
            padding:14px 18px;border-radius:8px;border:1px solid #bbb;
            font-family:Arial,sans-serif;font-size:12px;max-width:280px;
            box-shadow:0 2px 8px rgba(0,0,0,0.15);">
  <b>Risco de roubo — Logit L2</b><br><br>
  <span style="background:linear-gradient(to right,#ffffb2,#fd8d3c,#bd0026);
    display:inline-block;width:120px;height:10px;border-radius:3px;"></span><br>
  Menor &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Maior<br>
  <i style="color:#666;">Escala compartilhada entre horizontes</i>
</div>
"""

m.get_root().html.add_child(folium.Element(title_html))
m.get_root().html.add_child(folium.Element(legend_html))
m.get_root().html.add_child(folium.Element(control_html))
m.get_root().script.add_child(folium.Element(js_code))

out_path = OUTPUT_DIR / "mapa_interativo.html"
m.save(str(out_path))
print(f"Mapa interativo salvo → {out_path}")
print(f"  • Horizontes: {list(hex_layers.keys())}")
print(f"  • Áreas filtráveis: {len(poly_layers)}")
print(f"  • Hexes em múltiplas áreas: {multi}")
m
'''

nb["cells"][cell_map["cell-23-interactive-map"]]["source"] = cell_src.splitlines(keepends=True)
nb["cells"][cell_map["cell-23-interactive-map"]]["outputs"] = []
nb["cells"][cell_map["cell-23-interactive-map"]]["execution_count"] = None

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("cell-23-interactive-map reescrito com filtro conjunto de hex+polígono.")
