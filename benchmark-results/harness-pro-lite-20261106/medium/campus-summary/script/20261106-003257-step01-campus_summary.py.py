# ─── OpenGIS Agent · run 892bcbc2 · step 1 · campus_summary.py ───
# Timestamp : 2026-11-06T00:32:57
# Semantic : campus_summary.py
# Metadata : 20261106-003257-step01-campus_summary.py.metadata.json
# User query: Read input.csv. Write result.json as UTF-8 JSON with exactly: row_count (integer) and category_counts (object counting the Chinese 类别 column). Use a direct file/data tool or Python, verify the written…
import csv, json, collections, os

with open("input.csv", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

cats = collections.Counter(r["类别"] for r in rows)
result = {"row_count": len(rows), "category_counts": dict(cats)}

with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(len(rows), dict(cats))

# ─── Observations ───
# 234 {'建筑': 95, '设施': 26, '体育休闲': 34, '出入口': 9, '道路': 61, '用地': 2, '景点': 3, '节点': 4}
