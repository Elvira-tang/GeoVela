# ─── OpenGIS Agent · run 9639bb8f · step 2 · parse_poi_csv_wgs84_validate ───
# Timestamp : 2026-11-06T01:07:52
# Semantic : parse_poi_csv_wgs84_validate
# Metadata : 20261106-010752-step02-parse_poi_csv_wgs84_validate.metadata.json
# User query: input.csv contains deliberately appended malformed rows. Parse it robustly using the WGS84 longitude/latitude columns. Reject rows whose coordinates are missing, non-numeric, or outside valid ranges. …
import csv, json, math

with open("input.csv", "r", encoding="utf-8-sig", errors="replace", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)

idx_lon = header.index("经度(WGS84)")
idx_lat = header.index("纬度(WGS84)")
print("lon col:", idx_lon, "lat col:", idx_lat, "header len:", len(header))
print("raw rows (incl blank):", len(rows))

valid = 0
rejected = 0
reasons = {}

def is_num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return v

blank_skipped = 0
for r in rows:
    if not r or all(c.strip() == "" for c in r):
        blank_skipped += 1
        continue
    lon_s = r[idx_lon] if len(r) > idx_lon else ""
    lat_s = r[idx_lat] if len(r) > idx_lat else ""
    lon_s = "" if lon_s is None else str(lon_s).strip()
    lat_s = "" if lat_s is None else str(lat_s).strip()
    key = "ok"
    if lon_s == "" or lat_s == "":
        key = "missing"
    else:
        lon = is_num(lon_s); lat = is_num(lat_s)
        if lon is None or lat is None:
            key = "non_numeric"
        elif not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            key = "out_of_range"
    if key == "ok":
        valid += 1
    else:
        rejected += 1
        reasons[key] = reasons.get(key, 0) + 1

print("valid:", valid, "rejected:", rejected, "blank_skipped:", blank_skipped)
print("reasons:", reasons)
print("field-count anomalies:", sum(1 for r in rows if len(r) != len(header)))

result = {"valid_rows": valid, "rejected_rows": rejected}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# ─── Observations ───
# lon col: 12 lat col: 13 header len: 21
# raw rows (incl blank): 1658
# valid: 1654 rejected: 4
# reasons: {'blank_line': 1, 'missing': 3}
# field-count anomalies: 4
