# ─── OpenGIS Agent · run 33ddec08 · step 1 · robust_poi_coord_validation_counts ───
# Timestamp : 2026-11-06T01:06:38
# Semantic : robust_poi_coord_validation_counts
# Metadata : 20261106-010638-step01-robust_poi_coord_validation_counts.metadata.json
# User query: input.csv contains deliberately appended malformed rows. Parse it robustly using the WGS84 longitude/latitude columns. Reject rows whose coordinates are missing, non-numeric, or outside valid ranges. …
import csv, json, io, os

base = os.getcwd()
csv_path = os.path.join(base, "input.csv")
out_path = os.path.join(base, "result.json")

with open(csv_path, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8-sig")

rows = list(csv.reader(io.StringIO(text)))
header = rows[0]
lon_key = next(h for h in header if "WGS84" in h and "经度" in h)
lat_key = next(h for h in header if "WGS84" in h and "纬度" in h)
lon_i = header.index(lon_key)
lat_i = header.index(lat_key)

valid = 0
rejected = 0
reasons = {}

def check(v):
    v = (v or "").strip()
    if v == "":
        return None, "missing"
    try:
        return float(v), None
    except ValueError:
        return None, "non-numeric"

for r in rows[1:]:
    if not any(c.strip() for c in r):
        continue
    if len(r) < len(header):
        r = r + [""] * (len(header) - len(r))
    lon, e1 = check(r[lon_i])
    lat, e2 = check(r[lat_i])
    err = e1 or e2
    if err is None:
        if not (-180.0 <= lon <= 180.0) or not (-90.0 <= lat <= 90.0):
            err = "out-of-range"
    if err:
        rejected += 1
        reasons[err] = reasons.get(err, 0) + 1
    else:
        valid += 1

result = {"valid_rows": valid, "rejected_rows": rejected}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f)

print("header_cols", len(header))
print("data_rows", valid + rejected)
print(result)
print("breakdown", reasons)
with open(out_path, encoding="utf-8") as f:
    print("file_content", f.read())

# ─── Observations ───
# header_cols 21
# data_rows 1657
# {'valid_rows': 1654, 'rejected_rows': 3}
# breakdown {'missing': 3}
# file_content {"valid_rows": 1654, "rejected_rows": 3}
