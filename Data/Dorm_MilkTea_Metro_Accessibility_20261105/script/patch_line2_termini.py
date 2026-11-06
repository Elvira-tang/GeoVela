# -*- coding: utf-8 -*-
"""轻量补丁：为2号线补 梅园开原寺/安镇 两个终点站，并更新相关边。
只发一个小型节点查询，避免再次全量拉取 relation。
"""
import csv
import json
import math
import os
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")

MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

Q = """[out:json][timeout:100];
node["railway"~"^(station|halt|stop)$"]["name"~"梅园开原寺|安镇"](31.30,119.95,31.75,120.55);
out body;"""


def overpass(query):
    for attempt in range(8):
        mirror = MIRRORS[attempt % len(MIRRORS)]
        try:
            data = urllib.parse.urlencode({"data": query}).encode()
            req = urllib.request.Request(mirror, data=data,
                                         headers={"User-Agent": "wuxi-metro-patch/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  retry {attempt}: {type(e).__name__} {str(e)[:60]}", flush=True)
            time.sleep(8 + attempt * 4)
    raise SystemExit("Overpass 均不可用")


def hav(lon1, lat1, lon2, lat2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def norm(name):
    return name[:-1] if name.endswith("站") and len(name) > 2 else name


stations = list(csv.DictReader(open(os.path.join(RAW, "metro_stations.csv"), encoding="utf-8-sig")))
edges = list(csv.DictReader(open(os.path.join(RAW, "metro_edges.csv"), encoding="utf-8-sig")))

data = overpass(Q)
found = {}
for el in data["elements"]:
    n = norm(el.get("tags", {}).get("name") or "")
    if n in ("梅园开原寺", "安镇") and n not in found:
        found[n] = (el["lon"], el["lat"])
print("找到:", {k: v for k, v in found.items()})

l2 = {r["station_name"]: r for r in stations if r["line_id"] == "2号线"}
max_sid = max(int(r["station_id"][1:]) for r in stations)


def add_station(name, lon, lat):
    global max_sid
    max_sid += 1
    row = {"station_id": f"S{max_sid:03d}", "station_name": name, "line_id": "2号线",
           "longitude": f"{lon:.6f}", "latitude": f"{lat:.6f}", "is_transfer": "0"}
    stations.append(row)
    l2[name] = row
    return row


def add_edge(a, b):
    d = hav(float(a["longitude"]), float(a["latitude"]), float(b["longitude"]), float(b["latitude"]))
    edges.append({"from_station": a["station_id"], "to_station": b["station_id"],
                  "line_id": "2号线", "travel_time_min": f"{d/1000/35*60:.1f}",
                  "distance_m": f"{d:.0f}", "direction": "安镇"})


if "梅园开原寺" in found and "梅园开原寺" not in l2:
    s = add_station("梅园开原寺", *found["梅园开原寺"])
    add_edge(s, l2["荣巷"])
if "安镇" in found and "安镇" not in l2:
    s = add_station("安镇", *found["安镇"])
    add_edge(l2["无锡东"], s)

# 既有2号线边的 direction 更新为东端终点 安镇
for e in edges:
    if e["line_id"] == "2号线" and e["direction"] == "无锡东":
        e["direction"] = "安镇"

with open(os.path.join(RAW, "metro_stations.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(stations[0].keys()))
    w.writeheader()
    w.writerows(stations)
with open(os.path.join(RAW, "metro_edges.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(edges[0].keys()))
    w.writeheader()
    w.writerows(edges)

l2seq = [r["station_name"] for r in stations if r["line_id"] == "2号线"]
print("2号线站点数:", len(l2seq))
print("stations:", len(stations), "edges:", len(edges))
