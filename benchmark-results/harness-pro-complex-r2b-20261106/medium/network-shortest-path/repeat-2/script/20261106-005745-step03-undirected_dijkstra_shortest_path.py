# ─── OpenGIS Agent · run b99e5e57 · step 3 · undirected_dijkstra_shortest_path ───
# Timestamp : 2026-11-06T00:57:45
# Semantic : undirected_dijkstra_shortest_path
# Metadata : 20261106-005745-step03-undirected_dijkstra_shortest_path.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import pandas as pd, json, heapq

src, tgt = "N10029499416", "N9988513543"
df = pd.read_csv("edges.csv")

adj_f = {}
adj_b = {}
for a, b, w in zip(df["from_node"], df["to_node"], df["length_m"]):
    adj_f.setdefault(a, []).append((b, w))
    adj_f.setdefault(b, []).append((a, w))
    adj_b.setdefault(b, []).append((a, w))
    adj_b.setdefault(a, []).append((b, w))


def bidirectional_dijkstra(s, t):
    df_ = {s: 0.0}
    db_ = {t: 0.0}
    pf = {}
    pb = {}
    seen_f, seen_b = set(), set()
    pqf = [(0.0, s)]
    pqb = [(0.0, t)]
    best = float("inf")
    meet = None
    while pqf and pqb:
        if pqf[0][0] + pqb[0][0] >= best:
            break
        d, u = heapq.heappop(pqf)
        if u in seen_f:
            continue
        seen_f.add(u)
        if u in db_ and d + db_[u] < best:
            best = d + db_[u]
            meet = u
        for v, w in adj_f.get(u, []):
            nd = d + w
            if nd < df_.get(v, float("inf")):
                df_[v] = nd
                pf[v] = u
                heapq.heappush(pqf, (nd, v))
        d, u = heapq.heappop(pqb)
        if u in seen_b:
            continue
        seen_b.add(u)
        if u in df_ and d + df_[u] < best:
            best = d + df_[u]
            meet = u
        for v, w in adj_b.get(u, []):
            nd = d + w
            if nd < db_.get(v, float("inf")):
                db_[v] = nd
                pb[v] = u
                heapq.heappush(pqb, (nd, v))
    if meet is None:
        return float("inf"), None
    left = []
    cur = meet
    while cur != s:
        left.append(cur)
        cur = pf[cur]
    left.append(s)
    left.reverse()
    right = []
    cur = meet
    while cur != t:
        cur = pb[cur]
        right.append(cur)
    return best, left + right


dist2, path2 = bidirectional_dijkstra(src, tgt)

# sanity: path edges all exist, length sum
edgeset = set(zip(df["from_node"], df["to_node"])) | set(zip(df["to_node"], df["from_node"]))
wmap = {}
for a, b, ww in zip(df["from_node"], df["to_node"], df["length_m"]):
    wmap[(a, b)] = min(wmap.get((a, b), 1e18), ww)
    wmap[(b, a)] = min(wmap.get((b, a), 1e18), ww)
seq_sum = sum(wmap[(path2[i], path2[i+1])] for i in range(len(path2)-1))
print("scipy distance", round(dist2, 3), "seqsum", round(seq_sum, 3), "nodes", len(path2))

result = {"source": src, "target": tgt, "distance_m": round(float(dist2), 3), "path_node_count": len(path2)}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False))
pd.DataFrame({"seq": range(len(path2)), "node": path2}).to_csv("shortest_path_nodes.csv", index=False)

# ─── Observations ───
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 468, in _run_exec
#     compiled = compile(code, "<agent>", "eval")
#                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 1
#     import pandas as pd, numpy as np, json, heapq
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
# ModuleNotFoundError: No module named 'scipy'
# 
# --- stdout before error ---
