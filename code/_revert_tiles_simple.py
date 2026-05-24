"""Reverte os 3 mapas para o shortcut original tiles='CartoDB dark_matter'
   que estava funcionando. Remove o bloco folium.TileLayer(...) explícito
   que foi adicionado posteriormente.
"""
import json
import re
from pathlib import Path

NB_PATH = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.load(open(NB_PATH, encoding="utf-8"))

TARGETS = ["cell-22-risk-map", "7ec058e2", "cell-23-interactive-map"]

# Padrão 1: o Map() com tiles=None + bloco TileLayer separado
# Captura qualquer indentação (\s*) antes do folium.TileLayer
TILE_BLOCK_RE = re.compile(
    r"\n(\s*)folium\.TileLayer\(\n"
    r"(?:.*\n)*?"
    r"\s*\)\.add_to\(m\)\n",
    re.MULTILINE,
)

# Padrão 2: troca "tiles=None, control_scale=True" de volta para "tiles=..."
MAP_REPLACEMENTS = [
    (
        'tiles=None, control_scale=True',
        'tiles="CartoDB dark_matter"',
    ),
]

for cid in TARGETS:
    idx = next((i for i, c in enumerate(nb["cells"]) if c.get("id") == cid), None)
    if idx is None:
        continue

    src_list = nb["cells"][idx]["source"]
    src_str = "".join(src_list) if isinstance(src_list, list) else src_list
    before = src_str

    # 1. Remove o bloco TileLayer explícito
    src_str = TILE_BLOCK_RE.sub("\n", src_str)

    # 2. Devolve o atalho tiles="CartoDB dark_matter"
    for old, new in MAP_REPLACEMENTS:
        src_str = src_str.replace(old, new)

    if src_str != before:
        nb["cells"][idx]["source"] = src_str.splitlines(keepends=True)
        nb["cells"][idx]["outputs"] = []
        nb["cells"][idx]["execution_count"] = None
        print(f"[ok] {cid}: voltado ao shortcut 'CartoDB dark_matter'")
    else:
        print(f"[noop] {cid}")

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

# Verifica
print("\n— Verificação —")
import ast
nb2 = json.load(open(NB_PATH, encoding="utf-8"))
for cid in TARGETS:
    idx = next(i for i, c in enumerate(nb2["cells"]) if c.get("id") == cid)
    src = "".join(nb2["cells"][idx]["source"])
    try:
        ast.parse(src)
        syntax = "OK"
    except SyntaxError as e:
        syntax = f"FAIL: {e.msg} L{e.lineno}"

    has_dark = '"CartoDB dark_matter"' in src
    has_tilelayer_block = "folium.TileLayer(" in src
    print(f"  {cid}: syntax={syntax} | shortcut={'YES' if has_dark else 'no'} | tilelayer={'still there' if has_tilelayer_block else 'removed'}")
