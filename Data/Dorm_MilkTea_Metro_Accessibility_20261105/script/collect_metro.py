# -*- coding: utf-8 -*-
"""采集无锡地铁站点、相邻站关系、出入口（数据源：OpenStreetMap via Overpass）。
输出到 data/raw/：metro_stations.csv, metro_edges.csv, metro_station_entrances.csv
"""
import csv
import json
import math
import os
import re
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")

MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

BBOX = "31.30,119.95,31.75,120.55"  # 无锡全域

QUERY_REL = """
[out:json][timeout:150];
rel["type"="route"]["route"="subway"]({bbox})->.rels;
.rels out body;
way(r.rels)->.plats;
.plats out body;
node(r.rels)->.stops;
.stops out body;
node(w.plats);
out body;
""".format(bbox=BBOX)

QUERY_STATIONS = """
[out:json][timeout:120];
node["railway"~"^(station|halt|stop)$"]({bbox});
out body;
""".format(bbox=BBOX)

QUERY_ENTRANCE = """
[out:json][timeout:120];
node["railway"="subway_entrance"]({bbox});
out body;
""".format(bbox=BBOX)


def overpass(query):
    for attempt in range(4):
        mirror = MIRRORS[attempt % len(MIRRORS)]
        try:
            data = urllib.parse.urlencode({"data": query}).encode()
            req = urllib.request.Request(mirror, data=data,
                                         headers={"User-Agent": "wuxi-metro-collector/1.0"})
            with urllib.request.urlopen(req, timeout=170) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  retry {attempt} {mirror.split('/')[2]}: {type(e).__name__} {str(e)[:60]}",
                  flush=True)
            time.sleep(3 + attempt * 2)
    raise SystemExit("Overpass 均不可用")


def haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def line_of(tags):
    ref = (tags.get("ref") or "").strip()
    if ref:
        return ref if ref.endswith("号线") else ref + "号线"
    s = tags.get("name") or ""
    m = re.search(r"(S?\d+)\s*号线", s)
    return (m.group(1) + "号线") if m else ""


CORE = (31.40, 119.98, 31.75, 120.45)  # 无锡核心区 bbox，用于排除苏州/常州线路


def in_core(lon, lat):
    return CORE[1] <= lon <= CORE[3] and CORE[0] <= lat <= CORE[2]


def norm_name(name):
    return name[:-1] if name.endswith("站") and len(name) > 2 else name


