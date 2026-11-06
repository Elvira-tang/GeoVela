# ─── OpenGIS Agent · run 1856dd30 · step 5 · build_point_label_layers ───
# Timestamp : 2026-11-05T23:34:35
# Semantic : build_point_label_layers
# Metadata : 20261105-233435-step05-build_point_label_layers.metadata.json
# User query: 请美化当前“宿舍—地铁—奶茶店TOP5沿路/地铁线路”图层，并在地图上添加宿舍和奶茶店名称。  一、减少路线数量  1. 不要同时展示全部100条路线。 2. 默认每栋宿舍只保留总出行时间最短的1条路线。 3. 另外生成一个“选中宿舍TOP5路线”图层，但默认隐藏。 4. 删除或隐藏现有杂乱的红色路线图层。  二、按照交通方式拆分线路  将完整路线拆成三个图层，不要全部使用红色：  1. 宿舍到上…
import pandas as pd, geopandas as gpd, numpy as np, os
from shapely.geometry import Point, LineString, MultiLineString
from pyproj import Geod
geod = Geod(ellps='WGS84')
OUT = 'output/beautify'
ar = pd.read_csv('data/processed/accessibility_results.csv', encoding='utf-8-sig')
pois = pd.read_csv('data/processed/milktea_wgs84.csv', encoding='utf-8-sig')
poi_xy = pois.drop_duplicates('name').set_index('name')[['longitude','latitude']]
dorms = pd.read_csv('data/processed/dormitories.csv', encoding='utf-8-sig').set_index('宿舍名称')
st = pd.read_csv('data/raw/metro_stations.csv', encoding='utf-8-sig').set_index('station_id')
best = ar.sort_values('total_min').groupby('dorm').first().reset_index()

def short_dorm(n):
    return n.replace('江南大学蠡湖校区','')

def short_poi(n):
    return n.replace('((', '(').replace('))', ')')

walk = gpd.read_file(f'{OUT}/routes_walk_board.geojson')
walkp = gpd.read_file(f'{OUT}/routes_walk_poi.geojson')
poi_list = sorted(set(walk.poi_name))

drows = []
for d, r in best.set_index('dorm').iterrows():
    drows.append(dict(name=d, label=short_dorm(d), total_min=float(r['total_min']),
                      walk_min=round(float(r['walk_to_station_min'])+float(r['walk_to_poi_min']),1),
                      ride_min=float(r['ride_min']), board=f"{st.loc[r['board_station'],'station_name']}({r['board_station']})",
                      alight=f"{st.loc[r['alight_station'],'station_name']}({r['alight_station']})",
                      transfers=int(r.get('transfers', 0)) if not pd.isna(r.get('transfers', np.nan)) else 0,
                      poi_name=r['poi_name'],
                      popup=f"<b>{d}</b><br>最近奶茶店: {r['poi_name']}<br>总出行时间: {r['total_min']} 分钟"
                            f"<br>步行时间: {round(float(r['walk_to_station_min'])+float(r['walk_to_poi_min']),1)} 分钟"
                            f"<br>地铁乘车时间: {r['ride_min']} 分钟<br>上车站: {st.loc[r['board_station'],'station_name']}({r['board_station']})"
                            f"<br>下车站: {st.loc[r['alight_station'],'station_name']}({r['alight_station']})<br>换乘次数: {0}",
                      geometry=Point(float(dorms.loc[d,'经度']), float(dorms.loc[d,'纬度']))))
gd = gpd.GeoDataFrame(drows, crs='EPSG:4326')

prows = []
for p in poi_list:
    recs = best[best.poi_name == p]
    prows.append(dict(name=p, label=short_poi(p), brand=recs['brand'].iloc[0],
                      n_dorm=len(recs), best_min=float(recs['total_min'].min()),
                      popup=f"<b>{p}</b><br>品牌: {recs['brand'].iloc[0]}<br>服务宿舍数: {len(recs)}"
                            f"<br>最快总出行时间: {recs['total_min'].min()} 分钟",
                      geometry=Point(float(poi_xy.loc[p,'longitude']), float(poi_xy.loc[p,'latitude']))))
gp = gpd.GeoDataFrame(prows, crs='EPSG:4326')

