# ─── OpenGIS Agent · run 7ba9248d · step 1 · transform_first_row_to_3857 ───
# Timestamp : 2026-11-06T00:59:26
# Semantic : transform_first_row_to_3857
# Metadata : 20261106-005926-step01-transform_first_row_to_3857.metadata.json
# User query: Read the first data row of input.csv. Transform its Chinese 经度/纬度 from EPSG:4326 to EPSG:3857 using an appropriate geospatial library. Write result.json with source_name, x_3857 and y_3857, coordinate…
import json
import pandas as pd
from pyproj import Transformer
from pathlib import Path

csv_path = Path("input.csv")
df = pd.read_csv(csv_path, encoding="utf-8-sig", nrows=1)

row = df.iloc[0]
name = str(row["名称"]).strip()
lon = float(row["经度"])
lat = float(row["纬度"])

transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
x, y = transformer.transform(lon, lat)

result = {
    "source_name": name,
    "x_3857": round(x, 3),
    "y_3857": round(y, 3),
}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
print("lon/lat:", lon, lat)

# ─── Observations ───
# {"source_name": "江南大学蠡湖校区体育馆", "x_3857": 13388356.085, "y_3857": 3696258.834}
# lon/lat: 120.269649 31.487771