def main():
    print("== 线路关系查询 ==", flush=True)
    data = overpass(QUERY_REL)
    nodes = {}
    ways = {}
    relations = []
    for el in data["elements"]:
        if el["type"] == "node":
            nodes[el["id"]] = el
        elif el["type"] == "way":
            ways[el["id"]] = el
        elif el["type"] == "relation":
            relations.append(el)
    print(f"relations={len(relations)} ways={len(ways)} nodes={len(nodes)}", flush=True)

    def station_from_node(nd):
        t = nd.get("tags", {})
        if t.get("railway") != "station" and t.get("subway") != "yes" and "station" not in (t.get("public_transport") or ""):
            return None
        name = norm_name((t.get("name") or "").strip())
        return (name, nd["lon"], nd["lat"]) if name else None

    def station_from_way(wy):
        t = wy.get("tags", {})
        name = norm_name((t.get("name") or "").strip())
        if not name:
            return None
        if t.get("railway") not in ("station", "platform") and "platform" not in (t.get("public_transport") or ""):
            return None
        pts = [(nodes[r]["lon"], nodes[r]["lat"]) for r in wy.get("nodes", []) if r in nodes]
        if not pts:
            return None
        return (name, sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    # 每条线路：按 relation 成员顺序提取站点序列（去重后取最长）
    line_seq = {}  # line -> ordered list of station names
    line_stop_coords = {}  # (line, name) -> (lon, lat)
    for rel in relations:
        tags = rel.get("tags", {})
        rel_name = tags.get("name") or ""
        if "苏州" in rel_name or "常州" in rel_name:
            print(f"  跳过外地线路: {rel_name}", flush=True)
            continue
        line = line_of(tags)
        if not line:
            continue
        seq = []
        seen_in_rel = set()
        for m in rel.get("members", []):
            if m.get("role") not in ("stop", "platform", ""):
                continue
            st = None
            if m["type"] == "node" and m["ref"] in nodes:
                st = station_from_node(nodes[m["ref"]])
            elif m["type"] == "way" and m["ref"] in ways:
                st = station_from_way(ways[m["ref"]])
            if st and st[0] not in seen_in_rel:
                seen_in_rel.add(st[0])
                seq.append(st)
        if len(seq) < 2:
            continue
        # 排除落在无锡核心区以外的同名线路（双保险）
        if "无锡" not in rel_name and not any(in_core(lon, lat) for _, lon, lat in seq):
            print(f"  跳过非无锡线路: {rel_name} ({line})", flush=True)
            continue
        # 保留更长的序列（双向 relation 只留一条）
        names = [s[0] for s in seq]
        if line not in line_seq or len(names) > len(line_seq[line]):
            line_seq[line] = names
        for name, lon, lat in seq:
            line_stop_coords[(line, name)] = (lon, lat)

    # 补充 relation 成员缺失的终点站；全局规范化名称去重，避免把邻线站点吸附进来
    st_data = overpass(QUERY_STATIONS)
    extra = []
    for el in st_data["elements"]:
        if el["type"] != "node":
            continue
        name = (el.get("tags", {}).get("name") or "").strip()
        if name:
            extra.append((norm_name(name), el["lon"], el["lat"]))
    print(f"候选地铁站节点: {len(extra)}", flush=True)
    placed = {norm_name(n) for seq in line_seq.values() for n in seq}
    changed = True
    while changed:
        changed = False
        for line, seq in line_seq.items():
            first = line_stop_coords[(line, seq[0])]
            last = line_stop_coords[(line, seq[-1])]
            for name, lon, lat in extra:
                if name in placed:
                    continue
                d1 = haversine(lon, lat, first[0], first[1])
                d2 = haversine(lon, lat, last[0], last[1])
                if d1 < 2600 and d1 <= d2:
                    seq.insert(0, name)
                    line_stop_coords[(line, name)] = (lon, lat)
                    placed.add(name)
                    print(f"  {line} 首端补站: {name}", flush=True)
                    changed = True
                elif d2 < 2600:
                    seq.append(name)
                    line_stop_coords[(line, name)] = (lon, lat)
                    placed.add(name)
                    print(f"  {line} 末端补站: {name}", flush=True)
                    changed = True

    for line, seq in sorted(line_seq.items()):
        print(f"  {line}: {len(seq)} 站  {seq[0]} -> {seq[-1]}", flush=True)

    # 站点表：按各线保留序列的顺序排列，未进入序列的站点追加在末尾
    name_lines = {}
    for (line, name) in line_stop_coords:
        name_lines.setdefault(name, set()).add(line)
    ordered_keys = []
    for line, seq in sorted(line_seq.items()):
        for name in seq:
            if (line, name) in line_stop_coords and (line, name) not in ordered_keys:
                ordered_keys.append((line, name))
        for (l2, name) in line_stop_coords:
            if l2 == line and (l2, name) not in ordered_keys:
                ordered_keys.append((l2, name))
    station_rows = []
    for sid, (line, name) in enumerate(ordered_keys, 1):
        lon, lat = line_stop_coords[(line, name)]
        station_rows.append({
            "station_id": f"S{sid:03d}",
            "station_name": name,
            "line_id": line,
            "longitude": f"{lon:.6f}",
            "latitude": f"{lat:.6f}",
            "is_transfer": "1" if len(name_lines[name]) > 1 else "0",
        })
    station_id_of = {(r["station_name"], r["line_id"]): r["station_id"] for r in station_rows}

    # 相邻站表
    edge_rows = []
    seen_pairs = set()
    for line, seq in sorted(line_seq.items()):
        for i in range(len(seq) - 1):
            a, b = seq[i], seq[i + 1]
            key = (line, frozenset((a, b)))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            la, lb = line_stop_coords[(line, a)], line_stop_coords[(line, b)]
            d = haversine(la[0], la[1], lb[0], lb[1])
            t = d / 1000 / 35 * 60  # 按商业运行速度 35km/h 估算
            edge_rows.append({
                "from_station": station_id_of[(a, line)],
                "to_station": station_id_of[(b, line)],
                "line_id": line,
                "travel_time_min": f"{t:.1f}",
                "distance_m": f"{d:.0f}",
                "direction": seq[-1],
            })
    # 换乘步行边（同站名跨线，3 分钟）
    for name, lines in name_lines.items():
        if len(lines) > 1:
            ids = [station_id_of[(name, l)] for l in sorted(lines)]
            for i in range(len(ids) - 1):
                edge_rows.append({
                    "from_station": ids[i],
                    "to_station": ids[i + 1],
                    "line_id": "换乘",
                    "travel_time_min": "3.0",
                    "distance_m": "0",
                    "direction": "站内换乘",
                })

    with open(os.path.join(RAW, "metro_stations.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["station_id", "station_name", "line_id", "longitude", "latitude", "is_transfer"])
        w.writeheader()
        w.writerows(station_rows)
    with open(os.path.join(RAW, "metro_edges.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["from_station", "to_station", "line_id", "travel_time_min", "distance_m", "direction"])
        w.writeheader()
        w.writerows(edge_rows)
    print(f"stations={len(station_rows)} edges={len(edge_rows)}", flush=True)

    # 出入口
    print("== 出入口查询 ==", flush=True)
    ent = overpass(QUERY_ENTRANCE)
    ent_rows = []
    eid = 0
    for el in ent["elements"]:
        if el["type"] != "node":
            continue
        t = el.get("tags", {})
        lon, lat = el["lon"], el["lat"]
        best = None
        for r in station_rows:
            d = haversine(lon, lat, float(r["longitude"]), float(r["latitude"]))
            if d <= 450 and (best is None or d < best[0]):
                best = (d, r)
        if not best:
            continue
        eid += 1
        ent_rows.append({
            "entrance_id": f"E{eid:03d}",
            "station_id": best[1]["station_id"],
            "entrance_name": t.get("name") or t.get("ref") or f"{best[1]['station_name']}出入口",
            "longitude": f"{lon:.6f}",
            "latitude": f"{lat:.6f}",
        })
    with open(os.path.join(RAW, "metro_station_entrances.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["entrance_id", "station_id", "entrance_name", "longitude", "latitude"])
        w.writeheader()
        w.writerows(ent_rows)
    print(f"entrances={len(ent_rows)}（未匹配到站点的已丢弃）", flush=True)


if __name__ == "__main__":
    main()
