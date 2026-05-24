"""Reverte tema dos 3 mapas para escuro (CartoDB dark_matter), mantendo
   toda a lógica de filtros e dicionário de rótulos previamente adicionada.
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.load(open(NB_PATH, encoding="utf-8"))

TARGETS = ["cell-22-risk-map", "7ec058e2", "cell-23-interactive-map"]

# Reverte tile + esquema visual das caixas (control, título, legenda)
REPLACEMENTS = [
    # Tile base
    ('tiles="CartoDB positron"',     'tiles="CartoDB dark_matter"'),
    ("tiles='CartoDB positron'",     "tiles='CartoDB dark_matter'"),

    # Fundo claro -> escuro
    ("background:rgba(255,255,255,0.97)", "background:rgba(20,20,20,0.92)"),
    ("background:rgba(255,255,255,0.95)", "background:rgba(20,20,20,0.92)"),

    # Texto escuro -> branco
    ("color:#222",  "color:white"),

    # Bordas claras -> escuras
    ("border:1px solid #bbb", "border:1px solid #555"),

    # Cor das legendas/subtítulos cinza médio -> cinza claro
    ("color:#666",  "color:#aaa"),
    ('color:"#666"', 'color:"#aaa"'),

    # Sombra mais sutil no escuro
    ("box-shadow:0 2px 8px rgba(0,0,0,0.15)", "box-shadow:0 2px 8px rgba(0,0,0,0.5)"),

    # Contorno do polígono: azul (#1f6feb) -> turquesa (#4ecdc4) que era o original do escuro
    ('color="#1f6feb"', 'color="#4ecdc4"'),
    ("color='#1f6feb'", "color='#4ecdc4'"),
]

changed = []
for cid in TARGETS:
    idx = next((i for i, c in enumerate(nb["cells"]) if c.get("id") == cid), None)
    if idx is None:
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
        print(f"[ok] {cid} revertido para tema escuro")

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"\n{len(changed)} mapas revertidos. Re-rode as células para regerar os HTMLs.")