cx, cy = gd.geometry.x.mean(), gd.geometry.y.mean()
srows = []
for sid, s in st.iterrows():
    dist = geod.inv(cx, cy, float(s['longitude']), float(s['latitude']))[2] / 1000
    if dist <= 2.5:
        srows.append(dict(station_id=sid, station_name=s['station_name'], line_id=s['line_id'],
                          stop_type=s.get('stop_type',''), dist_km=round(dist,2),
                          popup=f"<b>{s['station_name']}</b><br>编号: {sid}<br>线路: {s['line_id']}<br>距校园: {dist:.2f} km",
                          geometry=Point(float(s['longitude']), float(s['latitude']))))
gs = gpd.GeoDataFrame(srows, crs='EPSG:4326')

def offset(g, dx=0.00007, dy=0.00005):
    return gpd.GeoDataFrame(g.drop(columns='geometry'), geometry=[Point(p.x+dx, p.y+dy) for p in g.geometry], crs='EPSG:4326')

gd.to_file(f'{OUT}/nodes_dorm.geojson', driver='GeoJSON')
gp.to_file(f'{OUT}/nodes_poi.geojson', driver='GeoJSON')
gs.to_file(f'{OUT}/nodes_metro_stations.geojson', driver='GeoJSON')
offset(gd).to_file(f'{OUT}/labels_dorm.geojson', driver='GeoJSON')
offset(gp).to_file(f'{OUT}/labels_poi.geojson', driver='GeoJSON')

t5w = gpd.read_file(f'{OUT}/selected_top5_walk_board.geojson')
t5p = gpd.read_file(f'{OUT}/selected_top5_walk_poi.geojson')
t5m = gpd.read_file(f'{OUT}/selected_top5_metro_ride.geojson')
keys = ['name','dorm','poi_name','total_min','walk_min','ride_min','board','alight','transfers','popup']
rows = []
for _, r in t5w.iterrows():
    parts = [LineString(r.geometry.coords)]
    for g in t5m[t5m['name'] == r['name']].geometry:
        parts.append(LineString(g.coords))
    seg = t5p[t5p['name'] == r['name']]
    if len(seg):
        parts.append(LineString(seg.geometry.iloc[0].coords))
    rec = {k: r[k] for k in keys}
    rec['geometry'] = MultiLineString(parts)
    rows.append(rec)
t5 = gpd.GeoDataFrame(rows, crs='EPSG:4326')
t5.to_file(f'{OUT}/selected_top5_full_routes.geojson', driver='GeoJSON')
print('dorm', len(gd), 'poi', len(gp), 'stations', len(gs), 'top5 lines', len(t5))
print(gp[['name','label','best_min']].to_string())
print(gs[['station_id','station_name','line_id','dist_km']].to_string())

# ─── Observations ───
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 468, in _run_exec
#     compiled = compile(code, "<agent>", "eval")
#   File "<agent>", line 1
#     import pandas as pd, geopandas as gpd, numpy as np, os
#     ^^^^^^
# SyntaxError: invalid syntax
# 
# During handling of the above exception, another exception occurred:
# 
# Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 471, in _run_exec
#     exec(compile(code, "<agent>", "exec"), namespace, namespace)
#     ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 73, in <module>
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\geopandas\geodataframe.py", line 246, in __init__
#     self.set_geometry(geometry, inplace=True, crs=crs)
#     ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\geopandas\geodataframe.py", line 482, in set_geometry
#     frame[geo_column_name] = level
#     ~~~~~^^^^^^^^^^^^^^^^^
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\geopandas\geodataframe.py", line 2011, in __setitem__
#     super().__setitem__(key, value)
#     ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\frame.py", line 4659, in __setitem__
#     self._set_item(key, value)
#     ~~~~~~~~~~~~~~^^^^^^^^^^^^
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\frame.py", line 4895, in _set_item
#     value, refs = self._sanitize_column(value)
#                   ~~~~~~~~~~~~~~~~~~~~~^^^^^^^
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\frame.py", line 6406, in _sanitize_column
#     com.require_length_match(value, self.index)
#     ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\common.py", line 612, in require_length_match
#     raise ValueError(
#     ...<4 lines>...
#     )
# ValueError: Length of values (15) does not match length of index (5)
# 
# --- stdout before error ---
