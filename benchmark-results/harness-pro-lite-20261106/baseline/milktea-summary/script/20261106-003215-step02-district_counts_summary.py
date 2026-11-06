# ─── OpenGIS Agent · run 56786a1a · step 2 · district_counts_summary ───
# Timestamp : 2026-11-06T00:32:15
# Semantic : district_counts_summary
# Metadata : 20261106-003215-step02-district_counts_summary.metadata.json
# User query: Read input.csv. Write result.json as UTF-8 JSON with exactly: row_count (integer) and district_counts (object counting the Chinese 区县 column). Verify the written file, then finish.
import pandas as pd, json
df = pd.read_csv('input.csv', encoding='utf-8-sig', dtype=str)
counts = df['区县'].value_counts().to_dict()
result = {"row_count": int(len(df)), "district_counts": {str(k): int(v) for k, v in counts.items()}}
with open('result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(result)

# ─── Observations ───
# {'row_count': 1654, 'district_counts': {'江阴市': 298, '梁溪区': 248, '宜兴市': 243, '新吴区': 225, '滨湖区': 222, '惠山区': 215, '锡山区': 203}}
