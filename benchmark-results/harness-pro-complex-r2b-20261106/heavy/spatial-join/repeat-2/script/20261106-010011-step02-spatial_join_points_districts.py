# ─── OpenGIS Agent · run 4e2362db · step 2 · spatial_join_points_districts ───
# Timestamp : 2026-11-06T01:00:11
# Semantic : spatial_join_points_districts
# Metadata : 20261106-010011-step02-spatial_join_points_districts.metadata.json
# User query: Load points.csv using the WGS84 longitude/latitude columns and spatially join the points to districts.geojson. Write result.json with matched_count and district_counts keyed by polygon name. Exclude u…
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

lon_col, lat_col = "经度(WGS84)", "纬度(WGS84)"

pts = pd.read_csv("points.csv", encoding="utf-8-sig", dtype=str)
pts[lon_col] = pd.to_numeric(pts[lon_col], errors="coerce")
pts[lat_col] = pd.to_numeric(pts[lat_col], errors="coerce")
pts = pts.dropna(subset=[lon_col, lat_col]).reset_index(drop=True)

gpts = gpd.GeoDataFrame(
    pts,
    geometry=[Point(x, y) for x, y in zip(pts[lon_col], pts[lat_col])],
    crs="EPSG:4326",
)

dis = gpd.read_file("districts.geojson")
if dis.crs is None:
    dis = dis.set_crs("EPSG:4326")
dis = dis.to_crs("EPSG:4326")

joined = gpd.sjoin(gpts, dis[["name", "geometry"]], how="inner", predicate="within")
matched = joined[~joined.index.duplicated(keep="first")]
print("input rows:", len(gpts), "join rows:", len(joined), "matched unique points:", len(matched))
print("dup matches:", int(len(joined) - len(matched)))

counts = matched["name"].value_counts().sort_index()
district_counts = {str(k): int(v) for k, v in counts.items()}
result = {"matched_count": int(len(matched)), "district_counts": district_counts}

with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps(result, ensure_ascii=False, indent=2))

# ─── Observations ───
# input rows: 1654 join rows: 1651 matched unique points: 1651
# dup matches: 0
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
