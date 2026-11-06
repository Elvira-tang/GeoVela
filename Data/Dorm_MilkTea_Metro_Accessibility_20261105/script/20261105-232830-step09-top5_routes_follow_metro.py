# ─── OpenGIS Agent · run dc6b3e53 · step 9 · top5_routes_follow_metro ───
# Timestamp : 2026-11-05T23:28:30
# Semantic : top5_routes_follow_metro
# Metadata : 20261105-232830-step09-top5_routes_follow_metro.metadata.json
# User query: 📎top5_routes.geojson图层中的直线线路不好看，能否改成沿着地铁线路   --- 📎 **Attached File: `top5_routes.geojson`** Path: `D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Dorm_MilkTea_Metro_Accessibility_20261105\output\top5_rout…
import pandas as pd, geopandas as gpd, networkx as nx, numpy as np
from shapely.geometry import Point, LineString
from pyproj import Geod

geod = Geod(ellps="WGS84")

def hdist(a, b):
    return geod.inv(a[0], a[1], b[0], b[1])[2]

G = nx.read_graphml('data/raw/walking_network.graphml')
nodes = {n: (float(d['longitude']), float(d['latitude'])) for n, d in G.nodes(data=True)}
comp = max(nx.connected_components(G), key=len)
H = G.subgraph(comp).copy()
print('main comp nodes', H.number_of_nodes())
for u, v in H.edges():
    H[u][v]['length'] = hdist(nodes[u], nodes[v])

node_gdf = gpd.GeoDataFrame({'nid': list(comp)}, geometry=[Point(nodes[n]) for n in comp], crs='EPSG:4326').to_crs('EPSG:32651')
_xy = np.column_stack([node_gdf.geometry.x.values, node_gdf.geometry.y.values])
_nids = node_gdf['nid'].values
def snap(pt):
    p = gpd.GeoSeries([Point(pt)], crs='EPSG:4326').to_crs('EPSG:32651').iloc[0]
    dd = np.hypot(_xy[:, 0] - p.x, _xy[:, 1] - p.y)
    i = int(np.argmin(dd))
    return float(dd[i]), _nids[i]

def walk_path(a, b):
    da, na = snap(a); db, nb = snap(b)
    try:
        p = nx.shortest_path(H, na, nb, weight='length')
        coords = [a] + [nodes[n] for n in p] + [b]
        return coords, da, db, False
    except Exception:
        return [a, b], da, db, True

st = pd.read_csv('data/raw/metro_stations.csv').set_index('station_id')
ed = pd.read_csv('data/raw/metro_edges.csv')
M = nx.Graph()
for _, r in ed.iterrows():
    M.add_edge(r.from_station, r.to_station, weight=float(r.travel_time_min))

def metro_path(s1, s2):
    if s1 == s2:
        return []
    p = nx.shortest_path(M, s1, s2, weight='weight')
    return [(st.loc[s, 'longitude'], st.loc[s, 'latitude']) for s in p]

rt = gpd.read_file('output/top5_routes.geojson')
pois = pd.read_csv('data/processed/milktea_wgs84.csv').drop_duplicates('name').set_index('name')
dorms = pd.read_csv('data/processed/dormitories.csv').set_index('宿舍名称')

rows, geoms, falls = [], [], 0
for _, r in rt.iterrows():
    d = (float(dorms.loc[r['dorm'], '经度']), float(dorms.loc[r['dorm'], '纬度']))
    p = (float(pois.loc[r['poi_name'], 'longitude']), float(pois.loc[r['poi_name'], 'latitude']))
    sc = (float(st.loc[r['board'], 'longitude']), float(st.loc[r['board'], 'latitude']))
    ec = (float(st.loc[r['alight'], 'longitude']), float(st.loc[r['alight'], 'latitude']))
    w1, d1, d2, f1 = walk_path(d, sc)
    mp = metro_path(r['board'], r['alight'])
    w2, d3, d4, f2 = walk_path(ec, p)
    falls += int(f1) + int(f2)
    coords = w1 + mp + w2
    rows.append(dict(rank=int(r['rank']), dorm=r['dorm'], poi_name=r['poi_name'], brand=r['brand'],
                     board=r['board'], alight=r['alight'], walk_to_station=r['walk_to_station'],
                     ride_min=r['ride_min'], walk_to_poi=r['walk_to_poi'], total_min=r['total_min'],
                     detail=r['detail'], popup=r['popup'],
                     snap_m=round(max(d1, d2, d3, d4), 1)))
    geoms.append(LineString(coords))

out = gpd.GeoDataFrame(rows, geometry=geoms, crs='EPSG:4326')
out['geom_km'] = (out.geometry.to_crs('EPSG:32651').length / 1000).round(3)
print('fallback walk segments:', falls)
print(out[['rank', 'dorm', 'brand', 'total_min', 'geom_km', 'snap_m']].head(12).to_string())
out.to_file('output/top5_routes_network.geojson', driver='GeoJSON')
print(out.shape)

# ─── Observations ───
# main comp nodes 37942
# 
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 468, in _run_exec
#     compiled = compile(code, "<agent>", "eval")
#   File "<agent>", line 1
#     import pandas as pd, geopandas as gpd, networkx as nx, numpy as np
#     ^^^^^^
# SyntaxError: invalid syntax
# 
# During handling of the above exception, another exception occurred:
# 
# Traceback (most recent call last):
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\indexes\base.py", line 3816, in get_loc
#     return self._engine.get_loc(casted_key)
#            ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
#   File "pandas/_libs/index.pyx", line 172, in pandas._libs.index.IndexEngine.get_loc
#   File "pandas/_libs/index.pyx", line 201, in pandas._libs.index.IndexEngine.get_loc
#   File "pandas/_libs/hashtable_class_helper.pxi", line 7726, in pandas._libs.hashtable.PyObjectHashTable.get_item
#   File "pandas/_libs/hashtable_class_helper.pxi", line 7734, in pandas._libs.hashtable.PyObjectHashTable.get_item
# KeyError: 'poi_id'
# 
# The above exception was the direct cause of the following exception:
# 
# Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 471, in _run_exec
#     exec(compile(code, "<agent>", "exec"), namespace, namespace)
#     ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 53, in <module>
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\series.py", line 1102, in __getitem__
#     return self._get_value(key)
#            ~~~~~~~~~~~~~~~^^^^^
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\series.py", line 1189, in _get_value
#     loc = self.index.get_loc(label)
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\indexes\base.py", line 3823, in get_loc
#     raise KeyError(key) from err
# KeyError: 'poi_id'
# 
# --- stdout before error ---
# main comp nodes 37942
