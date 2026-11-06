# ─── OpenGIS Agent · run f58bc5ff · step 2 · network_shortest_path ───
# Timestamp : 2026-11-06T01:00:51
# Semantic : network_shortest_path
# Metadata : 20261106-010051-step02-network_shortest_path.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import json, heapq
import pandas as pd
import numpy as np

SRC = "N10029499416"
TGT = "N9988513543"

df = pd.read_csv("edges.csv", encoding="utf-8-sig")[["from_node", "to_node", "length_m"]]

adj = {}
for u, v, w in df.itertuples(index=False):
    w = float(w)
    adj.setdefault(u, []).append((v, w))
    adj.setdefault(v, []).append((u, w))

dist = {SRC: 0.0}
prev = {}
pq = [(0.0, SRC)]
visited = set()
while pq:
    d, u = heapq.heappop(pq)
    if u in visited:
        continue
    visited.add(u)
    for v, w in adj.get(u, ()):
        nd = d + w
        if nd < dist.get(v, float("inf")):
            dist[v] = nd
            prev[v] = u
            heapq.heappush(pq, (nd, v))

path = [TGT]
while path[-1] != SRC:
    path.append(prev[path[-1]])
path.reverse()

dijkstra_dist = dist[TGT]

# independent optimality certificate: dual feasibility of dist over ALL edges
# (for every undirected edge u-v with weight w: dist[u] + w >= dist[v])
violations = 0
max_violation = 0.0
checked = 0
for u, v, w in df.itertuples(index=False):
    w = float(w)
    if u not in visited or v not in visited:
        continue
    du = dist[u]
    dv = dist[v]
    checked += 1
    if du + w < dv - 1e-9 or dv + w < du - 1e-9:
        violations += 1
        max_violation = max(max_violation, abs((du + w) - dv), abs((dv + w) - du))

# path length recomputed directly from matched edges between consecutive nodes
edge_map = {}
for u, v, ww in df.itertuples(index=False):
    edge_map.setdefault((u, v), []).append(float(ww))
    edge_map.setdefault((v, u), []).append(float(ww))
recomputed = 0.0
missing = 0
for a, b in zip(path[:-1], path[1:]):
    ws = edge_map.get((a, b))
    if not ws:
        missing += 1
    else:
        recomputed += min(ws)

print("dijkstra distance_m:", round(dijkstra_dist, 6))
print("edges checked:", checked, "optimality violations:", violations, "max_violation:", max_violation)
print("recomputed from path edges:", round(recomputed, 6), "missing edges:", missing)
print("path_node_count:", len(path))
print("path preview:", path[:5], "...", path[-5:])

result = {
    "source": SRC,
    "target": TGT,
    "distance_m": round(float(dijkstra_dist), 3),
    "path_node_count": int(len(path)),
}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

with open("path_nodes.json", "w", encoding="utf-8") as f:
    json.dump({"source": SRC, "target": TGT, "path_nodes": path}, f, ensure_ascii=False, indent=2)

print(json.dumps(result, ensure_ascii=False))
reachable = TGT in dist
ok = reachable and violations == 0 and missing == 0 and abs(recomputed - dijkstra_dist) < 1e-6
print("reachable:", reachable, "nodes settled:", len(visited))
print("verified:", ok)

# ─── Observations ───
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 468, in _run_exec
#     compiled = compile(code, "<agent>", "eval")
#                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 1
#     import json, heapq
#     ^^^^^^
# SyntaxError: invalid syntax
# 
# During handling of the above exception, another exception occurred:
# 
# Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 471, in _run_exec
#     exec(compile(code, "<agent>", "exec"), namespace, namespace)
#   File "<agent>", line 42, in <module>
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 277, in patched_import
#     result = _original_import(name, globals, locals, fromlist, level)
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# ModuleNotFoundError: No module named 'scipy'
# 
# --- stdout before error ---
