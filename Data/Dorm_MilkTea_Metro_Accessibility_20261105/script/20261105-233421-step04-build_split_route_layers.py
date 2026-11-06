# ─── OpenGIS Agent · run 1856dd30 · step 4 · build_split_route_layers ───
# Timestamp : 2026-11-05T23:34:21
# Semantic : build_split_route_layers
# Metadata : 20261105-233421-step04-build_split_route_layers.metadata.json
# User query: 请美化当前“宿舍—地铁—奶茶店TOP5沿路/地铁线路”图层，并在地图上添加宿舍和奶茶店名称。  一、减少路线数量  1. 不要同时展示全部100条路线。 2. 默认每栋宿舍只保留总出行时间最短的1条路线。 3. 另外生成一个“选中宿舍TOP5路线”图层，但默认隐藏。 4. 删除或隐藏现有杂乱的红色路线图层。  二、按照交通方式拆分线路  将完整路线拆成三个图层，不要全部使用红色：  1. 宿舍到上…
import pandas as pd, geopandas as gpd, networkx as nx, numpy as np, os
from shapely.geometry import Point, LineString
from pyproj import Geod

geod = Geod(ellps="WGS84")
OUT = 'output/beautify'
os.makedirs(OUT, exist_ok=True)

ar = pd.read_csv('data/processed/accessibility_results.csv', encoding='utf-8-sig')
pois = pd.read_csv('data/processed/milktea_wgs84.csv', encoding='utf-8-sig')
poi_xy = pois.drop_duplicates('name').set_index('name')[['longitude', 'latitude']]
dorms = pd.read_csv('data/processed/dormitories.csv', encoding='utf-8-sig').set_index('宿舍名称')
st = pd.read_csv('data/raw/metro_stations.csv', encoding='utf-8-sig').set_index('station_id')
ed = pd.read_csv('data/raw/metro_edges.csv', encoding='utf-8-sig')

G = nx.read_graphml('data/raw/walking_network.graphml')
nodes = {n: (float(d['longitude']), float(d['latitude'])) for n, d in G.nodes(data=True)}
comp = max(nx.connected_components(G), key=len)
H = G.subgraph(comp).copy()
for u, v in H.edges():
    H[u][v]['length'] = geod.inv(nodes[u][0], nodes[u][1], nodes[v][0], nodes[v][1])[2]

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
        return [a] + [nodes[n] for n in p] + [b], max(da, db), False
    except Exception:
        return [a, b], max(da, db), True

M = nx.Graph()
edge_line = {}
for _, r in ed.iterrows():
    M.add_edge(r.from_station, r.to_station, weight=float(r.travel_time_min))
    edge_line[(r.from_station, r.to_station)] = r.line_id
    edge_line.setdefault((r.to_station, r.from_station), r.line_id)

def metro_segments(s1, s2):
    if s1 == s2:
        return [], []
    seq = nx.shortest_path(M, s1, s2, weight='weight')
    segs = []
    for a, b in zip(seq[:-1], seq[1:]):
        ln = edge_line.get((a, b), '未知')
        cs = [(float(st.loc[a, 'longitude']), float(st.loc[a, 'latitude'])),
              (float(st.loc[b, 'longitude']), float(st.loc[b, 'latitude']))]
        if segs and segs[-1]['line'] == ln:
            segs[-1]['coords'].extend(cs[1:])
        else:
            segs.append({'line': ln, 'coords': cs})
    return segs, seq

def sname(sid):
    return f"{st.loc[sid,'station_name']}({sid})"

