# ─── OpenGIS Agent · run fb09911d · step 1 · validate_wgs84_rows ───
# Timestamp : 2026-11-06T01:06:20
# Semantic : validate_wgs84_rows
# Metadata : 20261106-010620-step01-validate_wgs84_rows.metadata.json
# User query: input.csv contains deliberately appended malformed rows. Parse it robustly using the WGS84 longitude/latitude columns. Reject rows whose coordinates are missing, non-numeric, or outside valid ranges. …
import csv, json, math, io

path = "input.csv"
with open(path, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8-sig")

reader = csv.reader(io.StringIO(text, newline=""))
rows = list(reader)
header = rows[0]
data = rows[1:]

idx_lon = header.index("经度(WGS84)")
idx_lat = header.index("纬度(WGS84)")

def num(v):
    if v is None:
        return None
    s = str(v).strip().replace("，", "").replace(",", "")
    if s == "":
        return None
    try:
        x = float(s)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    return x

valid = 0
rejected = 0
reasons = {}
for r in data:
    if not any(c.strip() for c in r):
        continue
    lon = num(r[idx_lon]) if len(r) > idx_lon else None
    lat = num(r[idx_lat]) if len(r) > idx_lat else None
    if lon is None or lat is None:
        rejected += 1
        reasons["missing_or_non_numeric"] = reasons.get("missing_or_non_numeric", 0) + 1
    elif not (-180.0 <= lon <= 180.0) or not (-90.0 <= lat <= 90.0):
        rejected += 1
        reasons["out_of_range"] = reasons.get("out_of_range", 0) + 1
    else:
        valid += 1

result = {"valid_rows": int(valid), "rejected_rows": int(rejected)}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(len(header), len(data), valid, rejected, reasons)
print(json.dumps(result, ensure_ascii=False))

# ─── Observations ───
# 21 1658 1654 3 {'missing_or_non_numeric': 3}
# {"valid_rows": 1654, "rejected_rows": 3}
