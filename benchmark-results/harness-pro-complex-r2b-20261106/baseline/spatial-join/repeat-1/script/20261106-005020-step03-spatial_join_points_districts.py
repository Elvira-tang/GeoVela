# ─── OpenGIS Agent · run b8d32716 · step 3 · spatial_join_points_districts ───
# Timestamp : 2026-11-06T00:50:20
# Semantic : spatial_join_points_districts
# Metadata : 20261106-005020-step03-spatial_join_points_districts.metadata.json
# User query: Load points.csv using the WGS84 longitude/latitude columns and spatially join the points to districts.geojson. Write result.json with matched_count and district_counts keyed by polygon name. Exclude u…
import pandas as pd, geopandas as gpd, json

df = pd.read_csv('points.csv')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['经度(WGS84)'], df['纬度(WGS84)']), crs='EPSG:4326')
dist = gpd.read_file('districts.geojson').to_crs('EPSG:4326')
dist['geometry'] = dist.geometry.buffer(0)

joined = gpd.sjoin(gdf, dist[['name', 'geometry']], how='left', predicate='within')
matched = joined[joined['name'].notna()].copy()

counts = matched['name'].value_counts().sort_index()
result = {
    'matched_count': int(len(matched)),
    'district_counts': {str(k): int(v) for k, v in counts.items()},
}
with open('result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

matched.drop(columns='geometry').to_csv('matched_points.csv', index=False, encoding='utf-8-sig')
print(json.dumps(result, ensure_ascii=False, indent=2))
print('total points:', len(df), 'unmatched:', len(df) - len(matched))
print('sum(counts):', sum(result['district_counts'].values()))

# verification pass: independent re-read of inputs, point-in-polygon check
chk = json.load(open('result.json', encoding='utf-8'))
d2 = gpd.read_file('districts.geojson').to_crs('EPSG:4326')
p2 = pd.read_csv('points.csv')
pts = gpd.GeoDataFrame(p2, geometry=gpd.points_from_xy(p2['经度(WGS84)'], p2['纬度(WGS84)']), crs='EPSG:4326')
res = []
for i, row in pts.iterrows():
    hit = d2[d2.geometry.apply(lambda geom: geom.contains(row.geometry))]
    if len(hit):
        res.append(hit.iloc[0]['name'])
vc = pd.Series(res).value_counts().sort_index()
print('verify matched:', len(res))
print('verify matches file:', {str(k): int(v) for k, v in vc.items()} == chk['district_counts'], len(res) == chk['matched_count'])
print('verify sum:', sum(chk['district_counts'].values()) == chk['matched_count'])

# ─── Observations ───
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
# total points: 1654 unmatched: 3
# sum(counts): 1651
# verify matched: 1651
# verify matches file: True True
# verify sum: True
