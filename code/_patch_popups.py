"""One-shot patch: enrich FM polygon popups with top drivers (readable labels).

Edits cells 23, 27, 29 and 30 of logit_compstat.ipynb without touching their
outputs. Run once, then delete.
"""
import json
from pathlib import Path

NB = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.loads(NB.read_text(encoding="utf-8"))


def set_source(idx: int, text: str) -> None:
    nb["cells"][idx]["source"] = text.splitlines(keepends=True)


# ─────────────────────────────────────────────────────────────────────────────
# Cell 23 — adiciona helper area_top_drivers_summary no final
# ─────────────────────────────────────────────────────────────────────────────
CELL_23 = """\
# ── 4.1 Predição para o período T (mais recente disponível) ──────────────────
# Features construídas em T; prediz probabilidade em T+s para cada hex.

df_T = df_full[df_full['t'] == T_TEST].copy()

print(f'Hexes na semana T (período {df_T["ano_sem"].iloc[0] if len(df_T) > 0 else "?"}): {len(df_T)}')

# Calcula atribuição top-3 drivers por hex
def top_drivers(coef_vector, feat_names, x_row, n=3):
    \"\"\"Retorna os n features com maior |beta * x| (contribuição absoluta).\"\"\"
    contribs = np.abs(coef_vector * x_row)
    total = contribs.sum()
    idx = np.argsort(contribs)[::-1][:n]
    return [(feat_names[i], contribs[i] / total if total > 0 else 0) for i in idx]

pred_dfs = {}
for s, (clf, _, _, _) in models.items():
    X_T = df_T[ALL_FEATS].fillna(0)
    proba_s = clf.predict_proba(X_T)[:, 1]

    df_pred = df_T[['hex_id', 'area_fm', 'lat_centroide', 'lon_centroide', 'y_lag1']].copy()
    df_pred[f'prob_crime'] = proba_s

    # Decil de risco (dentro das áreas FM)
    df_pred['decil_risco'] = pd.qcut(proba_s, q=10, labels=False, duplicates='drop') + 1

    # Top-3 drivers por hex
    coef_vec = clf.coef_[0]
    driver_rows = []
    for x_arr in X_T.values:
        drivers = top_drivers(coef_vec, ALL_FEATS, x_arr, n=3)
        driver_rows.append({
            'top_driver_1': drivers[0][0] if len(drivers) > 0 else '',
            'contrib_top1': round(drivers[0][1], 4) if len(drivers) > 0 else 0,
            'top_driver_2': drivers[1][0] if len(drivers) > 1 else '',
            'contrib_top2': round(drivers[1][1], 4) if len(drivers) > 1 else 0,
            'top_driver_3': drivers[2][0] if len(drivers) > 2 else '',
            'contrib_top3': round(drivers[2][1], 4) if len(drivers) > 2 else 0,
        })
    df_drivers = pd.DataFrame(driver_rows)
    df_pred = pd.concat([df_pred.reset_index(drop=True), df_drivers], axis=1)

    # Adiciona todas as features (rastreabilidade)
    df_pred = pd.concat([df_pred, X_T.reset_index(drop=True)], axis=1)

    pred_dfs[s] = df_pred
    print(f's={s} | prob média: {proba_s.mean():.3f} | top decil (10): {(df_pred["decil_risco"] == 10).sum()} hexes')


# ── Agregação dos top drivers em nível de área FM ────────────────────────────
# Usada nos popups dos polígonos: combina os top_driver_{1,2,3} de cada hex
# da área, pondera pela P(crime) e devolve os N principais fatores em
# linguagem legível para policy maker.
def area_top_drivers_summary(df_area, n=5):
    \"\"\"Agrega top drivers dos hexes em uma área FM, ponderando por P(crime).

    Retorna lista [(label_legível, share_relativa), ...] em ordem decrescente.
    share_relativa = fração da explicação total atribuída àquela feature na área.
    \"\"\"
    if df_area is None or len(df_area) == 0:
        return []
    pieces = []
    for k in (1, 2, 3):
        d = df_area[[f"top_driver_{k}", f"contrib_top{k}", "prob_crime"]].copy()
        d.columns = ["feat", "contrib", "p"]
        d["score"] = d["contrib"].fillna(0) * d["p"].fillna(0)
        pieces.append(d)
    df_all = pd.concat(pieces, ignore_index=True)
    df_all = df_all[df_all["feat"].astype(str).str.len() > 0]
    if df_all.empty:
        return []
    agg = df_all.groupby("feat")["score"].sum().sort_values(ascending=False)
    total = agg.sum()
    if total <= 0:
        return []
    agg = agg / total
    return [(pretty_label(f), float(agg[f])) for f in agg.head(n).index]


def _drivers_html_block(df_area, title="Fatores que mais explicam o risco", n=5):
    \"\"\"Bloco HTML compacto com os top-n drivers de uma área FM.\"\"\"
    drivers = area_top_drivers_summary(df_area, n=n)
    if not drivers:
        items = "<li><i>sem hexes preditos nesta área</i></li>"
    else:
        items = "".join(
            f"<li>{lab} <span style='color:#888'>({sc:.0%})</span></li>"
            for lab, sc in drivers
        )
    return (
        f"<div style='margin-top:6px'>"
        f"<b style='font-size:11px'>{title}:</b>"
        f"<ol style='margin:4px 0 0 18px;padding:0;font-size:12px'>{items}</ol>"
        f"</div>"
    )
"""
set_source(23, CELL_23)


