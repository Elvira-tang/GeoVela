# ─── OpenGIS Agent · run 046b24f7 · step 4 · beautify_offset_label_layers ───
# Timestamp : 2026-11-05T23:37:22
# Semantic : beautify_offset_label_layers
# Metadata : 20261105-233722-step04-beautify_offset_label_layers.metadata.json
# User query: 请美化当前“宿舍—地铁—奶茶店TOP5沿路/地铁线路”图层，并在地图上添加宿舍和奶茶店名称。  一、减少路线数量  1. 不要同时展示全部100条路线。 2. 默认每栋宿舍只保留总出行时间最短的1条路线。 3. 另外生成一个“选中宿舍TOP5路线”图层，但默认隐藏。 4. 删除或隐藏现有杂乱的红色路线图层。  二、按照交通方式拆分线路  将完整路线拆成三个图层，不要全部使用红色：  1. 宿舍到上…
import geopandas as gpd
from shapely.geometry import Point
base = r"D:\Study\大三\申威高级语言编译与程序设计\GIS\GeoVela\Data\Dorm_MilkTea_Metro_Accessibility_20261105\output\beautify"
dx, dy = 18.0, 14.0
for src, dst in [("labels_dorm.geojson", "labels_dorm_offset.geojson"), ("labels_poi.geojson", "labels_poi_offset.geojson")]:
    g = gpd.read_file(base + "\\" + src)
    g = g.to_crs(32651)
    g["geometry"] = g.geometry.apply(lambda p: Point(p.x + dx, p.y + dy))
    g = g.to_crs(4326)
    g.to_file(base + "\\" + dst, driver="GeoJSON")
    print(dst, len(g), list(g.columns))

res = list_layers()
for l in res["layers"]:
    print(l["layer_id"], "|", l["name"], "|", l["visible"], "|", l["feature_count"])

# ─── Observations ───
# labels_dorm_offset.geojson 20 ['name', 'label', 'total_min', 'walk_min', 'ride_min', 'board', 'alight', 'transfers', 'poi_name', 'popup', 'geometry']
# labels_poi_offset.geojson 1 ['name', 'label', 'brand', 'n_dorm', 'best_min', 'popup', 'geometry']
# milktea_poi | 参与计算奶茶店(275) | True | 275
# metro_stations | 无锡地铁站点(98) | True | 98
# dorm_access | 宿舍奶茶可达性分级 | True | 20
# ccabf668-1f63-4689-bb50-97436460ab47 | dorm_accessibility_summary | True | 20
# 04c082bd-1ad3-426f-b3d0-4ef13da14ef8 | dorm_accessibility_summary | True | 20
# 1e7de375-158f-489a-bc29-80616568855c | metro_stations | True | 98
# f1305de5-d136-4f91-aedf-e714ab08d703 | reachable_milktea | True | 275
# poi_grade | 奶茶店可达性分级(275) | True | 275
# cd2a1c21-8e7d-45c1-97ca-b068dc0fc9f0 | dorm_accessibility_summary | True | 20
# 4be0d4ea-e78e-4dcd-8edd-7ee7c73a546b | dorm_accessibility_summary | True | 20
# 85b55178-9fa2-4db5-9464-480840daf292 | metro_stations | True | 98
# f1b3dbdf-ba13-4672-a1d1-44554eb5a068 | poi_accessibility_grades | True | 275
# e7be9a13-dd84-4367-8a82-fbd57784bd7b | reachable_milktea | True | 275
# top5_routes_network | 宿舍→奶茶店 TOP5 沿路网/地铁线路 | False | 100
# beautify_metro_ride | 地铁乘车段 | True | 7
# beautify_walk_board | 宿舍到地铁站步行 | True | 20
# beautify_walk_poi | 地铁站到奶茶店步行 | True | 20
# beautify_stations | 地铁站 | True | 3
# beautify_poi | 奶茶店 | True | 1
# beautify_dorm | 宿舍点 | True | 20
