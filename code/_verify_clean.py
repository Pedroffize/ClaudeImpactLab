"""Verifica que cell-22-risk-map está sintaticamente correto agora."""
import json
import ast
from pathlib import Path

NB_PATH = Path(__file__).parent / "logit_compstat.ipynb"
nb = json.load(open(NB_PATH, encoding="utf-8"))

for cid in ["cell-22-risk-map", "7ec058e2", "cell-23-interactive-map"]:
    idx = next((i for i, c in enumerate(nb["cells"]) if c.get("id") == cid), None)
    if idx is None:
        continue
    src = "".join(nb["cells"][idx]["source"])

    # Tenta compilar o código Python (não executa, só checa sintaxe)
    try:
        ast.parse(src)
        status = "OK — sintaxe válida"
    except SyntaxError as e:
        status = f"FAIL — {e.msg} na linha {e.lineno}"

    print(f"{cid}: {status}")

    # Mostra primeiras 20 linhas para sanity check visual
    print("  Primeiras 15 linhas:")
    for i, line in enumerate(src.split("\n")[:15], 1):
        print(f"  {i:3}|{line}")
    print()
