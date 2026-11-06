# ─── OpenGIS Agent · run 1503dba9 · step 1 · network_shortest_path ───
# Timestamp : 2026-11-06T00:46:25
# Semantic : network_shortest_path
# Metadata : 20261106-004625-step01-network_shortest_path.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import csv, json, heapq, math, os

SRC = "N10029499416"
TGT = "N9988513543"

adj = {}
nodes = set()
n_edges = 0
with open("edges.csv", encoding="utf-8-sig", newline="") as f:
    r = csv.DictReader(f)
    for row in r:
        u = row["from_node"].strip()
        v = row["to_node"].strip()
        w = float(row["length_m"])
        n_edges += 1
        nodes.add(u); nodes.add(v)
        adj.setdefault(u, []).append((v, w))
        adj.setdefault(v, []).append((u, w))

print("edges:", n_edges, "nodes:", len(nodes))
print("src in graph:", SRC in nodes, "tgt in graph:", TGT in nodes)

dist = {SRC: 0.0}
prev = {}
pq = [(0.0, SRC)]
visited = set()
while pq:
    d, u = heapq.heappop(pq)
    if u in visited:
        continue
    visited.add(u)
    if u == TGT:
        break
    for v, w in adj.get(u, ()):
        nd = d + w
        if nd < dist.get(v, math.inf):
            dist[v] = nd
            prev[v] = u
            heapq.heappush(pq, (nd, v))

if TGT not in dist:
    print("UNREACHABLE")
else:
    path = [TGT]
    while path[-1] != SRC:
        path.append(prev[path[-1]])
    path.reverse()
    total = sum(
        min(w for nb, w in adj[path[i]] if nb == path[i+1])
        for i in range(len(path)-1)
    )
    print("dijkstra dist:", round(dist[TGT], 6))
    print("path len:", len(path), "recomputed sum:", round(total, 6))
    print("reached nodes:", len(visited))
    result = {
        "source": SRC,
        "target": TGT,
        "distance_m": round(dist[TGT], 3),
        "path_node_count": len(path),
    }
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))

# ─── Observations ───
# edges: 43461 nodes: 38877
# src in graph: True tgt in graph: True
# dijkstra dist: 5004.2
# path len: 61 recomputed sum: 5004.2
# reached nodes: 9380
# {"source": "N10029499416", "target": "N9988513543", "distance_m": 5004.2, "path_node_count": 61}
