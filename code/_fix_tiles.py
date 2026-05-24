"""Substitui o atalho 'CartoDB dark_matter' por TileLayer explícito com URL
   completa do CartoDB DarkMatter, que carrega de forma confiável.
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.load(open(NB_PATH, encoding="utf-8"))

TARGETS = ["cell-22-risk-map", "7ec058e2", "cell-23-interactive-map"]

# Snippet que adiciona o tile explícito logo após criar o folium.Map(...)
TILE_LAYER_SNIPPET = (
    'folium.TileLayer(\n'
    '    tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",\n'
    '    attr="© OpenStreetMap contributors © CARTO",\n'
    '    name="CartoDB Dark Matter",\n'
    '    subdomains="abcd",\n'
    '    max_zoom=20,\n'
    ').add_to(m)\n'
)

# Variações dos padrões existentes onde o Map é criado com tiles="CartoDB dark_matter"
MAP_CREATE_PATTERNS = [
    # interactive-map: folium.Map(location=[-22.92, -43.28], zoom_start=12, tiles="CartoDB dark_matter")
    (
        'm = folium.Map(location=[-22.92, -43.28], zoom_start=12, tiles="CartoDB dark_matter")\n',
        'm = folium.Map(location=[-22.92, -43.28], zoom_start=12, tiles=None, control_scale=True)\n'
        + TILE_LAYER_SNIPPET,
    ),
    # risk-map cell-22: same pattern, zoom=13
    (
        'm = folium.Map(location=[-22.92, -43.28], zoom_start=13, tiles="CartoDB dark_matter")\n',
        'm = folium.Map(location=[-22.92, -43.28], zoom_start=13, tiles=None, control_scale=True)\n'
        + TILE_LAYER_SNIPPET,
    ),
    # per-area maps: folium.Map(location=[cy, cx], zoom_start=15, tiles="CartoDB dark_matter")
    (
        'm = folium.Map(location=[cy, cx], zoom_start=15, tiles="CartoDB dark_matter")\n',
        'm = folium.Map(location=[cy, cx], zoom_start=15, tiles=None, control_scale=True)\n'
        + TILE_LAYER_SNIPPET,
    ),
]

changed = []
for cid in TARGETS:
    idx = next((i for i, c in enumerate(nb["cells"]) if c.get("id") == cid), None)
    if idx is None:
        continue

    src_list = nb["cells"][idx]["source"]
    src_str = "".join(src_list) if isinstance(src_list, list) else src_list

    before = src_str
    for old, new in MAP_CREATE_PATTERNS:
        if old in src_str:
            src_str = src_str.replace(old, new)

    if src_str != before:
        nb["cells"][idx]["source"] = src_str.splitlines(keepends=True)
        nb["cells"][idx]["outputs"] = []
        nb["cells"][idx]["execution_count"] = None
        changed.append(cid)
        print(f"[ok] {cid}: TileLayer explícito injetado")
    else:
        print(f"[noop] {cid}: padrão não encontrado")

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"\n{len(changed)} mapas atualizados. Re-rode para regerar os HTMLs.")
