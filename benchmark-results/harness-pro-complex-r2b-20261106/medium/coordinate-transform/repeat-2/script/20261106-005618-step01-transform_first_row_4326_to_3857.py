# ─── OpenGIS Agent · run 1a65da2a · step 1 · transform_first_row_4326_to_3857 ───
# Timestamp : 2026-11-06T00:56:18
# Semantic : transform_first_row_4326_to_3857
# Metadata : 20261106-005618-step01-transform_first_row_4326_to_3857.metadata.json
# User query: Read the first data row of input.csv. Transform its Chinese 经度/纬度 from EPSG:4326 to EPSG:3857 using an appropriate geospatial library. Write result.json with source_name, x_3857 and y_3857, coordinate…
import json
import pandas as pd
from pyproj import Transformer

df = pd.read_csv("input.csv", encoding="utf-8-sig", nrows=1)
row = df.iloc[0]
name = str(row["名称"]).strip()
lon = float(row["经度"])
lat = float(row["纬度"])

tr = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
x, y = tr.transform(lon, lat)

result = {
    "source_name": name,
    "x_3857": round(x, 3),
    "y_3857": round(y, 3),
}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(name, lon, lat)
print(x, y)

# ─── Observations ───
# 江南大学蠡湖校区体育馆 120.269649 31.487771
# 13388356.084565746 3696258.833830366
