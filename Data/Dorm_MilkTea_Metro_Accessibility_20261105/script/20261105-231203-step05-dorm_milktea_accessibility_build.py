# ─── OpenGIS Agent · run ede2c20a · step 5 · dorm_milktea_accessibility_build ───
# Timestamp : 2026-11-05T23:12:03
# Semantic : dorm_milktea_accessibility_build
# Metadata : 20261105-231203-step05-dorm_milktea_accessibility_build.metadata.json
# User query: 📎dormitories.csv 📎metro_station_entrances.csv 📎milktea_wgs84.csv 📎accessibility_results.csv请对江南大学学生宿舍—无锡地铁—奶茶店数据进行可达性分析。  请读取以下数据：  1. data/processed/dormitories.csv    作为出发点，表示江南大学学生宿舍。  2. data/raw/…
import pandas as pd, numpy as np, json, os
import geopandas as gpd
from shapely.geometry import Point, LineString

base = r"D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Dorm_MilkTea_Metro_Accessibility_20261105"
out = os.path.join(base, "output"); os.makedirs(out, exist_ok=True)

acc  = pd.read_csv(os.path.join(base, "data/processed/accessibility_results.csv"))
dorm = pd.read_csv(os.path.join(base, "data/processed/dormitories.csv")).rename(
    columns={"宿舍名称": "dorm", "经度": "lon", "纬度": "lat"})
mtea = pd.read_csv(os.path.join(base, "data/processed/milktea_wgs84.csv"))
stn  = pd.read_csv(os.path.join(base, "data/raw/metro_stations.csv"))

sdf = pd.read_csv(os.path.join(out, "dorm_accessibility_summary.csv"))

# 1) 宿舍点
geom = [Point(x, y) for x, y in zip(sdf["lon"], sdf["lat"])]
gd = gpd.GeoDataFrame(sdf.copy(), geometry=geom, crs="EPSG:4326")
gd["label"] = gd.apply(lambda r: f"{r['dorm']}\n45min可达 {int(r['n45'])} 家", axis=1)
gd.to_file(os.path.join(out, "dorm_accessibility_summary.geojson"), driver="GeoJSON", encoding="utf-8")

# 2) 地铁站点
gs = gpd.GeoDataFrame(stn.copy(), geometry=[Point(x, y) for x, y in zip(stn.longitude, stn.latitude)],
                      crs="EPSG:4326")
gs["stop_type"] = np.where(gs["is_transfer"] == 1, "换乘站", "普通站")
gs.to_file(os.path.join(out, "metro_stations.geojson"), driver="GeoJSON", encoding="utf-8")

# 3) 参与计算奶茶店（275）到达时间统计
poi_join = mtea.set_index("poi_id")[["longitude", "latitude"]]
best = acc.groupby("poi_id")["total_min"].min().rename("best_min")
n45 = acc[acc.total_min <= 45].groupby("poi_id").size().rename("n_dorm_45")
n_dorm = acc.groupby("poi_id").size().rename("n_dorm_all")
st = pd.concat([best, n45, n_dorm], axis=1).fillna({"n_dorm_45": 0})
st = st.join(acc.drop_duplicates("poi_id").set_index("poi_id")[["poi_name", "brand"]])
st = st.join(poi_join, how="left")
gp = gpd.GeoDataFrame(st.reset_index(), geometry=[Point(x, y) for x, y in zip(st["longitude"], st["latitude"])],
                      crs="EPSG:4326")
gp["popup"] = gp.apply(lambda r: f"{r['poi_name']}（{r['brand']}）<br>最短到达 {r['best_min']} 分钟<br>45分钟内可达宿舍 {int(r['n_dorm_45'])}/20 栋", axis=1)
gp.to_file(os.path.join(out, "reachable_milktea.geojson"), driver="GeoJSON", encoding="utf-8")
print("milk tea:", len(gp), "missing coord:", gp["longitude"].isna().sum())

