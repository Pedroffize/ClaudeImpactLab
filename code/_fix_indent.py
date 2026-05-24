"""Corrige indentação do bloco folium.TileLayer(...) que foi injetado em
   coluna 0 dentro de blocos que precisam de indent (cell-22 = 4 espaços,
   7ec058e2 = 8 espaços). cell-23 é módulo-top, fica em 0.
"""
import json
import re
from pathlib import Path

NB_PATH = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.load(open(NB_PATH, encoding="utf-8"))

# (cell_id, número de espaços de indent necessários)
TARGETS = [
    ("cell-22-risk-map", 4),
    ("7ec058e2",          8),
]

# Regex para identificar o bloco que precisa ser re-indentado:
# das linhas iniciando com 'folium.TileLayer(' até '.add_to(m)'
BLOCK_RE = re.compile(
    r"^(folium\.TileLayer\(\n"
    r"(?:.*\n)*?"
    r"\)\.add_to\(m\)\n)",
    re.MULTILINE,
)

for cid, indent in TARGETS:
    idx = next((i for i, c in enumerate(nb["cells"]) if c.get("id") == cid), None)
    if idx is None:
        print(f"[skip] {cid} não encontrado")
        continue

    src_list = nb["cells"][idx]["source"]
    src_str = "".join(src_list) if isinstance(src_list, list) else src_list

    # Aplica indent
    pad = " " * indent

    def indent_block(match):
        block = match.group(1)
        return "\n".join(pad + l if l else l for l in block.split("\n"))

    new_src = BLOCK_RE.sub(indent_block, src_str)

    if new_src != src_str:
        nb["cells"][idx]["source"] = new_src.splitlines(keepends=True)
        nb["cells"][idx]["outputs"] = []
        nb["cells"][idx]["execution_count"] = None
        print(f"[ok] {cid}: bloco TileLayer indentado com {indent} espaços")
    else:
        print(f"[noop] {cid}: padrão não encontrado")

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

# Verifica
print("\n— Verificação —")
nb2 = json.load(open(NB_PATH, encoding="utf-8"))
for cid, want_indent in TARGETS:
    idx = next(i for i, c in enumerate(nb2["cells"]) if c.get("id") == cid)
    src = "".join(nb2["cells"][idx]["source"])
    for line in src.split("\n"):
        if "folium.TileLayer(" in line:
            leading = len(line) - len(line.lstrip())
            ok = "OK" if leading == want_indent else f"FAIL (got {leading}, want {want_indent})"
            print(f"  {cid}: folium.TileLayer indent = {leading} → {ok}")
            break
