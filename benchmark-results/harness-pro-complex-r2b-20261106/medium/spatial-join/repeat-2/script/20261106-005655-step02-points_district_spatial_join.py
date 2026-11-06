# ─── OpenGIS Agent · run 3de4a05c · step 2 · points_district_spatial_join ───
# Timestamp : 2026-11-06T00:56:55
# Semantic : points_district_spatial_join
# Metadata : 20261106-005655-step02-points_district_spatial_join.metadata.json
# User query: Load points.csv using the WGS84 longitude/latitude columns and spatially join the points to districts.geojson. Write result.json with matched_count and district_counts keyed by polygon name. Exclude u…
import json
import pandas as pd
import geopandas as gpd

pts = pd.read_csv('points.csv')
pts = pts.dropna(subset=['经度(WGS84)', '纬度(WGS84)'])
gpts = gpd.GeoDataFrame(
    pts,
    geometry=gpd.points_from_xy(pts['经度(WGS84)'], pts['纬度(WGS84)']),
    crs='EPSG:4326',
)

dist = gpd.read_file('districts.geojson')
if dist.crs is None:
    dist = dist.set_crs('EPSG:4326')
dist = dist.to_crs('EPSG:4326')
dist['geometry'] = dist.geometry.buffer(0)
dist = dist[['name', 'geometry']]

join_within = gpd.sjoin(gpts, dist, how='inner', predicate='within')
join_intersects = gpd.sjoin(gpts, dist, how='inner', predicate='intersects')

print('points:', len(gpts), 'within matches:', len(join_within), 'intersects matches:', len(join_intersects))
print('dup ids within:', join_within['POI_ID'].duplicated().sum(), 'dup ids intersects:', join_intersects['POI_ID'].duplicated().sum())
print('district names:', dist['name'].tolist())

matched = join_within.drop_duplicates(subset=['POI_ID'])
counts = matched['name'].value_counts().to_dict()
counts = {k: int(v) for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))}
result = {"matched_count": int(len(matched)), "district_counts": counts}
with open('result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False, indent=2))

# ─── Observations ───
# points: 1654 within matches: 1651 intersects matches: 1651
# dup ids within: 0 dup ids intersects: 0
# district names: ['锡山区', '惠山区', '滨湖区', '梁溪区', '新吴区', '江阴市', '宜兴市']
# {
#   "matched_count": 1651,
#   "district_counts": {
#     "江阴市": 295,
#     "梁溪区": 270,
#     "宜兴市": 243,
#     "滨湖区": 229,
#     "惠山区": 219,
#     "新吴区": 202,
#     "锡山区": 193
#   }
# }
