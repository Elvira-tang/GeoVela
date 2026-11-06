# ─── OpenGIS Agent · run 43fcc979 · step 2 · spatial_join_points_districts ───
# Timestamp : 2026-11-06T00:54:46
# Semantic : spatial_join_points_districts
# Metadata : 20261106-005446-step02-spatial_join_points_districts.metadata.json
# User query: Load points.csv using the WGS84 longitude/latitude columns and spatially join the points to districts.geojson. Write result.json with matched_count and district_counts keyed by polygon name. Exclude u…
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

df = pd.read_csv("points.csv", encoding="utf-8-sig")
lon_col, lat_col = "经度(WGS84)", "纬度(WGS84)"
df = df.dropna(subset=[lon_col, lat_col])
pts = gpd.GeoDataFrame(
    df,
    geometry=[Point(xy) for xy in zip(df[lon_col].astype(float), df[lat_col].astype(float))],
    crs="EPSG:4326",
)

districts = gpd.read_file("districts.geojson")
if districts.crs is None:
    districts = districts.set_crs("EPSG:4326")
districts = districts.to_crs("EPSG:4326")

joined = gpd.sjoin(pts, districts[["name", "geometry"]], how="inner", predicate="intersects")
counts = joined["name"].value_counts().sort_index()
result = {
    "matched_count": int(len(joined)),
    "district_counts": {str(k): int(v) for k, v in counts.items()},
}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("total points:", len(pts), "unmatched:", len(pts) - len(joined))
print(json.dumps(result, ensure_ascii=False, indent=2))
print("sum of counts:", sum(result["district_counts"].values()))
print("districts total:", len(districts), "matched district names:", len(result["district_counts"]))
print("duplicate poi ids in join:", joined["POI_ID"].duplicated().sum())

# ─── Observations ───
# total points: 1654 unmatched: 3
# {
#   "matched_count": 1651,
#   "district_counts": {
#     "宜兴市": 243,
#     "惠山区": 219,
#     "新吴区": 202,
#     "梁溪区": 270,
#     "江阴市": 295,
#     "滨湖区": 229,
#     "锡山区": 193
#   }
# }
# sum of counts: 1651
# districts total: 7 matched district names: 7
# duplicate poi ids in join: 0