# 4) Top5 线路
station_xy = stn.set_index("station_id")[["longitude", "latitude"]]
station_name = stn.set_index("station_id")["station_name"].to_dict()
dxy = sdf.set_index("dorm")[["lon", "lat"]]
rows = []
for d, sub in acc.groupby("dorm"):
    top = sub.nsmallest(5, "total_min")
    for rank, (_, r) in enumerate(top.iterrows(), 1):
        bx, by = dxy.loc[d, "lon"], dxy.loc[d, "lat"]
        sx, sy = station_xy.loc[r["board_station"]]
        ex, ey = station_xy.loc[r["alight_station"]]
        px, py = gp.set_index("poi_id").loc[r["poi_id"], ["longitude", "latitude"]]
        rows.append({
            "dorm": d, "rank": rank, "poi_name": r["poi_name"], "brand": r["brand"],
            "board": r["board_station"], "alight": r["alight_station"],
            "walk_to_station": r["walk_to_station_min"], "ride_min": r["ride_min"],
            "walk_to_poi": r["walk_to_poi_min"], "total_min": r["total_min"],
            "detail": r["detail"],
            "popup": (f"<b>{d}</b> → {r['poi_name']}<br>{r['detail']}<br>"
                      f"总时长 {r['total_min']} 分钟<br>进站步行 {r['walk_to_station_min']} + 乘车 {r['ride_min']} "
                      f"+ 出站步行 {r['walk_to_poi_min']}"),
            "geometry": LineString([(bx, by), (sx, sy), (ex, ey), (px, py)]),
        })
rt = gpd.GeoDataFrame(rows, crs="EPSG:4326")
rt.to_file(os.path.join(out, "top5_routes.geojson"), driver="GeoJSON", encoding="utf-8")
print("route features:", len(rt))

# 5) 站点受益统计
alight_cnt = acc[acc.total_min <= 45].groupby("alight_station")["dorm"].nunique().sort_values(ascending=False)
board_cnt = acc.groupby("board_station")["dorm"].nunique().sort_values(ascending=False)
print("board:", board_cnt.head(5).to_dict())
print("alight(≤45min dorm count):", alight_cnt.head(8).to_dict())
print(gs["stop_type"].value_counts().to_dict())

# ─── Observations ───
# milk tea: 275 missing coord: 0
# 
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 468, in _run_exec
#     compiled = compile(code, "<agent>", "eval")
#   File "<agent>", line 1
#     import pandas as pd, numpy as np, json, os
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
#   File "pandas/_libs/index.pyx", line 196, in pandas._libs.index.IndexEngine.get_loc
#   File "pandas/_libs/index.pyx", line 643, in pandas._libs.index.ObjectEngine._get_loc_duplicates
#   File "pandas/_libs/index.pyx", line 247, in pandas._libs.index.IndexEngine._maybe_get_bool_indexer
#   File "pandas/_libs/index.pyx", line 139, in pandas._libs.index._unpack_bool_indexer
# KeyError: 'S023'
# 
# The above exception was the direct cause of the following exception:
# 
# Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 471, in _run_exec
#     exec(compile(code, "<agent>", "exec"), namespace, namespace)
#     ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 50, in <module>
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\indexing.py", line 1342, in __getitem__
#     return self._getitem_axis(maybe_callable, axis=axis)
#            ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\indexing.py", line 1966, in _getitem_axis
#     return self._get_label(key, axis=axis)
#            ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\indexing.py", line 1884, in _get_label
#     return self.obj.xs(label, axis=axis)
#            ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\generic.py", line 4291, in xs
#     loc = index.get_loc(key)
#   File "C:\Users\Elvira\AppData\Roaming\geovela\venv\Lib\site-packages\pandas\core\indexes\base.py", line 3823, in get_loc
#     raise KeyError(key) from err
# KeyError: 'S023'
# 
# --- stdout before error ---
# milk tea: 275 missing coord: 0
