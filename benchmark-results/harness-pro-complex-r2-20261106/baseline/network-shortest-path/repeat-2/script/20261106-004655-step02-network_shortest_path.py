# ─── OpenGIS Agent · run a40cd2cc · step 2 · network_shortest_path ───
# Timestamp : 2026-11-06T00:46:55
# Semantic : network_shortest_path
# Metadata : 20261106-004655-step02-network_shortest_path.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import pandas as pd
import heapq, json, math

df = pd.read_csv('edges.csv')
src, tgt = 'N10029499416', 'N9988513543'
nodes = set(df.from_node) | set(df.to_node)
print('src present:', src in nodes, 'tgt present:', tgt in nodes, 'n_nodes:', len(nodes))
print('bad lengths:', df.length_m.isna().sum(), (df.length_m <= 0).sum())

# undirected adjacency
adj = {}
for f, t, w in zip(df.from_node, df.to_node, df.length_m.astype(float)):
    adj.setdefault(f, []).append((t, w))
    adj.setdefault(t, []).append((f, w))

dist = {src: 0.0}
prev = {}
pq = [(0.0, src)]
visited = set()
while pq:
    d, u = heapq.heappop(pq)
    if u in visited:
        continue
    visited.add(u)
    if u == tgt:
        break
    for v, w in adj.get(u, ()):
        nd = d + w
        if nd < dist.get(v, math.inf):
            dist[v] = nd
            prev[v] = u
            heapq.heappush(pq, (nd, v))

print('reachable:', tgt in dist)
if tgt in dist:
    path = [tgt]
    while path[-1] != src:
        path.append(prev[path[-1]])
    path.reverse()
    print('distance', dist[tgt], 'nodes', len(path), 'edges', len(path)-1)
    res = {"source": src, "target": tgt, "distance_m": round(dist[tgt], 3), "path_node_count": len(path)}
    with open('result.json', 'w', encoding='utf-8') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False))

# ─── Observations ───
# src present: True tgt present: True n_nodes: 38877
# bad lengths: 0 0
# reachable: True
# distance 5004.199999999998 nodes 61 edges 60
# {"source": "N10029499416", "target": "N9988513543", "distance_m": 5004.2, "path_node_count": 61}
