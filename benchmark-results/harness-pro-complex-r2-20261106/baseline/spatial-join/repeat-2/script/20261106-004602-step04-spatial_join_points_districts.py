# ─── OpenGIS Agent · run dcd554a7 · step 4 · spatial_join_points_districts ───
# Timestamp : 2026-11-06T00:46:02
# Semantic : spatial_join_points_districts
# Metadata : 20261106-004602-step04-spatial_join_points_districts.metadata.json
# User query: Load points.csv using the WGS84 longitude/latitude columns and spatially join the points to districts.geojson. Write result.json with matched_count and district_counts keyed by polygon name. Exclude u…
import pandas as pd, geopandas as gpd, json

df = pd.read_csv("points.csv")
districts = gpd.read_file("districts.geojson").to_crs("EPSG:4326")

pts = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df["经度(WGS84)"], df["纬度(WGS84)"]),
    crs="EPSG:4326",
)
print("total points:", len(pts))

joined = gpd.sjoin(pts, districts[["name", "geometry"]], how="inner", predicate="intersects")
print("matched rows:", len(joined))
print("matched unique points:", joined["POI_ID"].nunique())

counts = joined["name"].value_counts().sort_index()
result = {
    "matched_count": int(len(joined)),
    "district_counts": {str(k): int(v) for k, v in counts.items()},
}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False, indent=2))

# ─── Observations ───
# total points: 1654
# matched rows: 1651
# matched unique points: 1651
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
