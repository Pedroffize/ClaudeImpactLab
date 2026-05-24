"""Corrige o timing da IIFE no cell-23-interactive-map: envolve em
   window.addEventListener('load', ...) para garantir que as variáveis
   feature_group_xxx do Folium já estejam declaradas quando o JS rodar.
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.load(open(NB_PATH, encoding="utf-8"))

idx = next(i for i, c in enumerate(nb["cells"]) if c.get("id") == "cell-23-interactive-map")
src = "".join(nb["cells"][idx]["source"])

# A IIFE atual começa com `(function() {` e termina com `})();`
# Substituímos por `window.addEventListener('load', function() { ... });`
# que garante que rode após TODAS as <script> tags terem sido executadas.

old_js_start = 'js_code = f"""\n(function() {{\n'
new_js_start = 'js_code = f"""\nwindow.addEventListener("load", function() {{\n'

old_js_end = '  refresh();\n}})();\n"""\n'
new_js_end = '  refresh();\n}});\n"""\n'

if old_js_start in src and old_js_end in src:
    src = src.replace(old_js_start, new_js_start)
    src = src.replace(old_js_end, new_js_end)
    nb["cells"][idx]["source"] = src.splitlines(keepends=True)
    nb["cells"][idx]["outputs"] = []
    nb["cells"][idx]["execution_count"] = None
    with open(NB_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print("[ok] IIFE envolvida em window.addEventListener('load', ...)")
else:
    print("[fail] Padrão da IIFE não encontrado — vou inspecionar")
    # Debug: mostra onde está '(function()' no source
    idxs = []
    pos = 0
    while True:
        p = src.find("(function()", pos)
        if p < 0: break
        idxs.append(p)
        pos = p + 1
    print(f"  '(function()' encontrado em posições: {idxs}")

# Verifica sintaxe
import ast
nb2 = json.load(open(NB_PATH, encoding="utf-8"))
idx2 = next(i for i, c in enumerate(nb2["cells"]) if c.get("id") == "cell-23-interactive-map")
src2 = "".join(nb2["cells"][idx2]["source"])
try:
    ast.parse(src2)
    print("[ok] Sintaxe Python válida")
except SyntaxError as e:
    print(f"[fail] SyntaxError L{e.lineno}: {e.msg}")
