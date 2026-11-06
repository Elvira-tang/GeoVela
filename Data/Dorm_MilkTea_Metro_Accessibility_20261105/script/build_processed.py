# -*- coding: utf-8 -*-
"""生成 processed 数据：宿舍表、奶茶 WGS84 表、地铁运营参数表、可达性模型参数表。"""
import csv
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
OUT = os.path.join(BASE, "data", "processed")

# 1) 宿舍表
campus = list(csv.DictReader(open(os.path.join(RAW, "jiangnan_university_campus.csv"), encoding="utf-8-sig")))
dorms = [r for r in campus if r["类别"] == "建筑" and ("公寓" in r["名称"] or "宿舍" in r["名称"])]
with open(os.path.join(OUT, "dormitories.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["宿舍名称", "经度", "纬度", "层数", "高度(m)", "面积(m2)", "学生人数", "备注"])
    w.writeheader()
    for r in dorms:
        w.writerow({"宿舍名称": r["名称"], "经度": r["经度"], "纬度": r["纬度"],
                    "层数": r["层数"], "高度(m)": r["高度(m)"], "面积(m2)": r["面积(m2)"],
                    "学生人数": "", "备注": "学生人数待学校数据补充"})
print(f"dormitories: {len(dorms)}")

# 2) 奶茶 WGS84 表
mt = list(csv.DictReader(open(os.path.join(RAW, "wuxi_milktea_poi.csv"), encoding="utf-8-sig")))
with open(os.path.join(OUT, "milktea_wgs84.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["poi_id", "name", "brand", "district", "longitude", "latitude",
                                      "rating", "price_cny", "open_hours"])
    w.writeheader()
    for r in mt:
        w.writerow({"poi_id": r["POI_ID"], "name": r["名称"], "brand": r["品牌"],
                    "district": r["区县"], "longitude": r["经度(WGS84)"], "latitude": r["纬度(WGS84)"],
                    "rating": r["评分"], "price_cny": r["人均消费(元)"], "open_hours": r["营业时间"]})
print(f"milktea_wgs84: {len(mt)}")

# 3) 地铁运营参数（参考值，以无锡地铁官方公告为准）
svc = [
    ("1号线", "06:00", "22:37", 6, 9),
    ("2号线", "05:55", "22:25", 6, 9),
    ("3号线", "06:00", "22:35", 7, 10),
    ("4号线", "06:00", "22:30", 7, 10),
    ("S1号线", "06:00", "22:30", 8, 12),
]
with open(os.path.join(OUT, "metro_service.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["line_id", "first_train", "last_train",
                                      "peak_headway_min", "offpeak_headway_min", "备注"])
    w.writeheader()
    for line, ft, lt, pk, op in svc:
        w.writerow({"line_id": line, "first_train": ft, "last_train": lt,
                    "peak_headway_min": pk, "offpeak_headway_min": op,
                    "备注": "公开资料参考值，以无锡地铁官方公告为准"})
print("metro_service: 5 条线路")

# 4) 可达性模型参数
params = [
    ("walk_speed_m_min", 75, "步行速度"),
    ("station_access_min", 2, "进出站固定时间"),
    ("transfer_walk_min", 3, "站内换乘步行时间（与 metro_edges 换乘边一致）"),
    ("train_speed_km_h", 35, "地铁商业运行速度（travel_time 估算依据）"),
    ("max_walk_to_station_m", 1500, "宿舍-地铁站步行接驳上限"),
]
with open(os.path.join(OUT, "access_params.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["参数", "取值", "说明"])
    w.writeheader()
    for k, v, d in params:
        w.writerow({"参数": k, "取值": v, "说明": d})
print("access_params: 5 项")