# ─────────────────────────────────────────────────────────────────────────────
# Cell 27 — popup do polígono FM em mapa_risco_t1.html agora inclui drivers
# ─────────────────────────────────────────────────────────────────────────────
CELL_27 = """\
# ── Mapa de risco — predições T+1 sobre hexágonos FM ─────────────────────────

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

        # Popup enriquecido: resumo de risco da área + top fatores em linguagem natural
        df_area_pop = df_plot[df_plot["area_fm"] == area_name]
        n_hex = len(df_area_pop)
        p_med = df_area_pop["prob_crime"].mean() if n_hex else 0.0
        p_max = df_area_pop["prob_crime"].max() if n_hex else 0.0
        popup_html = (
            f"<div style='font-family:Arial,sans-serif;font-size:12px;min-width:240px'>"
            f"<b style='font-size:13px'>{area_name}</b><br>"
            f"<span style='color:#555;font-size:11px'>"
            f"{n_hex} hexes · P média: {p_med:.1%} · P máx: {p_max:.1%}"
            f"</span>"
            f"<hr style='margin:6px 0;border:none;border-top:1px solid #ddd'>"
            f"{_drivers_html_block(df_area_pop)}"
            f"</div>"
        )

        folium.Polygon(
            locations=locations,
            color=color,
            weight=2.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.05,
            tooltip=f"Área FM: {area_name}",
            popup=folium.Popup(popup_html, max_width=360),
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
    legend_html = \"\"\"
    <div style="position:fixed;bottom:40px;right:20px;z-index:1000;
                background:rgba(20,20,20,0.92);color:white;
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
    \"\"\"
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(str(OUTPUT_DIR / "mapa_risco_t1.html"))
    print("Mapa salvo → output/mapa_risco_t1.html")
    m
"""
set_source(27, CELL_27)


# ─────────────────────────────────────────────────────────────────────────────
# Cell 29 — mapas por área FM: contorno do polígono agora tem popup com drivers
# ─────────────────────────────────────────────────────────────────────────────
CELL_29 = """\
# ── Mapas individuais por área FM (HTML) ─────────────────────────────────────
# Gera um HTML separado para cada área da Força Municipal com:
#   • Contorno do polígono da área (linha grossa) com popup dos fatores explicativos
#   • Hexágonos H3 coloridos por P(crime T+1)
#   • Marcadores destacando os top hexes com drivers em LINGUAGEM NATURAL

import re
import unicodedata
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def slugify(text: str) -> str:
    \"\"\"Converte nome da área em slug seguro para arquivo.\"\"\"
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

        # ─── Contorno do polígono da área com popup explicativo ───
        exterior = list(poly.exterior.coords)
        locations = [(lat, lon) for lon, lat in exterior]
        popup_html = (
            f"<div style='font-family:Arial,sans-serif;font-size:12px;min-width:240px'>"
            f"<b style='font-size:13px'>{area_name}</b><br>"
            f"<span style='color:#555;font-size:11px'>"
            f"{len(df_area)} hexes · P média: {df_area['prob_crime'].mean():.1%} · "
            f"P máx: {p_max:.1%}"
            f"</span>"
            f"<hr style='margin:6px 0;border:none;border-top:1px solid #ddd'>"
            f"{_drivers_html_block(df_area)}"
            f"</div>"
        )
        folium.Polygon(
            locations=locations,
            color="#4ecdc4",
            weight=3,
            fill=False,
            tooltip=f"Área FM: {area_name}",
            popup=folium.Popup(popup_html, max_width=360),
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
            f'background:rgba(20,20,20,0.92);color:white;padding:8px 14px;'
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
"""
set_source(29, CELL_29)


