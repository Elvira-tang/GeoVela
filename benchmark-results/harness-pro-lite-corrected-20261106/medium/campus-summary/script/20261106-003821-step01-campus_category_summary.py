# ─── OpenGIS Agent · run c6554a8d · step 1 · campus_category_summary ───
# Timestamp : 2026-11-06T00:38:21
# Semantic : campus_category_summary
# Metadata : 20261106-003821-step01-campus_category_summary.metadata.json
# User query: Read input.csv. Write result.json as UTF-8 JSON with exactly: row_count (integer) and category_counts (object counting the Chinese 类别 column). Use a direct file/data tool or Python, verify the written…
import pandas as pd, json, os

df = pd.read_csv("input.csv", encoding="utf-8-sig")
counts = df["类别"].value_counts().to_dict()
counts = {str(k): int(v) for k, v in counts.items()}
result = {"row_count": int(len(df)), "category_counts": counts}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(result)

# ─── Observations ───
# {'row_count': 234, 'category_counts': {'建筑': 95, '道路': 61, '体育休闲': 34, '设施': 26, '出入口': 9, '节点': 4, '景点': 3, '用地': 2}}
