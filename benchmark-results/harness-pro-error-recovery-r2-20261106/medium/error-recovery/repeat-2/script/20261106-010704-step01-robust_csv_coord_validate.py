# ─── OpenGIS Agent · run 9d59a47a · step 1 · robust_csv_coord_validate ───
# Timestamp : 2026-11-06T01:07:04
# Semantic : robust_csv_coord_validate
# Metadata : 20261106-010704-step01-robust_csv_coord_validate.metadata.json
# User query: input.csv contains deliberately appended malformed rows. Parse it robustly using the WGS84 longitude/latitude columns. Reject rows whose coordinates are missing, non-numeric, or outside valid ranges. …
import csv, json, math, os

path = "input.csv"
with open(path, "r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f))

header = [h.strip() for h in rows[0]]
lon_i = header.index("经度(WGS84)")
lat_i = header.index("纬度(WGS84)")

valid = 0
rejected = 0
mismatch = []
bad_details = []

for raw in rows[1:]:
    if not raw or all(str(c).strip() == "" for c in raw):
        continue
    if len(raw) != len(header):
        mismatch.append(raw[:3])
        rejected += 1
        continue
    lon_s, lat_s = raw[lon_i].strip(), raw[lat_i].strip()
    ok = True
    try:
        if lon_s == "" or lat_s == "":
            ok = False
        else:
            lon, lat = float(lon_s), float(lat_s)
            if not (math.isfinite(lon) and math.isfinite(lat)):
                ok = False
            elif not (-180.0 <= lon <= 180.0) or not (-90.0 <= lat <= 90.0):
                ok = False
    except ValueError:
        ok = False
    if ok:
        valid += 1
    else:
        rejected += 1
        bad_details.append((raw[0], lon_s, lat_s, len(raw)))

print("header_len", len(header), "total_raw", len(rows)-1)
print("field_count_mismatch_rows", len(mismatch), mismatch)
print("coord_rejects", bad_details)
print("valid", valid, "rejected", rejected)

out = {"valid_rows": valid, "rejected_rows": rejected}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
print("written", out)

# ─── Observations ───
# header_len 21 total_raw 1658
# field_count_mismatch_rows 3 [['BROKEN-1', '损坏数据', ''], ['BROKEN-2', '缺失经度', ''], ['BROKEN-3', '超出范围', '']]
# coord_rejects []
# valid 1654 rejected 3
# written {'valid_rows': 1654, 'rejected_rows': 3}
