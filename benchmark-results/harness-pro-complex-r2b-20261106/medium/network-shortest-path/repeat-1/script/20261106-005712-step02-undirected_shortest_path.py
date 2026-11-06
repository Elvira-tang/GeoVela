# ─── OpenGIS Agent · run 5f90a291 · step 2 · undirected_shortest_path ───
# Timestamp : 2026-11-06T00:57:12
# Semantic : undirected_shortest_path
# Metadata : 20261106-005712-step02-undirected_shortest_path.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import heapq, json
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra as sp_dijkstra, connected_components

df = pd.read_csv("edges.csv", encoding="utf-8-sig")
src, tgt = "N10029499416", "N9988513543"

adj = {}
for f, t, w in zip(df["from_node"].astype(str), df["to_node"].astype(str), df["length_m"].astype(float)):
    adj.setdefault(f, []).append((t, w))
    adj.setdefault(t, []).append((f, w))

def dijkstra(adj, s, t):
    dist = {s: 0.0}
    prev = {s: None}
    pq = [(0.0, s)]
    done = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in done:
            continue
        done.add(u)
        if u == t:
            break
        for v, w in adj.get(u, ()):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if t not in dist:
        return None, None
    path = []
    cur = t
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return dist[t], path[::-1]

dist, path = dijkstra(adj, src, tgt)
print("dijkstra dist:", dist, "nodes:", len(path))
print("sampled path head:", path[:5])

nodes = sorted(adj)
idx = {n: i for i, n in enumerate(nodes)}
U = df["from_node"].astype(str).map(idx).to_numpy()
V = df["to_node"].astype(str).map(idx).to_numpy()
W = df["length_m"].astype(float).to_numpy()
n_nodes = len(nodes)
mat = csr_matrix(
    (np.concatenate([W, W]), (np.concatenate([U, V]), np.concatenate([V, U]))),
    shape=(n_nodes, n_nodes),
)
sp_dist, sp_pred = sp_dijkstra(mat, directed=False, indices=idx[src], return_predecessors=True)
ver_dist = float(sp_dist[idx[tgt]])
seq = [idx[tgt]]
while seq[-1] != idx[src]:
    seq.append(int(sp_pred[seq[-1]]))
sp_path = [nodes[i] for i in reversed(seq)]

edge_w = {}
for f, t, w in zip(df["from_node"].astype(str), df["to_node"].astype(str), df["length_m"].astype(float)):
    edge_w[(f, t)] = min(w, edge_w.get((f, t), w))
    edge_w[(t, f)] = min(w, edge_w.get((t, f), w))
sumpath = sum(edge_w[(sp_path[i], sp_path[i + 1])] for i in range(len(sp_path) - 1))
ncomp = connected_components(mat, directed=False)[0]
print("scipy dist:", ver_dist, "nodes:", len(sp_path), "path sum from csv:", sumpath)
print("same path as heapq:", sp_path == path, "dist match:", abs(ver_dist - dist) < 1e-6)
print("components:", ncomp, "graph nodes:", n_nodes, "edges:", len(df))

result = {
    "source": src,
    "target": tgt,
    "distance_m": round(float(dist), 3),
    "path_node_count": len(path),
}
with open("result.json", "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=2)
with open("shortest_path_nodes.json", "w", encoding="utf-8") as fh:
    json.dump(
        {"source": src, "target": tgt, "distance_m": round(float(dist), 3), "path": path},
        fh,
        ensure_ascii=False,
        indent=2,
    )
print("wrote result.json:", result)

# ─── Observations ───
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 468, in _run_exec
#     compiled = compile(code, "<agent>", "eval")
#                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 1
#     import heapq, json
#     ^^^^^^
# SyntaxError: invalid syntax
# 
# During handling of the above exception, another exception occurred:
# 
# Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 471, in _run_exec
#     exec(compile(code, "<agent>", "exec"), namespace, namespace)
#   File "<agent>", line 3, in <module>
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 277, in patched_import
#     result = _original_import(name, globals, locals, fromlist, level)
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# ModuleNotFoundError: No module named 'networkx'
# 
# --- stdout before error ---
