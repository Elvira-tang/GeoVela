# ─── OpenGIS Agent · run bf4c7aa7 · step 1 · wgs84_to_webmercator_first_row ───
# Timestamp : 2026-11-06T00:44:34
# Semantic : wgs84_to_webmercator_first_row
# Metadata : 20261106-004434-step01-wgs84_to_webmercator_first_row.metadata.json
# User query: Read the first data row of input.csv. Transform its Chinese 经度/纬度 from EPSG:4326 to EPSG:3857 using an appropriate geospatial library. Write result.json with source_name, x_3857 and y_3857, coordinate…
import json, csv
import pandas as pd
from pyproj import Transformer
from pathlib import Path

src = Path("input.csv")
df = pd.read_csv(src, encoding="utf-8-sig")
row = df.iloc[0]

name = row["名称"]
lon = float(row["经度"])
lat = float(row["纬度"])

t = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
x, y = t.transform(lon, lat)

result = {
    "source_name": name,
    "x_3857": round(x, 3),
    "y_3857": round(y, 3),
}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(name, lon, lat, x, y)
print(json.dumps(result, ensure_ascii=False, indent=2))

# ─── Observations ───
# 江南大学蠡湖校区体育馆 120.269649 31.487771 13388356.084565746 3696258.833830366
# {
#   "source_name": "江南大学蠡湖校区体育馆",
#   "x_3857": 13388356.085,
#   "y_3857": 3696258.834
# }
