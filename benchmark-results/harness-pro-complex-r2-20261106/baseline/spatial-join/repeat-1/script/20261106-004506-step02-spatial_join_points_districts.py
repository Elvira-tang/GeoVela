# ─── OpenGIS Agent · run 638b8139 · step 2 · spatial_join_points_districts ───
# Timestamp : 2026-11-06T00:45:06
# Semantic : spatial_join_points_districts
# Metadata : 20261106-004506-step02-spatial_join_points_districts.metadata.json
# User query: Load points.csv using the WGS84 longitude/latitude columns and spatially join the points to districts.geojson. Write result.json with matched_count and district_counts keyed by polygon name. Exclude u…
import json
import pandas as pd
import geopandas as gpd
import numpy as np

pts_df = pd.read_csv("points.csv")
dist = gpd.read_file("districts.geojson")
print("districts crs:", dist.crs, "| bounds:", [round(v, 4) for v in dist.total_bounds])
print("polygons:", len(dist), list(dist["name"]))

pts_df = pts_df.dropna(subset=["经度(WGS84)", "纬度(WGS84)"]).copy()
pts_df = pts_df[(pts_df["经度(WGS84)"].between(-180, 180)) & (pts_df["纬度(WGS84)"].between(-90, 90))]
print("valid points:", len(pts_df))

pts = gpd.GeoDataFrame(
    pts_df,
    geometry=gpd.points_from_xy(pts_df["经度(WGS84)"], pts_df["纬度(WGS84)"]),
    crs="EPSG:4326",
)
if dist.crs is None:
    dist = dist.set_crs("EPSG:4326")
dist = dist.to_crs("EPSG:4326")

joined = gpd.sjoin(pts, dist[["name", "geometry"]], how="inner", predicate="intersects")
matched = joined[~joined.index.duplicated(keep="first")]
print("joined rows:", len(joined), "| unique matched points:", len(matched))
print("columns:", list(matched.columns))
counts = matched["name"].value_counts().sort_index()
print(counts.to_string())
print("sum:", int(counts.sum()))

result = {"matched_count": int(len(matched)), "district_counts": {str(k): int(v) for k, v in counts.items()}}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False, indent=2)[:800])
print("NAME collisions (duplicate polygons):", int(joined.index.duplicated().sum()))

# ─── Observations ───
# districts crs: EPSG:4326 | bounds: [np.float64(119.5197), np.float64(31.1086), np.float64(120.6058), np.float64(31.9908)]
# polygons: 7 ['锡山区', '惠山区', '滨湖区', '梁溪区', '新吴区', '江阴市', '宜兴市']
# valid points: 1654
# joined rows: 1651 | unique matched points: 1651
# columns: ['POI_ID', '名称', '品牌', '类型', '类型编码', '地址', '省', '市', '区县', '商圈', '经度(GCJ-02)', '纬度(GCJ-02)', '经度(WGS84)', '纬度(WGS84)', '电话', '评分', '人均消费(元)', '营业时间', '来源', '数据来源', '采集日期', 'geometry', 'index_right', 'name']
# name
# 宜兴市    243
# 惠山区    219
# 新吴区    202
# 梁溪区    270
# 江阴市    295
# 滨湖区    229
# 锡山区    193
# sum: 1651
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
# NAME collisions (duplicate polygons): 0
