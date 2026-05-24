"""Patch: overlay=False -> overlay=True nas FeatureGroups de horizontes
(estavam virando base layer e escondendo o tile do CartoDB)."""
import json
from pathlib import Path

NB = Path(r"c:/Users/pedro/Documents/2026/ClaudeImpactLab/code/logit_compstat.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))
cell = nb["cells"][30]
src = "".join(cell["source"])
old = (
    '        show=(s == 1),\n'
    '        overlay=False,  # comporta-se como base layer mutuamente exclusiva\n'
)
new = (
    '        show=(s == 1),\n'
    '        overlay=True,  # overlay (checkbox); base layer escondia o tile\n'
)
assert src.count(old) == 1, f"padrao nao encontrado / ambiguo: {src.count(old)}"
src2 = src.replace(old, new)
cell["source"] = src2.splitlines(keepends=True)
cell["outputs"] = []
cell["execution_count"] = None
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("patch aplicado")
