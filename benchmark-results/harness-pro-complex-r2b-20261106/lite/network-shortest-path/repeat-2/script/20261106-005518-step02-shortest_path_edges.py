# ─── OpenGIS Agent · run 15c0dcf1 · step 2 · shortest_path_edges ───
# Timestamp : 2026-11-06T00:55:18
# Semantic : shortest_path_edges
# Metadata : 20261106-005518-step02-shortest_path_edges.metadata.json
# User query: Treat edges.csv as an undirected weighted graph using length_m. Find the shortest path from N10029499416 to N9988513543. Write result.json with source, target, distance_m rounded to 3 decimals, and pa…
import pandas as pd, networkx as nx, json, math

SOURCE = "N10029499416"
TARGET = "N9988513543"

df = pd.read_csv("edges.csv")
nodes = set(df.from_node) | set(df.to_node)
print("nodes:", len(nodes), "source in graph:", SOURCE in nodes, "target in graph:", TARGET in nodes)

G = nx.Graph()
for r in df.itertuples(index=False):
    a, b, w = r.from_node, r.to_node, float(r.length_m)
    if G.has_edge(a, b):
        if w < G[a][b]["weight"]:
            G[a][b]["weight"] = w
    else:
        G.add_edge(a, b, weight=w)
print("graph nodes/edges:", G.number_of_nodes(), G.number_of_edges())
print("positive weights only:", all(d["weight"] > 0 for _, _, d in G.edges(data=True)))

comp = nx.node_connected_component(G, SOURCE)
print("target in same component:", TARGET in comp, "component size:", len(comp))

path = nx.dijkstra_path(G, SOURCE, TARGET, weight="weight")
dist = sum(G[path[i]][path[i+1]]["weight"] for i in range(len(path)-1))
print("dijkstra sum:", dist, "path_node_count:", len(path))
print(path[:5], "...", path[-5:])

result = {"source": SOURCE, "target": TARGET, "distance_m": round(dist, 3), "path_node_count": len(path)}
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(result)

# ─── Observations ───
# Error: Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 468, in _run_exec
#     compiled = compile(code, "<agent>", "eval")
#                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "<agent>", line 1
#     import pandas as pd, networkx as nx, json, math
#     ^^^^^^
# SyntaxError: invalid syntax
# 
# During handling of the above exception, another exception occurred:
# 
# Traceback (most recent call last):
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 471, in _run_exec
#     exec(compile(code, "<agent>", "exec"), namespace, namespace)
#   File "<agent>", line 1, in <module>
#   File "D:\Study\大三\申威高级语言编译与程序设计\GIS\OpenGIS\python-backend\opengis_backend\agent\execution\subprocess_runner.py", line 277, in patched_import
#     result = _original_import(name, globals, locals, fromlist, level)
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# ModuleNotFoundError: No module named 'networkx'
# 
# --- stdout before error ---