def build_routes(df, tag):
    walkA, walkB, rides, stats = [], [], [], {'fallback': 0, 'stations': set()}
    for _, r in df.iterrows():
        d = (float(dorms.loc[r['dorm'], '经度']), float(dorms.loc[r['dorm'], '纬度']))
        p = (float(poi_xy.loc[r['poi_name'], 'longitude']), float(poi_xy.loc[r['poi_name'], 'latitude']))
        sb, sa = r['board_station'], r['alight_station']
        sc = (float(st.loc[sb, 'longitude']), float(st.loc[sb, 'latitude']))
        ac = (float(st.loc[sa, 'longitude']), float(st.loc[sa, 'latitude']))

        c1, snap1, f1 = walk_path(d, sc)
        c2, snap2, f2 = walk_path(ac, p)
        stats['fallback'] += int(f1) + int(f2)

        segs, seq = metro_segments(sb, sa)
        stats['stations'].update(seq)
        transfers = max(0, len({s['line'] for s in segs}) - 1)
        walk_min = round(float(r['walk_to_station_min']) + float(r['walk_to_poi_min']), 1)
        popup = (f"<b>{r['dorm']}</b> → {r['poi_name']}<br>总出行时间: {r['total_min']} 分钟"
                 f"<br>步行时间: {walk_min} 分钟<br>地铁乘车时间: {r['ride_min']} 分钟"
                 f"<br>上车站: {sname(sb)}<br>下车站: {sname(sa)}<br>换乘次数: {transfers}")
        base = dict(name=f"{r['dorm']}→{r['poi_name']}", dorm=r['dorm'], poi_name=r['poi_name'],
                    brand=r['brand'], total_min=float(r['total_min']), walk_min=walk_min,
                    ride_min=float(r['ride_min']), board=sname(sb), alight=sname(sa),
                    transfers=int(transfers), popup=popup, snap_m=round(max(snap1, snap2), 1))
        walkA.append({**base, 'geometry': LineString(c1)})
        walkB.append({**base, 'geometry': LineString(c2)})
        for s in segs:
            rides.append({**base, 'line_id': s['line'],
                          'note': '示意线路：按 metro_edges.csv 相邻站点顺序的分段折线',
                          'geometry': LineString(s['coords'])})

    ga = gpd.GeoDataFrame(walkA, crs='EPSG:4326')
    gb = gpd.GeoDataFrame(walkB, crs='EPSG:4326')
    gr = gpd.GeoDataFrame(rides, crs='EPSG:4326')
    ga.to_file(f'{OUT}/{tag}_walk_board.geojson', driver='GeoJSON')
    gb.to_file(f'{OUT}/{tag}_walk_poi.geojson', driver='GeoJSON')
    if len(gr):
        gr.to_file(f'{OUT}/{tag}_metro_ride.geojson', driver='GeoJSON')
    print(tag, 'routes', len(df), 'walk_board', len(ga), 'walk_poi', len(gb), 'ride_segs', len(gr),
          'fallback', stats['fallback'], 'max_snap_m', round(max(ga.snap_m.max(), gb.snap_m.max()), 1))
    return ga, gb, gr, stats

best = ar.sort_values('total_min').groupby('dorm').first().reset_index()
ga, gb, gr, stats = build_routes(best, 'routes')

sel_dorm = best.sort_values('total_min').iloc[0]['dorm']
top5 = ar[ar.dorm == sel_dorm].sort_values('total_min').head(5)
build_routes(top5, 'selected_top5')
print('selected dorm:', sel_dorm)
print('ride segs by line:', gr['line_id'].value_counts().to_dict() if len(gr) else {})
print('used stations:', sorted(stats['stations']))
ga2 = gpd.read_file(f'{OUT}/routes_walk_board.geojson')
print(ga2[['dorm','poi_name','total_min','transfers','snap_m']].to_string())

# ─── Observations ───
# routes routes 20 walk_board 20 walk_poi 20 ride_segs 7 fallback 0 max_snap_m 94.0
# selected_top5 routes 5 walk_board 5 walk_poi 5 ride_segs 5 fallback 0 max_snap_m 103.5
# selected dorm: 江南大学蠡湖校区瀚苑公寓
# ride segs by line: {'1号线': 7}
# used stations: ['S023', 'S024']
#             dorm               poi_name  total_min  transfers  snap_m
# 0   江南大学蠡湖校区李园公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       26.5          0    79.5
# 1   江南大学蠡湖校区杏园公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       25.2          0    30.3
# 2   江南大学蠡湖校区桂园公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       29.6          0    86.0
# 3   江南大学蠡湖校区桃园公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       29.4          0    94.0
# 4   江南大学蠡湖校区桔园公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       26.5          0    91.4
# 5   江南大学蠡湖校区梅园公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       25.8          0    48.8
# 6   江南大学蠡湖校区榴园公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       29.3          0    74.3
# 7   江南大学蠡湖校区橙园公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       29.4          0    69.5
# 8   江南大学蠡湖校区浩苑公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       17.7          0    47.7
# 9   江南大学蠡湖校区涓苑公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       24.4          0    67.0
# 10  江南大学蠡湖校区清苑公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       22.6          0    67.0
# 11  江南大学蠡湖校区溪苑公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       23.4          0    63.3
# 12  江南大学蠡湖校区澈苑公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       20.6          0    67.0
# 13  江南大学蠡湖校区瀚苑公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       16.6          0    67.0
# 14  江南大学蠡湖校区鸿苑公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       19.4          0    22.1
# 15          浩苑公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       22.4          0    79.1
# 16       涓苑公寓臻善楼  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       24.4          0    72.5
# 17         留学生公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       17.1          0    67.0
# 18          青教公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       22.8          0    32.6
# 19          鸿园公寓  蜜雪冰城((星光广场店/张亮麻辣烫隔壁))       25.2          0    31.2