# ─────────────────────────────────────────────────────────────────────────────
# Cell 30 — mapa interativo: popup do polígono FM agora inclui drivers
# ─────────────────────────────────────────────────────────────────────────────
CELL_30 = """\
# -- Mapa interativo: camada por horizonte + poligonos FM (LayerControl nativo) --
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

# Mapa base com TileLayer explicito (tiles="CartoDB dark_matter" estava
# falhando em carregar - cinza no lugar do mapa).
m = folium.Map(location=[-22.92, -43.28], zoom_start=12, tiles=None)
folium.TileLayer(
    tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    name="OpenStreetMap",
    control=False,  # sempre visivel; nao aparece no LayerControl
).add_to(m)

# Uma FeatureGroup por horizonte; so a de s=1 fica visivel por padrao
for s in HORIZONS:
    if s not in pred_dfs:
        continue
    fg = folium.FeatureGroup(
        name=f"Hexes - horizonte T+{s}",
        show=(s == 1),
        overlay=True,  # overlay (checkbox); base layer escondia o tile
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
# Usa o horizonte s=1 (mais imediato) para o popup agregado dos poligonos
df_pop_base = pred_dfs[1] if 1 in pred_dfs else next(iter(pred_dfs.values()))
fg_polys = folium.FeatureGroup(name="Poligonos FM", show=True, overlay=True)
for i, (area_name, poly) in enumerate(fm_polygons.items()):
    color = palette[i % len(palette)]
    locations = [(lat, lon) for lon, lat in poly.exterior.coords]

    df_area_pop = df_pop_base[df_pop_base["area_fm"] == area_name]
    n_hex = len(df_area_pop)
    p_med = df_area_pop["prob_crime"].mean() if n_hex else 0.0
    p_max = df_area_pop["prob_crime"].max() if n_hex else 0.0
    popup_html = (
        f"<div style='font-family:Arial,sans-serif;font-size:12px;min-width:240px'>"
        f"<b style='font-size:13px'>{area_name}</b><br>"
        f"<span style='color:#555;font-size:11px'>"
        f"{n_hex} hexes - P media (T+1): {p_med:.1%} - P max: {p_max:.1%}"
        f"</span>"
        f"<hr style='margin:6px 0;border:none;border-top:1px solid #ddd'>"
        f"{_drivers_html_block(df_area_pop, title='Fatores que mais explicam o risco (T+1)')}"
        f"</div>"
    )

    folium.Polygon(
        locations=locations,
        color=color, weight=2.5,
        fill=True, fill_color=color, fill_opacity=0.04,
        tooltip=f"Area FM: {area_name}",
        popup=folium.Popup(popup_html, max_width=360),
    ).add_to(fg_polys)
fg_polys.add_to(m)

# Controle nativo do folium (canto superior direito, expandido)
folium.LayerControl(collapsed=False).add_to(m)

# Titulo e legenda compactos
title_html = \"\"\"
<div style="position:absolute;top:10px;left:60px;z-index:1000;
            background:rgba(20,20,20,0.92);color:white;
            padding:8px 14px;border-radius:6px;border:1px solid #555;
            font-family:Arial,sans-serif;font-size:13px;
            box-shadow:0 2px 6px rgba(0,0,0,0.5);">
  <b>CompStat-Rio - Mapa de Risco</b>
</div>
\"\"\"
legend_html = \"\"\"
<div style="position:absolute;bottom:30px;left:10px;z-index:1000;
            background:rgba(20,20,20,0.92);color:white;
            padding:10px 14px;border-radius:6px;border:1px solid #555;
            font-family:Arial,sans-serif;font-size:11px;
            box-shadow:0 2px 6px rgba(0,0,0,0.5);">
  <b>Risco de roubo - Logit L2</b><br>
  <span style="background:linear-gradient(to right,#ffffb2,#fd8d3c,#bd0026);
    display:inline-block;width:120px;height:10px;border-radius:3px;"></span><br>
  Menor &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Maior
</div>
\"\"\"
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
"""
set_source(30, CELL_30)


# Save back, preserving formatting
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print("Patched cells 23, 27, 29, 30.")

# Quick validation: notebook still parses and target cells contain the new helper
nb2 = json.loads(NB.read_text(encoding="utf-8"))
assert "area_top_drivers_summary" in "".join(nb2["cells"][23]["source"])
assert "_drivers_html_block(df_area_pop)" in "".join(nb2["cells"][27]["source"])
assert "_drivers_html_block(df_area)" in "".join(nb2["cells"][29]["source"])
assert "_drivers_html_block(df_area_pop" in "".join(nb2["cells"][30]["source"])
print("Validation OK.")
