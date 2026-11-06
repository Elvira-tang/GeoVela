# ─── OpenGIS Agent · run cb6f077b · step 1 · transform_first_row_wgs84_to_3857 ───
# Timestamp : 2026-11-06T00:59:37
# Semantic : transform_first_row_wgs84_to_3857
# Metadata : 20261106-005937-step01-transform_first_row_wgs84_to_3857.metadata.json
# User query: Read the first data row of input.csv. Transform its Chinese 经度/纬度 from EPSG:4326 to EPSG:3857 using an appropriate geospatial library. Write result.json with source_name, x_3857 and y_3857, coordinate…
import json
import pandas as pd
from pyproj import Transformer

df = pd.read_csv("input.csv", encoding="utf-8-sig", nrows=1)
row = df.iloc[0]
lng = float(row["经度"]); lat = float(row["纬度"])
name = row["名称"] if isinstance(row["名称"], str) and row["名称"].strip() else ""

t = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
x, y = t.transform(lng, lat)

result = {
    "source_name": name,
    "x_3857": round(x, 3),
    "y_3857": round(y, 3),
}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(df.shape, list(df.columns)[:7])
print(lng, lat, result)

# ─── Observations ───
# (1, 15) ['类别', '名称', '英文名称', '类型细分', '经度', '纬度', '长度(m)']
# 120.269649 31.487771 {'source_name': '江南大学蠡湖校区体育馆', 'x_3857': 13388356.085, 'y_3857': 3696258.834}
