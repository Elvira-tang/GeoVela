# ─── OpenGIS Agent · run bee87f79 · step 1 · transform_first_row_4326_to_3857 ───
# Timestamp : 2026-11-06T00:50:00
# Semantic : transform_first_row_4326_to_3857
# Metadata : 20261106-005000-step01-transform_first_row_4326_to_3857.metadata.json
# User query: Read the first data row of input.csv. Transform its Chinese 经度/纬度 from EPSG:4326 to EPSG:3857 using an appropriate geospatial library. Write result.json with source_name, x_3857 and y_3857, coordinate…
import json
import pandas as pd
from pyproj import Transformer

df = pd.read_csv("input.csv", encoding="utf-8-sig")
row = df.iloc[0]
lon = float(row["经度"])
lat = float(row["纬度"])

t = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
x, y = t.transform(lon, lat)

result = {
    "source_name": str(row["名称"]),
    "x_3857": round(x, 3),
    "y_3857": round(y, 3),
}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(dict(row[["名称", "经度", "纬度"]]))
print(result)

# ─── Observations ───
# {'名称': '江南大学蠡湖校区体育馆', '经度': np.float64(120.269649), '纬度': np.float64(31.487771)}
# {'source_name': '江南大学蠡湖校区体育馆', 'x_3857': 13388356.085, 'y_3857': 3696258.834}
