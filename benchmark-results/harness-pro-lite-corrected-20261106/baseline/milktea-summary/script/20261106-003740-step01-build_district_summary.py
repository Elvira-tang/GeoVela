# ─── OpenGIS Agent · run 7af20092 · step 1 · build_district_summary ───
# Timestamp : 2026-11-06T00:37:40
# Semantic : build_district_summary
# Metadata : 20261106-003740-step01-build_district_summary.metadata.json
# User query: Read input.csv. Write result.json as UTF-8 JSON with exactly: row_count (integer) and district_counts (object counting the Chinese 区县 column). Verify the written file, then finish.
import json
import pandas as pd

df = pd.read_csv("input.csv", encoding="utf-8-sig", dtype=str)
row_count = int(len(df))
counts = df["区县"].fillna("").value_counts(dropna=False)
district_counts = {str(k): int(v) for k, v in counts.items()}

result = {"row_count": row_count, "district_counts": district_counts}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(row_count, district_counts)

# ─── Observations ───
# 1654 {'江阴市': 298, '梁溪区': 248, '宜兴市': 243, '新吴区': 225, '滨湖区': 222, '惠山区': 215, '锡山区': 203}
