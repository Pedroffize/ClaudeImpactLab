import json
nb = json.load(open(r'c:\Users\pedro\Documents\2026\ClaudeImpactLab\code\logit_compstat.ipynb', encoding='utf-8'))
for c in nb['cells'][-5:]:
    src = ''.join(c.get('source', []))[:200]
    print(f"--- id={c.get('id')} | type={c.get('cell_type')} ---")
    print(src)
    print()
