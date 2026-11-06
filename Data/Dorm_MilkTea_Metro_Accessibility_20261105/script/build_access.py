# -*- coding: utf-8 -*-
"""基于步行网络与地铁图计算可达性：
1) dorm_station_access.csv   宿舍 -> 地铁出入口（步行）
2) station_milktea_access.csv 地铁站 -> 奶茶店（出站步行）
3) accessibility_results.csv  宿舍 -> 奶茶店 全程最短时间
"""
import csv
import heapq
import math
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")

WALK_M_PER_MIN = 75.0
STATION_FIXED_MIN = 2.0     # 进出站固定时间
MAX_DORM_WALK_M = 2500.0    # 宿舍到站步行上限（校园南北约 2km）
SNAP_MAX_M = 250.0          # 点位吸附到路网的最大距离


def hav(lon1, lat1, lon2, lat2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def load_walk():
    nodes = {}
    for r in csv.DictReader(open(os.path.join(RAW, "walking_nodes.csv"), encoding="utf-8-sig")):
        nodes[r["node_id"]] = (float(r["longitude"]), float(r["latitude"]))
    adj = {n: [] for n in nodes}
    for r in csv.DictReader(open(os.path.join(RAW, "walking_edges.csv"), encoding="utf-8-sig")):
        a, b, d = r["from_node"], r["to_node"], float(r["length_m"])
        adj[a].append((b, d))
        adj[b].append((a, d))
    return nodes, adj


def load_metro():
    st = {r["station_id"]: r for r in
          csv.DictReader(open(os.path.join(RAW, "metro_stations.csv"), encoding="utf-8-sig"))}
    adj = {s: [] for s in st}
    for r in csv.DictReader(open(os.path.join(RAW, "metro_edges.csv"), encoding="utf-8-sig")):
        a, b, t = r["from_station"], r["to_station"], float(r["travel_time_min"])
        adj.setdefault(a, []).append((b, t))
        adj.setdefault(b, []).append((a, t))
    return st, adj


def dijkstra(adj, source, cutoff=None):
    dist = {source: 0.0}
    pq = [(0.0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, float("inf")):
            continue
        if cutoff is not None and d > cutoff:
            continue
        for v, w in adj.get(u, ()):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def snap(points, nodes, max_m):
    """为每个点找最近路网节点；points = [(key, lon, lat)]。格网按 0.001° 分桶。"""
    grid = {}
    for nid, (lon, lat) in nodes.items():
        grid.setdefault((int(lon * 1000), int(lat * 1000)), []).append(nid)
    out = {}
    for key, lon, lat in points:
        gx, gy = int(lon * 1000), int(lat * 1000)
        best = None
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                for nid in grid.get((gx + dx, gy + dy), ()):
                    nlon, nlat = nodes[nid]
                    d = hav(lon, lat, nlon, nlat)
                    if best is None or d < best[0]:
                        best = (d, nid)
        if best and best[0] <= max_m:
            out[key] = best
    return out


def main():
    nodes, wadj = load_walk()
    stations, madj = load_metro()
    print(f"路网节点 {len(nodes)}，地铁站 {len(stations)}")

    # 出入口
    ents = list(csv.DictReader(open(os.path.join(RAW, "metro_station_entrances.csv"), encoding="utf-8-sig")))
    ent_rows = [(e["entrance_id"], e["station_id"], float(e["longitude"]), float(e["latitude"]) + 0.0) for e in ents]
    ent_pts = [(e[0], e[2], e[3]) for e in ent_rows]
    ent_snap = snap(ent_pts, nodes, SNAP_MAX_M)
    print(f"出入口 {len(ent_rows)}，吸附成功 {len(ent_snap)}")

    # 宿舍
    dorms = list(csv.DictReader(open(os.path.join(PROC, "dormitories.csv"), encoding="utf-8-sig")))
    dorm_pts = [(d["宿舍名称"], float(d["经度"]), float(d["纬度"])) for d in dorms]
    dorm_snap = snap(dorm_pts, nodes, SNAP_MAX_M)
    print(f"宿舍 {len(dorms)}，吸附成功 {len(dorm_snap)}")

    # 奶茶店
    pois = list(csv.DictReader(open(os.path.join(PROC, "milktea_wgs84.csv"), encoding="utf-8-sig")))
    poi_pts = [(p["poi_id"], float(p["longitude"]), float(p["latitude"])) for p in pois]
    poi_snap = snap(poi_pts, nodes, SNAP_MAX_M)
    print(f"奶茶店 {len(pois)}，吸附成功 {len(poi_snap)}")

    # 每个站（多源=该站全部出入口）到所有奶茶店的最短步行
    def multi_source(adj, sources):
        dist = {s: 0.0 for s in sources}
        pq = [(0.0, s) for s in sources]
        heapq.heapify(pq)
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, float("inf")):
                continue
            for v, w in adj.get(u, ()):
                nd = d + w
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return dist

    st_sources = {}
    for eid, sid, _, _ in ent_rows:
        if eid in ent_snap:
            st_sources.setdefault(sid, []).append(ent_snap[eid][1])
    station_to_poi = {}
    for sid, srcs in st_sources.items():
        dist = multi_source(wadj, srcs)
        station_to_poi[sid] = {pid: dist[nid] for pid, (_, nid) in poi_snap.items() if nid in dist}
    print(f"完成站点到奶茶店的步行距离：{len(station_to_poi)} 个站")

    # 1) 宿舍 -> 出入口
    with open(os.path.join(PROC, "dorm_station_access.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dorm", "station_id", "station_name", "entrance_id",
                                          "walk_distance_m", "walk_time_min"])
        w.writeheader()
        for d, (snapd, nid) in dorm_snap.items():
            dist = dijkstra(wadj, nid, cutoff=MAX_DORM_WALK_M)
            best = {}
            for eid, sid, _, _ in ent_rows:
                if eid not in ent_snap:
                    continue
                nd = ent_snap[eid][1]
                if nd in dist and dist[nd] <= MAX_DORM_WALK_M:
                    if sid not in best or dist[nd] < best[sid][1]:
                        best[sid] = (eid, dist[nd])
            for sid, (eid, d_m) in sorted(best.items()):
                w.writerow({"dorm": d, "station_id": sid,
                            "station_name": stations[sid]["station_name"],
                            "entrance_id": eid, "walk_distance_m": f"{d_m:.0f}",
                            "walk_time_min": f"{d_m / WALK_M_PER_MIN:.1f}"})
    print("dorm_station_access 完成")

    # 2) 地铁站 -> 奶茶店（该站所有出入口的多源最短步行）
    with open(os.path.join(PROC, "station_milktea_access.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["station_id", "station_name", "poi_id", "poi_name",
                                          "brand", "walk_distance_m", "walk_time_min"])
        w.writeheader()
        name_of = {p["poi_id"]: (p["name"], p["brand"]) for p in pois}
        for sid in sorted(station_to_poi):
            for pid, d in sorted(station_to_poi[sid].items(), key=lambda x: x[1]):
                nm, br = name_of[pid]
                w.writerow({"station_id": sid, "station_name": stations[sid]["station_name"],
                            "poi_id": pid, "poi_name": nm, "brand": br,
                            "walk_distance_m": f"{d:.0f}", "walk_time_min": f"{d / WALK_M_PER_MIN:.1f}"})
    print(f"station_milktea_access 完成：{sum(len(v) for v in station_to_poi.values())} 条")

    # 3) 宿舍 -> 奶茶店
    # 地铁全网时间
    metro_all = {s: dijkstra(madj, s) for s in stations}
    dorm_st = {}
    for r in csv.DictReader(open(os.path.join(PROC, "dorm_station_access.csv"), encoding="utf-8-sig")):
        dorm_st.setdefault(r["dorm"], {})[r["station_id"]] = float(r["walk_time_min"])

    with open(os.path.join(PROC, "accessibility_results.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dorm", "poi_id", "poi_name", "brand",
                                          "board_station", "alight_station",
                                          "walk_to_station_min", "ride_min", "walk_to_poi_min",
                                          "total_min", "detail"])
        w.writeheader()
        for dorm, cand in dorm_st.items():
            # 对每栋宿舍：最优上车点组合 term[B] = min_A(walk_A + ride(A->B)) + 出站固定
            term = {}
            via = {}
            for A, walk_a in cand.items():
                for B, ride in metro_all.get(A, {}).items():
                    if B not in station_to_poi:
                        continue
                    t = walk_a + STATION_FIXED_MIN + ride
                    if B not in term or t < term[B]:
                        term[B] = t
                        via[B] = A
            best_per_poi = {}
            for B, base in term.items():
                for pid, d in station_to_poi[B].items():
                    total = base + STATION_FIXED_MIN + d / WALK_M_PER_MIN
                    cur = best_per_poi.get(pid)
                    if cur is None or total < cur[0]:
                        best_per_poi[pid] = (total, B, via[B], d / WALK_M_PER_MIN, base)
            for pid, (total, B, A, wpoi, base) in best_per_poi.items():
                nm, br = name_of[pid]
                w.writerow({"dorm": dorm, "poi_id": pid, "poi_name": nm, "brand": br,
                            "board_station": A, "alight_station": B,
                            "walk_to_station_min": f"{cand[A]:.1f}",
                            "ride_min": f"{base - STATION_FIXED_MIN - cand[A]:.1f}",
                            "walk_to_poi_min": f"{wpoi:.1f}", "total_min": f"{total:.1f}",
                            "detail": f"{stations[A]['station_name']}上车→{stations[B]['station_name']}出站"})
    print("accessibility_results 完成")


if __name__ == "__main__":
    main()
