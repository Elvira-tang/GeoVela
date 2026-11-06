# ─── OpenGIS Agent · run ebbbeb89 · step 3 · undirected_shortest_path ───
# Timestamp : 2026-11-06T00:51:14
# Semantic : undirected_shortest_path
# Metadata : 20261106-005114-step03-undirected_shortest_path.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import pandas as pd, heapq, json, collections

df = pd.read_csv('edges.csv', dtype={'from_node': str, 'to_node': str})
src, tgt = 'N10029499416', 'N9988513543'

adj = collections.defaultdict(list)
for f, t, w in zip(df.from_node, df.to_node, df.length_m):
    adj[f].append((t, w))
    adj[t].append((f, w))

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
        if nd < dist.get(v, float('inf')):
            dist[v] = nd
            prev[v] = u
            heapq.heappush(pq, (nd, v))

path = [tgt]
while path[-1] != src:
    path.append(prev[path[-1]])
path.reverse()

result = {
    "source": src,
    "target": tgt,
    "distance_m": round(float(dist[tgt]), 3),
    "path_node_count": len(path),
}
with open('result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# --- independent verification ---
with open('result.json', encoding='utf-8') as f:
    loaded = json.load(f)

# 1) recompute with Dijkstra-in-reverse (target as source) as cross-check
def dijkstra(s):
    dd = {s: 0.0}
    pq = [(0.0, s)]
    seen = set()
    pv = {}
    while pq:
        d, u = heapq.heappop(pq)
        if u in seen:
            continue
        seen.add(u)
        for v, w in adj[u]:
            nd = d + w
            if nd < dd.get(v, float('inf')):
                dd[v] = nd
                pv[v] = u
                heapq.heappush(pq, (nd, v))
    return dd, pv

rev_dist, _ = dijkstra(tgt)
rev_check = round(rev_dist[src], 3)

# 2) optimality certificate from the reverse run: for every edge (u,v),
#    d_rev[u] <= w(u,v) + d_rev[v] proves d_rev[src] is the true shortest distance
edge_violations = 0
for f, t, w in zip(df.from_node, df.to_node, df.length_m):
    if f in rev_dist and t in rev_dist:
        if rev_dist[f] > w + rev_dist[t] + 1e-9 or rev_dist[t] > w + rev_dist[f] + 1e-9:
            edge_violations += 1

# 3) validate path is contiguous in the graph and sum weights
path_cost = 0.0
ok = True
for a, b in zip(path, path[1:]):
    cand = [w for (v, w) in adj[a] if v == b]
    if not cand:
        ok = False
        break
    path_cost += min(cand)
path_cost = round(path_cost, 3)

checks = {
    "keys_correct": list(loaded.keys()) == ["source", "target", "distance_m", "path_node_count"],
    "source_ok": loaded["source"] == src,
    "target_ok": loaded["target"] == tgt,
    "starts_at_source": path[0] == src,
    "ends_at_target": path[-1] == tgt,
    "path_contiguous": ok,
    "path_cost_matches": abs(path_cost - loaded["distance_m"]) < 1e-6,
    "reverse_dijkstra_matches": abs(rev_check - loaded["distance_m"]) < 1e-6,
    "optimality_certificate": edge_violations == 0,
    "distance_rounded_3dp": loaded["distance_m"] == round(loaded["distance_m"], 3),
    "path_node_count_matches": loaded["path_node_count"] == len(path),
}
print(json.dumps(loaded, indent=2, ensure_ascii=False))
print("path_cost_m:", path_cost, "reverse_dijkstra:", rev_check, "edge_violations:", edge_violations)
print("dijkstra_hops:", len(path) - 1)
print(json.dumps(checks, indent=2))
print("ALL OK" if all(checks.values()) else "FAILED")

# ─── Observations ───
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 468, in _run_exec
#     compiled = compile(code, "<agent>", "eval")
#                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 1
#     import pandas as pd, heapq, json, collections
#     ^^^^^^
# SyntaxError: invalid syntax
# 
# During handling of the above exception, another exception occurred:
# 
# Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 471, in _run_exec
#     exec(compile(code, "<agent>", "exec"), namespace, namespace)
#   File "<agent>", line 70, in <module>
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 277, in patched_import
#     result = _original_import(name, globals, locals, fromlist, level)
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# ModuleNotFoundError: No module named 'networkx'
# 
# --- stdout before error ---
