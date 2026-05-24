import json
nb = json.load(open(r"c:\Users\pedro\Documents\2026\ClaudeImpactLab\code\logit_compstat.ipynb", encoding="utf-8"))
for cid in ["cell-22-risk-map", "7ec058e2", "cell-23-interactive-map"]:
    idx = next((i for i, c in enumerate(nb["cells"]) if c.get("id") == cid), None)
    if idx is None:
        print(f"--- {cid} NOT FOUND ---")
        continue
    src = "".join(nb["cells"][idx]["source"])
    print(f"--- {cid} (chars={len(src)}) ---")
    # Find lines with 'folium.TileLayer' to check indent
    for i, line in enumerate(src.split("\n")):
        if "folium.TileLayer" in line or "TileLayer(" in line or ".add_to(m)" in line:
            print(f"  L{i}: {repr(line[:120])}")
    print()
