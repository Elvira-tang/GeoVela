# ─── OpenGIS Agent · run df1047c0 · step 1 · network_shortest_path ───
# Timestamp : 2026-11-06T00:54:58
# Semantic : network_shortest_path
# Metadata : 20261106-005458-step01-network_shortest_path.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import json, csv
from collections import defaultdict
import heapq

SRC, TGT = "N10029499416", "N9988513543"
rows = []
with open("edges.csv", newline="", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append((r["edge_id"], r["from_node"].strip(), r["to_node"].strip(), float(r["length_m"])))

adj = defaultdict(list)
for eid, u, v, w in rows:
    adj[u].append((v, w))
    adj[v].append((u, w))

print("edges", len(rows), "nodes", len(adj))
print("src in graph", SRC in adj, "tgt in graph", TGT in adj)

def dijkstra(src, tgt):
    dist = {src: 0.0}
    prev = {}
    pq = [(0.0, src)]
    done = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in done:
            continue
        done.add(u)
        if u == tgt:
            break
        for v, w in adj[u]:
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if tgt not in dist:
        return None, None
    path = [tgt]
    while path[-1] != src:
        path.append(prev[path[-1]])
    return dist[tgt], path[::-1]

d, path = dijkstra(SRC, TGT)
print("dist", d, "nodes", len(path))
print("path head", path[:3], "path tail", path[-3:])

result = {
    "source": SRC,
    "target": TGT,
    "distance_m": round(d, 3),
    "path_node_count": len(path),
}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("wrote result.json", result)

# ─── Verification (independent scipy implementation) ───
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra as sp_dijkstra

nodes = sorted(adj)
idx = {n: i for i, n in enumerate(nodes)}
I = [idx[u] for _, u, v, _ in rows] + [idx[v] for _, u, v, _ in rows]
J = [idx[v] for _, u, v, _ in rows] + [idx[u] for _, u, v, _ in rows]
W = [w for _, _, _, w in rows] * 2
G = csr_matrix((W, (I, J)), shape=(len(nodes), len(nodes)))
dist_matrix, pred = sp_dijkstra(
    G, directed=False, indices=idx[SRC], return_predecessors=True
)
sp_dist = dist_matrix[idx[TGT]]

sp_path = [idx[TGT]]
while sp_path[-1] != idx[SRC]:
    sp_path.append(pred[sp_path[-1]])
sp_path = [nodes[i] for i in sp_path[::-1]]

edge_w = {}
for eid, u, v, w in rows:
    edge_w.setdefault(frozenset((u, v)), w)
resummed = sum(edge_w[frozenset((a, b))] for a, b in zip(path, path[1:]))

print("VERIFY scipy dist      :", round(sp_dist, 3))
print("VERIFY distance match  :", abs(sp_dist - d) < 1e-6)
print("VERIFY path match      :", sp_path == path)
print("VERIFY resummed length :", round(resummed, 3), "match:", abs(resummed - d) < 1e-6)
print("VERIFY path contiguous :", all(frozenset((a, b)) in edge_w for a, b in zip(path, path[1:])))
print("VERIFY endpoints       :", path[0] == SRC, path[-1] == TGT)
with open("result.json", encoding="utf-8") as f:
    back = json.load(f)
print("VERIFY result.json     :", back)
print("VERIFY json keys ok    :", set(back) == {"source", "target", "distance_m", "path_node_count"})

# ─── Observations ───
# edges 43461 nodes 38877
# src in graph True tgt in graph True
# dist 5004.199999999998 nodes 61
# path head ['N10029499416', 'N7610822016', 'N1441349799'] path tail ['N2706614899', 'N2706614898', 'N9988513543']
