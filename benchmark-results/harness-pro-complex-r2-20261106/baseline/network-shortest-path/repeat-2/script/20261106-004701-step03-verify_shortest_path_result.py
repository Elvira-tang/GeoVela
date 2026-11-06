# ─── OpenGIS Agent · run a40cd2cc · step 3 · verify_shortest_path_result ───
# Timestamp : 2026-11-06T00:47:01
# Semantic : verify_shortest_path_result
# Metadata : 20261106-004701-step03-verify_shortest_path_result.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import heapq
import json
import math

import pandas as pd

df = pd.read_csv("edges.csv")
src, tgt = "N10029499416", "N9988513543"

# independent pure-Python Dijkstra with explicit path reconstruction
best = {}
for f, t, w in zip(df.from_node, df.to_node, df.length_m.astype(float)):
    if w < best.get((f, t), math.inf):
        best[(f, t)] = w
    if w < best.get((t, f), math.inf):
        best[(t, f)] = w
adj = {}
for (f, t), w in best.items():
    adj.setdefault(f, []).append((t, w))

dist = {src: 0.0}
prev = {}
pq = [(0.0, src)]
done = set()
while pq:
    d, u = heapq.heappop(pq)
    if u in done:
        continue
    done.add(u)
    for v, w in adj.get(u, ()):
        nd = d + w
        if nd < dist.get(v, math.inf):
            dist[v] = nd
            prev[v] = u
            heapq.heappush(pq, (nd, v))

path = [tgt]
while path[-1] != src:
    path.append(prev[path[-1]])
path.reverse()
seg = [best[(path[i], path[i + 1])] for i in range(len(path) - 1)]

bf = {src: 0.0}
for _ in range(len(best)):
    changed = False
    for (f, t), w in best.items():
        if bf.get(f, math.inf) + w < bf.get(t, math.inf):
            bf[t] = bf[f] + w
            changed = True
        if bf.get(t, math.inf) + w < bf.get(f, math.inf):
            bf[f] = bf[t] + w
            changed = True
    if not changed:
        break
d_bf = bf[tgt]

res = json.load(open("result.json", encoding="utf-8"))

checks = {
    "dist_matches_own_dijkstra": abs(res["distance_m"] - round(dist[tgt], 3)) < 1e-9,
    "dist_matches_bellman_ford": abs(res["distance_m"] - round(d_bf, 3)) < 1e-9,
    "path_edge_sum_matches": abs(res["distance_m"] - round(sum(seg), 3)) < 1e-9,
    "path_node_count_matches": res["path_node_count"] == len(path),
    "path_endpoints_ok": path[0] == src and path[-1] == tgt,
    "path_edges_all_exist": all((path[i], path[i + 1]) in best for i in range(len(path) - 1)),
    "no_negative_or_zero_weights": bool((df.length_m > 0).all()),
    "no_missing_lengths": bool(df.length_m.notna().all()),
    "keys_exact": list(res.keys()) == ["source", "target", "distance_m", "path_node_count"],
    "source_target_values_ok": res["source"] == src and res["target"] == tgt,
    "all_checks_pass": False,
}
checks["all_checks_pass"] = all(v for k, v in checks.items() if k != "all_checks_pass")

print("own dijkstra dist :", round(dist[tgt], 6))
print("bellman-ford dist :", round(d_bf, 6))
print("path edge sum     :", round(sum(seg), 6))
print("path node count   :", len(path))
print("result.json       :", res)
print("checks            :", json.dumps(checks, indent=2))


# ─── Observations ───
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 468, in _run_exec
#     compiled = compile(code, "<agent>", "eval")
#                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 1
#     import pandas as pd, json, math
#     ^^^^^^
# SyntaxError: invalid syntax
# 
# During handling of the above exception, another exception occurred:
# 
# Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 471, in _run_exec
#     exec(compile(code, "<agent>", "exec"), namespace, namespace)
#   File "<agent>", line 2, in <module>
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 277, in patched_import
#     result = _original_import(name, globals, locals, fromlist, level)
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# ModuleNotFoundError: No module named 'networkx'
# 
# --- stdout before error ---
