"""Patch: substitui o tile CartoDB (que nao esta carregando) por
TileLayer explicito do OpenStreetMap com control=False."""
import json
from pathlib import Path

NB = Path(r"c:/Users/pedro/Documents/2026/ClaudeImpactLab/code/logit_compstat.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))
cell = nb["cells"][30]
src = "".join(cell["source"])

old = '# Mapa base\nm = folium.Map(location=[-22.92, -43.28], zoom_start=12, tiles="CartoDB dark_matter")\n'
new = (
    '# Mapa base com TileLayer explicito (tiles="CartoDB dark_matter" estava\n'
    '# falhando em carregar - cinza no lugar do mapa).\n'
    'm = folium.Map(location=[-22.92, -43.28], zoom_start=12, tiles=None)\n'
    'folium.TileLayer(\n'
    '    tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",\n'
    '    attr=\'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors\',\n'
    '    name="OpenStreetMap",\n'
    '    control=False,  # sempre visivel; nao aparece no LayerControl\n'
    ').add_to(m)\n'
)
assert src.count(old) == 1, f"padrao nao encontrado / ambiguo: {src.count(old)}"
src2 = src.replace(old, new)
cell["source"] = src2.splitlines(keepends=True)
cell["outputs"] = []
cell["execution_count"] = None
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("patch aplicado")
