# ─── OpenGIS Agent · run 1503dba9 · step 5 · verify_shortest_path ───
# Timestamp : 2026-11-06T00:46:40
# Semantic : verify_shortest_path
# Metadata : 20261106-004640-step05-verify_shortest_path.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import csv, json, heapq
from collections import defaultdict

obj = json.load(open("result.json", encoding="utf-8"))
SRC, TGT = obj["source"], obj["target"]

adj = defaultdict(dict)
with open("edges.csv", encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        u, v, w = row["from_node"], row["to_node"], float(row["length_m"])
        if v not in adj[u] or w < adj[u][v]:
            adj[u][v] = w
        if u not in adj[v] or w < adj[v][u]:
            adj[v][u] = w

def bidir(src, tgt):
    if src == tgt:
        return 0.0
    df = {src: 0.0}; db = {tgt: 0.0}
    qf = [(0.0, src)]; qb = [(0.0, tgt)]
    best = float("inf"); done_f = set(); done_b = set()
    while qf or qb:
        if qf:
            d, u = heapq.heappop(qf)
            if u not in done_f:
                done_f.add(u)
                if u in db:
                    best = min(best, d + db[u])
                if best <= d:
                    return best
                for v, w in adj[u].items():
                    nd = d + w
                    if nd < df.get(v, float("inf")):
                        df[v] = nd; heapq.heappush(qf, (nd, v))
        if qb:
            d, u = heapq.heappop(qb)
            if u not in done_b:
                done_b.add(u)
                if u in df:
                    best = min(best, d + df[u])
                if best <= d:
                    return best
                for v, w in adj[u].items():
                    nd = d + w
                    if nd < db.get(v, float("inf")):
                        db[v] = nd; heapq.heappush(qb, (nd, v))
    return best

indep = bidir(SRC, TGT)
print("bidirectional dijkstra dist:", round(indep, 6))
print("matches result.json:", abs(indep - obj["distance_m"]) < 1e-9)
print("graph is undirected-symmetric:", all(v in adj[u] for u in adj for v in adj[u]))
print("src reachable, tgt reachable:", SRC in adj, TGT in adj)

# ─── Observations ───
# bidirectional dijkstra dist: 5004.2
# matches result.json: True
# graph is undirected-symmetric: True
# src reachable, tgt reachable: True True
