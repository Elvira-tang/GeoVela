# ─── OpenGIS Agent · run 83269699 · step 3 · spatial_join_points_districts ───
# Timestamp : 2026-11-06T00:59:55
# Semantic : spatial_join_points_districts
# Metadata : 20261106-005955-step03-spatial_join_points_districts.metadata.json
# User query: Load points.csv using the WGS84 longitude/latitude columns and spatially join the points to districts.geojson. Write result.json with matched_count and district_counts keyed by polygon name. Exclude u…
import pandas as pd, geopandas as gpd, json

pts_df = pd.read_csv('points.csv', encoding='utf-8-sig')
dist = gpd.read_file('districts.geojson')
dist = dist[['name', 'geometry']]
pts = gpd.GeoDataFrame(
    pts_df,
    geometry=gpd.points_from_xy(
        pd.to_numeric(pts_df['经度(WGS84)'], errors='coerce'),
        pd.to_numeric(pts_df['纬度(WGS84)'], errors='coerce'),
    ),
    crs='EPSG:4326',
)
pts = pts[pts.geometry.notna() & ~pts.geometry.is_empty].copy()

joined = gpd.sjoin(pts, dist, how='inner', predicate='within')
print('joined rows:', len(joined), 'unique pts:', joined['POI_ID'].nunique())
dups = joined['POI_ID'].value_counts()
print('points in >1 polygon:', (dups > 1).sum())

matched_pts = pts[pts['POI_ID'].isin(joined['POI_ID'])].copy()
unmatched_pts = pts[~pts['POI_ID'].isin(joined['POI_ID'])].copy()
print('total valid pts:', len(pts), 'matched:', len(matched_pts), 'unmatched:', len(unmatched_pts))

counts = joined['name'].value_counts()
district_counts = {name: int(counts.get(name, 0)) for name in dist['name']}
result = {
    'matched_count': int(len(matched_pts)),
    'district_counts': district_counts,
}
with open('result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False, indent=2))
print('sum district_counts:', sum(district_counts.values()))
print('unmatched sample:'); print(unmatched_pts[['POI_ID','名称','区县','经度(WGS84)','纬度(WGS84)']].head(10).to_string())

# ─── Observations ───
# joined rows: 1651 unique pts: 1651
# points in >1 polygon: 0
# total valid pts: 1654 matched: 1651 unmatched: 3
# {
#   "matched_count": 1651,
#   "district_counts": {
#     "锡山区": 193,
#     "惠山区": 219,
#     "滨湖区": 229,
#     "梁溪区": 270,
#     "新吴区": 202,
#     "江阴市": 295,
#     "宜兴市": 243
#   }
# }
# sum district_counts: 1651
# unmatched sample:
#           POI_ID               名称   区县   经度(WGS84)  纬度(WGS84)
# 1326  B0L2250A8I  茶百道(无锡江阴小湖商贸城店)  江阴市  119.995903  31.856495
# 1348  B0MAFDSZ1P      蜜雪冰城(五洲国际店)  江阴市  119.988213  31.853000
# 1389  B0J24Z1AN0        蜜雪冰城(美林店)  江阴市  119.999665  31.842384
