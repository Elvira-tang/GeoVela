# 江南大学宿舍—地铁—奶茶可达性数据集

采集日期：2026-11-05
坐标系：WGS84（奶茶数据由高德 GCJ-02 转换而来）
用途：以江南大学宿舍为起点、地铁为骨干、奶茶店为终点的可达性分析。

## 目录结构

```
Dorm_MilkTea_Metro_Accessibility_20261105/
├─ data/
│  ├─ raw/                        # 原始数据（源文件复制 + 接口采集，不做修改）
│  │  ├─ jiangnan_university_campus.csv   # 校园要素（234 行，含建筑高度/层数估算）
│  │  ├─ wuxi_milktea_poi.csv             # 无锡奶茶店 POI（1654 家，高德）
│  │  ├─ metro_stations.csv               # 地铁站点表（98 站）
│  │  ├─ metro_edges.csv                  # 相邻站关系表（101 条，含 8 条换乘边）
│  │  ├─ metro_station_entrances.csv      # 地铁出入口表（176 个）
│  │  ├─ walking_nodes.csv                # 步行网络节点
│  │  ├─ walking_edges.csv                # 步行网络边
│  │  └─ walking_network.graphml          # 步行网络（GraphML，可直接读入 networkx）
│  └─ processed/                  # 筛选、坐标统一与参数
│     ├─ dormitories.csv          # 宿舍表（20 栋，学生人数待补）
│     ├─ milktea_wgs84.csv        # 奶茶店 WGS84 坐标表（1654 家）
│     ├─ metro_service.csv        # 运营时段与发车间隔（参考值）
│     └─ access_params.csv        # 可达性模型参数
├─ script/                        # 采集与处理脚本
├─ output/                        # 计算结果输出
└─ figures/                       # 图表输出
```

## 数据说明

### metro_stations.csv
station_id, station_name, line_id, longitude, latitude, is_transfer
- 覆盖无锡地铁 1 号线(27)、2 号线(22)、3 号线(21)、4 号线(18)、S1 号线(10)，共 98 站
- 换乘站：堰桥(1/S1)、刘潭(1/4)、无锡火车站(1/3)、三阳广场(1/2)、市民中心(1/4)、河埒口(2/4)、靖海(2/3)、盛岸(3/4)
- 来源：OpenStreetMap（Overpass API），route=subway 关系 + subway=yes 节点补充

### metro_edges.csv
from_station, to_station, line_id, travel_time_min, distance_m, direction
- 相邻站边 93 条 + 站内换乘边 8 条（换乘步行 3.0 min，固定值）
- distance_m 为相邻站球面直线距离；travel_time_min = distance / 35km/h（估算值，未含加减速差异）
- direction 为该方向的终点站名；换乘边 direction = 站内换乘

### metro_station_entrances.csv
entrance_id, station_id, entrance_name, longitude, latitude
- 176 个出入口，关联到 450 m 内最近站点；步行接驳应以出入口为终点而非站点中心

### walking_nodes.csv / walking_edges.csv / walking_network.graphml
- 范围：滨湖区（约 31.42–31.58°N, 120.19–120.34°E），覆盖江南大学校园内部道路、周边地铁站（江南大学/长广溪/市民中心等）与区内奶茶店
- highway 类型：footway, pedestrian, path, steps, residential, service, unclassified, tertiary, secondary, living_street, cycleway
- 边长为节点间球面距离；graphml 为无向图，节点含经纬度，边含 length_m/highway/name

### processed/metro_service.csv 与 access_params.csv
- 首末班与发车间隔为公开资料参考值，正式分析前请以无锡地铁官方公告核对
- 参数：步行 75 m/min、进出站固定 2 min、换乘步行 3 min、列车商业速度 35 km/h、接驳上限 2500 m（校园南北约 2 km）

## 可达性结果（processed）

| 文件 | 行数 | 说明 |
|---|---|---|
| dorm_station_access.csv | 45 | 20 栋宿舍 × 4 个可达站（江南大学/长广溪/文化宫/雪浪），含到最近出入口的步行距离与时间 |
| station_milktea_access.csv | 5850 | 25 个站到 277 家可达奶茶店的出站步行距离/时间 |
| accessibility_results.csv | 5500 | 20 栋宿舍 × 275 家奶茶店的最优全程时间，含上车/下车站在 |

模型：全程 = 宿舍→出入口步行 + 进站固定 2 min + 乘车（含换乘 3 min/次） + 出站固定 2 min + 出入口→奶茶店步行。

初步结论（供参考）：
- 全程中位数 58.8 min，最快 16.6 min（瀚苑公寓 → 蜜雪冰城星光广场店，长广溪上车、江南大学出站）
- 宿舍步行到站中位数 17.3 min，最长 24.1 min（北区公寓）
- 乘车段中位数 19.3 min

## 脚本

- `script/collect_metro.py`：地铁站点/相邻站/出入口采集（Overpass）
- `script/patch_line2_termini.py`：2 号线终点站补丁（OSM relation 成员缺失时）
- `script/collect_walking.py`：步行网络采集（3×3 瓦片、失败四分递归、断点续跑）与 graphml 生成
- `script/build_processed.py`：processed 基础表生成
- `script/build_access.py`：三张可达性表计算（Dijkstra / 多源 Dijkstra）

## 已知局限

- 地铁 travel_time 为估算值（匀速 35 km/h、直线距离），非官方时刻表
- 奶茶 POI 的高德「冷饮店」分类单查询上限 200 条/区，个别门店可能遗漏
- 步行网络覆盖 31.44–31.56°N / 120.22–120.34°E，1654 家奶茶店中仅 277 家落在此范围（含 250 m 吸附），框外门店未参与可达性计算
- 地铁运营时段/发车间隔为公开资料参考值，需与官方核对
- 校园建筑高度/层数为按类型估算，备注列有标注
- 宿舍学生人数暂无数据，`dormitories.csv` 该列为空
