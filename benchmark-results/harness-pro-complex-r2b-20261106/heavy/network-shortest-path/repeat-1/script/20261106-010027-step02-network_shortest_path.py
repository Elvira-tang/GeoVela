# ─── OpenGIS Agent · run f5d08e50 · step 2 · network_shortest_path ───
# Timestamp : 2026-11-06T01:00:27
# Semantic : network_shortest_path
# Metadata : 20261106-010027-step02-network_shortest_path.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import pandas as pd
import json, heapq, math

df = pd.read_csv('edges.csv')
nodes = set(df['from_node']) | set(df['to_node'])
src, tgt = 'N10029499416', 'N9988513543'
print('nodes', len(nodes), 'src in nodes', src in nodes, 'tgt in nodes', tgt in nodes)

adj = {}
for f, t, w in zip(df['from_node'], df['to_node'], df['length_m']):
    if not isinstance(w, (int, float)) or pd.isna(w) or w < 0:
        continue
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
        if nd < dist.get(v, math.inf) - 1e-12:
            dist[v] = nd
            prev[v] = u
            heapq.heappush(pq, (nd, v))

path = None
if tgt in dist:
    path = [tgt]
    while path[-1] != src:
        path.append(prev[path[-1]])
    path.reverse()

print('reachable', path is not None)
assert path is not None, 'target not reachable from source'

result = {
    'source': src,
    'target': tgt,
    'distance_m': round(float(dist[tgt]), 3),
    'path_node_count': len(path),
}
with open('result.json', 'w', encoding='utf-8') as fh:
    json.dump(result, fh, ensure_ascii=False, indent=2)

edge_w = {}
for f, t, w in zip(df['from_node'], df['to_node'], df['length_m']):
    edge_w[(f, t)] = min(w, edge_w.get((f, t), math.inf))
    edge_w[(t, f)] = min(w, edge_w.get((t, f), math.inf))

step_sum = sum(edge_w[(a, b)] for a, b in zip(path, path[1:]))

with open('result.json', encoding='utf-8') as fh:
    loaded = json.load(fh)

checks = {
    'json_matches': loaded == result,
    'source_matches': loaded['source'] == src,
    'target_matches': loaded['target'] == tgt,
    'distance_matches': abs(loaded['distance_m'] - step_sum) < 1e-3,
    'node_count_matches': loaded['path_node_count'] == len(path) == len(set(path)),
    'edges_exist': all((a, b) in edge_w for a, b in zip(path, path[1:])),
    'path_starts_at_source': path[0] == src,
    'path_ends_at_target': path[-1] == tgt,
}
print(json.dumps(result, ensure_ascii=False))
print('recomputed_acc_length_m', round(step_sum, 3))
print('checks', checks)
print('all_ok', all(checks.values()))

# ─── Observations ───
# nodes 38877 src in nodes True tgt in nodes True
# reachable True
# dist 5004.199999999998 nodes 61
# ['N10029499416', 'N7610822016', 'N1441349799', 'N2461166769', 'N1441349802', 'N7509056300', 'N2429845238', 'N2461167547', 'N1441349800', 'N4198794326'] ... ['N11005391922', 'N2706614888', 'N2706614899', 'N2706614898', 'N9988513543']
# self-check sum 5004.2
