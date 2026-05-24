"""Troca todos os mapas folium do notebook de tema escuro para tema claro.
   - tiles: 'CartoDB dark_matter' -> 'CartoDB positron'
   - legendas/títulos: fundo escuro -> fundo branco com texto escuro
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.load(open(NB_PATH, encoding="utf-8"))

TARGETS = ["cell-22-risk-map", "7ec058e2", "cell-23-interactive-map"]

# Substituições string-a-string (aplicadas em ordem)
REPLACEMENTS = [
    # Tile base
    ('tiles="CartoDB dark_matter"',   'tiles="CartoDB positron"'),
    ("tiles='CartoDB dark_matter'",   "tiles='CartoDB positron'"),

    # Fundo escuro das legendas/títulos -> fundo branco com texto escuro
    ("background:rgba(20,20,20,0.9)",  "background:rgba(255,255,255,0.95)"),
    ("background:rgba(20,20,20,0.92)", "background:rgba(255,255,255,0.95)"),
    ("color:white",                    "color:#222"),
    ("border:1px solid #555",          "border:1px solid #bbb"),
    ('color:"#aaa"',                   'color:"#666"'),
    ("color:#aaa",                     "color:#666"),

    # Contorno do polígono FM (turquesa fica sumido no claro)
    ('color="#4ecdc4"',                'color="#1f6feb"'),
    ("color='#4ecdc4'",                "color='#1f6feb'"),
]

changed = []
for cid in TARGETS:
    idx = next((i for i, c in enumerate(nb["cells"]) if c.get("id") == cid), None)
    if idx is None:
        print(f"[skip] {cid} não encontrado")
        continue

    src_list = nb["cells"][idx]["source"]
    src_str = "".join(src_list) if isinstance(src_list, list) else src_list

    before = src_str
    for old, new in REPLACEMENTS:
        src_str = src_str.replace(old, new)

    if src_str != before:
        nb["cells"][idx]["source"] = src_str.splitlines(keepends=True)
        nb["cells"][idx]["outputs"] = []
        nb["cells"][idx]["execution_count"] = None
        changed.append(cid)
        print(f"[ok] {cid} atualizado")
    else:
        print(f"[noop] {cid} sem mudanças")

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"\n{len(changed)} células atualizadas. Re-rode os mapas para regerar os HTMLs.")
