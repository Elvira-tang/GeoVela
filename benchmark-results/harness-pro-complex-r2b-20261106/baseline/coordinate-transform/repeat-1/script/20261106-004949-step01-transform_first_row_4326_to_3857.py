# ─── OpenGIS Agent · run 8affcc90 · step 1 · transform_first_row_4326_to_3857 ───
# Timestamp : 2026-11-06T00:49:49
# Semantic : transform_first_row_4326_to_3857
# Metadata : 20261106-004949-step01-transform_first_row_4326_to_3857.metadata.json
# User query: Read the first data row of input.csv. Transform its Chinese 经度/纬度 from EPSG:4326 to EPSG:3857 using an appropriate geospatial library. Write result.json with source_name, x_3857 and y_3857, coordinate…
import csv, json, math
from pyproj import Transformer

CSV = "input.csv"
OUT = "result.json"

with open(CSV, "r", encoding="utf-8-sig", newline="") as f:
    row = next(csv.DictReader(f))

lng = float(row["经度"])
lat = float(row["纬度"])
name = (row.get("名称") or "").strip()

t = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
x, y = t.transform(lng, lat)

res = {
    "source_name": name,
    "x_3857": round(x, 3),
    "y_3857": round(y, 3),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2)

print(json.dumps(res, ensure_ascii=False, indent=2))
print("input lng/lat:", lng, lat)

# ─── Observations ───
# {
#   "source_name": "江南大学蠡湖校区体育馆",
#   "x_3857": 13388356.085,
#   "y_3857": 3696258.834
# }
# input lng/lat: 120.269649 31.487771
