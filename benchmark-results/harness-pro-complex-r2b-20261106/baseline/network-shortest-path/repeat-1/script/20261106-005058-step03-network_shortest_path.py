# ─── OpenGIS Agent · run 5db1861b · step 3 · network_shortest_path ───
# Timestamp : 2026-11-06T00:50:58
# Semantic : network_shortest_path
# Metadata : 20261106-005058-step03-network_shortest_path.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import pandas as pd, heapq, json

SRC, DST = 'N10029499416', 'N9988513543'
df = pd.read_csv('edges.csv')
adj = {}
for u, v, w in zip(df['from_node'], df['to_node'], df['length_m']):
    adj.setdefault(u, []).append((v, float(w)))
    adj.setdefault(v, []).append((u, float(w)))

dist = {SRC: 0.0}
prev = {SRC: None}
pq = [(0.0, SRC)]
done = set()
while pq:
    d, u = heapq.heappop(pq)
    if u in done:
        continue
    done.add(u)
    if u == DST:
        break
    for v, w in adj.get(u, ()):
        nd = d + w
        if nd < dist.get(v, float('inf')):
            dist[v] = nd
            prev[v] = u
            heapq.heappush(pq, (nd, v))

path = []
cur = DST
while cur is not None:
    path.append(cur)
    cur = prev[cur]
path.reverse()

# independent check: sum edge lengths along path using undirected lookup
wl = {}
for u, v, w in zip(df['from_node'], df['to_node'], df['length_m']):
    wl[(u, v)] = min(wl.get((u, v), float('inf')), float(w))
    wl[(v, u)] = min(wl.get((v, u), float('inf')), float(w))
recomputed = round(sum(wl[(a, b)] for a, b in zip(path[:-1], path[1:])), 3)

result = {
    "source": SRC,
    "target": DST,
    "distance_m": round(dist[DST], 3),
    "path_node_count": len(path),
}
with open('result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2)

print(result)
print('recomputed_distance', recomputed, 'match', abs(recomputed - result['distance_m']) < 1e-6)
print('path endpoints ok', path[0] == SRC, path[-1] == DST)
print('all path edges exist', all((a, b) in wl for a, b in zip(path[:-1], path[1:])))
print('path_nodes', len(path), 'unique', len(set(path)))

# ─── Observations ───
# {'source': 'N10029499416', 'target': 'N9988513543', 'distance_m': 5004.2, 'path_node_count': 61}
# recomputed_distance 5004.2 match True
# path endpoints ok True True
# all path edges exist True
# path_nodes 61 unique 61
