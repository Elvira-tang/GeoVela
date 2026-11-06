# -*- coding: utf-8 -*-
"""采集滨湖区步行网络（OSM/Overpass）。
3x3 主瓦片；单片失败自动四分递归；每片独立缓存，可断点续跑。
"""
import csv
import json
import math
import os
import time
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
CACHE = os.path.join(os.environ.get("TEMP", "."), "wuxi_walk_cache")
os.makedirs(CACHE, exist_ok=True)

MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

LATS = (31.44, 31.48, 31.52, 31.56)
LONS = (120.22, 120.26, 120.30, 120.34)
MAX_DEPTH = 2

HW = "footway|pedestrian|path|steps|residential|service|unclassified|tertiary|secondary|living_street|cycleway"

QUERY = """
[out:json][timeout:120];
way["highway"~"^({hw})$"]({bbox})->.w;
.w out body;
node(w.w);
out skel qt;
"""


def bbox_key(s, w, n, e):
    return f"{s:.3f}_{w:.3f}_{n:.3f}_{e:.3f}.json"


def overpass(query, tries=5):
    for attempt in range(tries):
        mirror = MIRRORS[attempt % len(MIRRORS)]
        try:
            data = urllib.parse.urlencode({"data": query}).encode()
            req = urllib.request.Request(mirror, data=data,
                                         headers={"User-Agent": "wuxi-walking-collector/1.0"})
            with urllib.request.urlopen(req, timeout=130) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"    retry {attempt} {mirror.split('/')[2]}: {type(e).__name__}", flush=True)
            time.sleep(min(5 + attempt * 3, 20))
    return None


def fetch(s, w, n, e, depth=0):
    """返回 elements 列表；失败则四分递归。"""
    path = os.path.join(CACHE, bbox_key(s, w, n, e))
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))["elements"]
    print(f"  bbox {s:.2f},{w:.2f},{n:.2f},{e:.2f} depth={depth}", flush=True)
    data = overpass(QUERY.format(hw=HW, bbox=f"{s},{w},{n},{e}"))
    if data is not None:
        json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        return data["elements"]
    if depth >= MAX_DEPTH:
        print("    !! 该片最终失败", flush=True)
        return []
    mla, mlo = (s + n) / 2, (w + e) / 2
    out = []
    for (s2, n2) in ((s, mla), (mla, n)):
        for (w2, e2) in ((w, mlo), (mlo, e)):
            out += fetch(s2, w2, n2, e2, depth + 1)
    return out


def hav(lon1, lat1, lon2, lat2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def main():
    nodes, ways = {}, {}
    for i in range(3):
        for j in range(3):
            legacy = os.path.join(CACHE, f"tile_{i}_{j}.json")
            new = os.path.join(CACHE, bbox_key(LATS[i], LONS[j], LATS[i + 1], LONS[j + 1]))
            if os.path.exists(legacy) and not os.path.exists(new):
                os.replace(legacy, new)
            els = fetch(LATS[i], LONS[j], LATS[i + 1], LONS[j + 1])
            for el in els:
                if el["type"] == "node":
                    nodes.setdefault(el["id"], (el["lon"], el["lat"]))
                elif el["type"] == "way":
                    ways.setdefault(el["id"], el)
            print(f"  累计 nodes={len(nodes)} ways={len(ways)}", flush=True)

    edges = {}
    for wid, wy in ways.items():
        t = wy.get("tags", {})
        hw, nm = t.get("highway", ""), t.get("name", "")
        refs = [r for r in wy.get("nodes", []) if r in nodes]
        for a, b in zip(refs, refs[1:]):
            if a == b:
                continue
            la, lb = nodes[a], nodes[b]
            d = hav(la[0], la[1], lb[0], lb[1])
            if d < 0.5 or d > 800:
                continue
            key = (min(a, b), max(a, b))
            if key not in edges or d < edges[key][2]:
                edges[key] = (a, b, d, hw, nm)

    node_rows = [{"node_id": f"N{nid}", "longitude": f"{lon:.6f}", "latitude": f"{lat:.6f}"}
                 for nid, (lon, lat) in sorted(nodes.items())]
    edge_rows = [{"edge_id": f"W{i:05d}", "from_node": f"N{a}", "to_node": f"N{b}",
                  "length_m": f"{d:.1f}", "highway": hw, "name": nm}
                 for i, (a, b, d, hw, nm) in enumerate(sorted(edges.values()), 1)]

    with open(os.path.join(RAW, "walking_nodes.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["node_id", "longitude", "latitude"])
        w.writeheader()
        w.writerows(node_rows)
    with open(os.path.join(RAW, "walking_edges.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["edge_id", "from_node", "to_node", "length_m", "highway", "name"])
        w.writeheader()
        w.writerows(edge_rows)
    with open(os.path.join(RAW, "walking_network.graphml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n')
        f.write('<key id="lon" for="node" attr.name="longitude" attr.type="double"/>\n')
        f.write('<key id="lat" for="node" attr.name="latitude" attr.type="double"/>\n')
        f.write('<key id="len" for="edge" attr.name="length_m" attr.type="double"/>\n')
        f.write('<key id="hw" for="edge" attr.name="highway" attr.type="string"/>\n')
        f.write('<key id="nm" for="edge" attr.name="name" attr.type="string"/>\n')
        f.write('<graph id="walking" edgedefault="undirected">\n')
        for nid, (lon, lat) in sorted(nodes.items()):
            f.write(f'<node id="N{nid}"><data key="lon">{lon:.6f}</data>'
                    f'<data key="lat">{lat:.6f}</data></node>\n')
        for a, b, d, hw, nm in sorted(edges.values()):
            f.write(f'<edge source="N{a}" target="N{b}"><data key="len">{d:.1f}</data>'
                    f'<data key="hw">{escape(hw)}</data><data key="nm">{escape(nm)}</data></edge>\n')
        f.write('</graph>\n</graphml>\n')
    print(f"完成: nodes={len(node_rows)} edges={len(edge_rows)}", flush=True)


if __name__ == "__main__":
    main()
