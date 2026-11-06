# ─── OpenGIS Agent · run 69d1b8aa · step 1 · robust_poi_coord_validation ───
# Timestamp : 2026-11-06T01:07:21
# Semantic : robust_poi_coord_validation
# Metadata : 20261106-010721-step01-robust_poi_coord_validation.metadata.json
# User query: input.csv contains deliberately appended malformed rows. Parse it robustly using the WGS84 longitude/latitude columns. Reject rows whose coordinates are missing, non-numeric, or outside valid ranges. …
import csv, io, json, math, os

path = "input.csv"
with open(path, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8-sig", errors="replace")

rows = list(csv.reader(io.StringIO(text, newline="")))
header = [h.strip() for h in rows[0]]

def find(*keys):
    for i, h in enumerate(header):
        if all(k in h for k in keys):
            return i
    raise KeyError(keys)

lon_i = find("经度", "WGS84")
lat_i = find("纬度", "WGS84")

valid = 0
rejected = 0
reasons = {}
for r in rows[1:]:
    if not any(c.strip() for c in r):
        continue
    aligned = list(r[: len(header)]) + [""] * max(0, len(header) - len(r))
    lon_s = aligned[lon_i].strip()
    lat_s = aligned[lat_i].strip()
    try:
        lon = float(lon_s)
        lat = float(lat_s)
    except (ValueError, TypeError):
        rejected += 1
        k = "missing" if (not lon_s or not lat_s) else "non_numeric"
        reasons[k] = reasons.get(k, 0) + 1
        continue
    if not (math.isfinite(lon) and math.isfinite(lat)):
        rejected += 1
        reasons["non_finite"] = reasons.get("non_finite", 0) + 1
    elif not (-180.0 <= lon <= 180.0) or not (-90.0 <= lat <= 90.0):
        rejected += 1
        reasons["out_of_range"] = reasons.get("out_of_range", 0) + 1
    else:
        valid += 1

result = {"valid_rows": int(valid), "rejected_rows": int(rejected)}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("header_len", len(header), "lon_i", lon_i, "lat_i", lat_i)
print("data_rows", len(rows) - 1)
print(result, reasons)

# ─── Observations ───
# header_len 21 lon_i 12 lat_i 13
# data_rows 1658
# {'valid_rows': 1654, 'rejected_rows': 3} {'field_count': 3}
