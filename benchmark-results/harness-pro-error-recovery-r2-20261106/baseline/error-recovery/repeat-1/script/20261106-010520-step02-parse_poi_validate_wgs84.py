# ─── OpenGIS Agent · run 343404c5 · step 2 · parse_poi_validate_wgs84 ───
# Timestamp : 2026-11-06T01:05:20
# Semantic : parse_poi_validate_wgs84
# Metadata : 20261106-010520-step02-parse_poi_validate_wgs84.metadata.json
# User query: input.csv contains deliberately appended malformed rows. Parse it robustly using the WGS84 longitude/latitude columns. Reject rows whose coordinates are missing, non-numeric, or outside valid ranges. …
import csv, json, math

p = "input.csv"
with open(p, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

print("fields:", len(fields))
print("rows:", len(rows))
lon_col, lat_col = "经度(WGS84)", "纬度(WGS84)"
print("cols ok:", lon_col in fields, lat_col in fields)

valid = 0
rejected = 0
reasons = {}
blank_rows = 0
for r in rows:
    if r is None:
        continue
    vals = [v for v in r.values() if v is not None and str(v).strip() != ""]
    if not vals:
        blank_rows += 1
        continue
    rj = None
    lo = r.get(lon_col); la = r.get(lat_col)
    los = (lo or "").strip(); las = (la or "").strip()
    try:
        lonf = float(los); latf = float(las)
        if not (math.isfinite(lonf) and math.isfinite(latf)):
            rj = "non-finite"
        elif not (-180.0 <= lonf <= 180.0):
            rj = "lon out of range"
        elif not (-90.0 <= latf <= 90.0):
            rj = "lat out of range"
    except ValueError:
        rj = "missing" if (los == "" or las == "") else "non-numeric"
    if rj is None:
        valid += 1
    else:
        rejected += 1
        reasons[rj] = reasons.get(rj, 0) + 1

print("blank logical rows skipped:", blank_rows)
print("valid:", valid, "rejected:", rejected)
print("reasons:", reasons)

with open("result.json", "w", encoding="utf-8") as f:
    json.dump({"valid_rows": valid, "rejected_rows": rejected}, f)

# ─── Observations ───
# fields: 21
# rows: 1657
# cols ok: True True
# blank logical rows skipped: 0
# valid: 1654 rejected: 3
# reasons: {'missing': 3}
