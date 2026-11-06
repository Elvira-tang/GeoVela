# ─── OpenGIS Agent · run eb6df6bb · step 2 · spatial_join_points_districts ───
# Timestamp : 2026-11-06T00:50:35
# Semantic : spatial_join_points_districts
# Metadata : 20261106-005035-step02-spatial_join_points_districts.metadata.json
# User query: Load points.csv using the WGS84 longitude/latitude columns and spatially join the points to districts.geojson. Write result.json with matched_count and district_counts keyed by polygon name. Exclude u…
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

df = pd.read_csv("points.csv", encoding="utf-8-sig")
dist = gpd.read_file("districts.geojson")

print("districts CRS:", dist.crs)
print("districts bounds:", dist.total_bounds)
print("points lon range:", df["经度(WGS84)"].min(), df["经度(WGS84)"].max())
print("points lat range:", df["纬度(WGS84)"].min(), df["纬度(WGS84)"].max())
print("null coords:", df[["经度(WGS84)", "纬度(WGS84)"]].isna().sum().to_dict())

pts = gpd.GeoDataFrame(
    df.copy(),
    geometry=[Point(x, y) for x, y in zip(df["经度(WGS84)"], df["纬度(WGS84)"])],
    crs="EPSG:4326",
)
if dist.crs is None:
    dist = dist.set_crs("EPSG:4326")
    print("assigned EPSG:4326 to districts (no CRS found)")
dist_w = dist.to_crs("EPSG:4326")

joined = gpd.sjoin(pts, dist_w[["name", "geometry"]], how="left", predicate="within")
print("rows after sjoin:", len(joined))
inside = joined[joined["name"].notna()]
multi = inside.groupby(level=0).size()
print("points in >1 polygon:", int((multi > 1).sum()))

inside = inside.reset_index().rename(columns={"index": "_pt_index"})
if "_pt_index" not in inside.columns:
    inside["_pt_index"] = range(len(inside))
matched = inside.drop_duplicates(subset=["_pt_index"])
matched_count = int(matched.shape[0])
counts = matched["name"].value_counts().sort_index()
print("matched:", matched_count, "unmatched:", len(df) - matched_count)
print(counts.to_dict())

agree = (matched["区县"] == matched["name"]).sum()
print("attr agreement 区县 vs polygon:", int(agree), "/", matched_count)
print(matched.loc[matched["区县"] != matched["name"], ["名称", "区县", "name"]].head(10).to_string())

result = {
    "matched_count": matched_count,
    "district_counts": {k: int(v) for k, v in counts.items()},
}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False, indent=2))

matched.drop(columns="geometry").to_csv("points_matched.csv", index=False, encoding="utf-8-sig")
gpd.GeoDataFrame(matched[["名称", "name", "geometry"]], geometry="geometry", crs="EPSG:4326").to_file("points_matched.geojson", driver="GeoJSON")
print("sum check:", sum(result["district_counts"].values()) == matched_count)

# ─── Observations ───
# districts CRS: EPSG:4326
# districts bounds: [119.51966   31.108647 120.605759  31.99082 ]
# points lon range: 119.574384 120.575661
# points lat range: 31.182103 31.940685
# null coords: {'经度(WGS84)': 0, '纬度(WGS84)': 0}
# rows after sjoin: 1654
# points in >1 polygon: 0
# 
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 468, in _run_exec
#     compiled = compile(code, "<agent>", "eval")
#                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 1
#     import json
#     ^^^^^^
# SyntaxError: invalid syntax
# 
# During handling of the above exception, another exception occurred:
# 
# Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 471, in _run_exec
#     exec(compile(code, "<agent>", "exec"), namespace, namespace)
#   File "<agent>", line 31, in <module>
#   File "C:\Users\Elvira\AppData\Roaming\opengis\venv\Lib\site-packages\pandas\core\frame.py", line 8908, in drop_duplicates
#     result = self[-self.duplicated(subset, keep=keep)]
#                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "C:\Users\Elvira\AppData\Roaming\opengis\venv\Lib\site-packages\pandas\core\frame.py", line 9041, in duplicated
#     raise KeyError(Index(diff))
# KeyError: Index(['index'], dtype='str')
# 
# --- stdout before error ---
# districts CRS: EPSG:4326
# districts bounds: [119.51966   31.108647 120.605759  31.99082 ]
# points lon range: 119.574384 120.575661
# points lat range: 31.182103 31.940685
# null coords: {'经度(WGS84)': 0, '纬度(WGS84)': 0}
# rows after sjoin: 1654
# points in >1 polygon: 0
