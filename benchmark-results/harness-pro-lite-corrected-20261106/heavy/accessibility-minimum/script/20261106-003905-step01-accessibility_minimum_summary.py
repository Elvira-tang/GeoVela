# ─── OpenGIS Agent · run 78e47890 · step 1 · accessibility_minimum_summary ───
# Timestamp : 2026-11-06T00:39:05
# Semantic : accessibility_minimum_summary
# Metadata : 20261106-003905-step01-accessibility_minimum_summary.metadata.json
# User query: Read input.csv. Write result.json as UTF-8 JSON with exactly: row_count (integer) and minimum_total_min (number, minimum of total_min). Verify the written file, then finish.
import pandas as pd, json, math

df = pd.read_csv("input.csv", encoding="utf-8-sig")
col = "total_min"
vals = pd.to_numeric(df[col], errors="coerce")
result = {
    "row_count": int(len(df)),
    "minimum_total_min": float(vals.min()),
}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(result)
print("na_total_min:", int(vals.isna().sum()))

# ─── Observations ───
# {'row_count': 5500, 'minimum_total_min': 16.6}
# na_total_min: 0
