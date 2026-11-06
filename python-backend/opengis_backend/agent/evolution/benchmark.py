"""Run a small, deterministic GeoVela GIS benchmark with a real model.

The benchmark uses copied real project data and validates machine-readable
artifacts.  It never asks an LLM judge whether a task passed.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import heapq
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from opengis_backend.agent.evolution.harness_pro_lite import (
    EvaluationObservation,
    aggregate_observations,
    evolve_seed_profiles,
    select_representatives,
)
from opengis_backend.agent.governance.profile import AgentProfile
from opengis_backend.agent.open_gis_agent import OpenGISAgent
from opengis_backend.tools.context import ToolContext
from opengis_backend.tools.registry import ToolRegistry


@dataclass(frozen=True)
class BenchmarkTask:
    task_id: str
    sources: dict[str, Path]
    prompt: str
    expected: dict[str, Any]
    corrupt_rows: int = 0
    map_state: dict[str, Any] | None = None


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def build_real_tasks(repo_root: Path) -> tuple[BenchmarkTask, ...]:
    campus = repo_root / "Data/CampusMap_Jiangnan_20261105/data/jiangnan_university_campus.csv"
    milktea = repo_root / "Data/MilkTea_Wuxi_20261105/data/wuxi_milktea_poi.csv"
    access = repo_root / (
        "Data/Dorm_MilkTea_Metro_Accessibility_20261105/data/processed/"
        "accessibility_results.csv"
    )
    campus_rows = _read_csv(campus)
    milktea_rows = _read_csv(milktea)
    access_rows = _read_csv(access)
    category_counts: dict[str, int] = {}
    for row in campus_rows:
        category = row["类别"]
        category_counts[category] = category_counts.get(category, 0) + 1
    district_counts: dict[str, int] = {}
    for row in milktea_rows:
        district = row["区县"]
        district_counts[district] = district_counts.get(district, 0) + 1
    min_total = min(float(row["total_min"]) for row in access_rows)
    return (
        BenchmarkTask(
            "campus-summary",
            {"input.csv": campus},
            "Read input.csv. Write result.json as UTF-8 JSON with exactly: "
            "row_count (integer) and category_counts (object counting the Chinese 类别 column). "
            "Use a direct file/data tool or Python, verify the written file, then finish.",
            {"row_count": len(campus_rows), "category_counts": category_counts},
        ),
        BenchmarkTask(
            "milktea-summary",
            {"input.csv": milktea},
            "Read input.csv. Write result.json as UTF-8 JSON with exactly: "
            "row_count (integer) and district_counts (object counting the Chinese 区县 column). "
            "Verify the written file, then finish.",
            {"row_count": len(milktea_rows), "district_counts": district_counts},
        ),
        BenchmarkTask(
            "accessibility-minimum",
            {"input.csv": access},
            "Read input.csv. Write result.json as UTF-8 JSON with exactly: "
            "row_count (integer) and minimum_total_min (number, minimum of total_min). "
            "Verify the written file, then finish.",
            {"row_count": len(access_rows), "minimum_total_min": min_total},
        ),
    )


def _shortest_path_truth(edges_path: Path) -> tuple[str, str, float, int]:
    rows = _read_csv(edges_path)
    adjacency: dict[str, list[tuple[str, float]]] = {}
    for row in rows:
        left, right, weight = row["from_node"], row["to_node"], float(row["length_m"])
        adjacency.setdefault(left, []).append((right, weight))
        adjacency.setdefault(right, []).append((left, weight))
    component: set[str] = set()
    stack = [next(iter(adjacency))]
    while stack:
        node = stack.pop()
        if node in component:
            continue
        component.add(node)
        stack.extend(neighbor for neighbor, _ in adjacency[node] if neighbor not in component)
    source, target = min(component), max(component)
    distances = {source: 0.0}
    hops = {source: 1}
    queue = [(0.0, source)]
    while queue:
        distance, node = heapq.heappop(queue)
        if distance != distances.get(node):
            continue
        if node == target:
            break
        for neighbor, weight in adjacency[node]:
            candidate = distance + weight
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                hops[neighbor] = hops[node] + 1
                heapq.heappush(queue, (candidate, neighbor))
    return source, target, round(distances[target], 3), hops[target]


def build_complex_tasks(repo_root: Path) -> tuple[BenchmarkTask, ...]:
    campus = repo_root / "Data/CampusMap_Jiangnan_20261105/data/jiangnan_university_campus.csv"
    milktea = repo_root / "Data/MilkTea_Wuxi_20261105/data/wuxi_milktea_poi.csv"
    districts = repo_root / "Data/MilkTea_Wuxi_20261105/data/wuxi_districts.json"
    edges = repo_root / (
        "Data/Dorm_MilkTea_Metro_Accessibility_20261105/data/raw/walking_edges.csv"
    )
    campus_rows = _read_csv(campus)
    first = campus_rows[0]
    from pyproj import Transformer

    transformer = Transformer.from_crs(4326, 3857, always_xy=True)
    x, y = transformer.transform(float(first["经度"]), float(first["纬度"]))
    source, target, distance, path_nodes = _shortest_path_truth(edges)
    map_layers = [
        {"id": "campus-buildings", "name": "Campus Buildings", "visible": True, "type": "fill"},
        {"id": "milktea-poi", "name": "Milk Tea POI", "visible": True, "type": "circle"},
        {"id": "walking-network", "name": "Walking Network", "visible": False, "type": "line"},
    ]
    return (
        BenchmarkTask(
            "coordinate-transform",
            {"input.csv": campus},
            "Read the first data row of input.csv. Transform its Chinese 经度/纬度 from "
            "EPSG:4326 to EPSG:3857 using an appropriate geospatial library. Write result.json "
            "with source_name, x_3857 and y_3857, coordinates rounded to 3 decimals. Verify it.",
            {"source_name": first["名称"], "x_3857": round(x, 3), "y_3857": round(y, 3)},
        ),
        BenchmarkTask(
            "spatial-join",
            {"points.csv": milktea, "districts.geojson": districts},
            "Load points.csv using the WGS84 longitude/latitude columns and spatially join the "
            "points to districts.geojson. Write result.json with matched_count and "
            "district_counts keyed by polygon name. Exclude unmatched points and verify it.",
            _spatial_join_truth(milktea, districts),
        ),
        BenchmarkTask(
            "network-shortest-path",
            {"edges.csv": edges},
            f"Treat edges.csv as an undirected weighted graph using length_m. Find the shortest "
            f"path from {source} to {target}. Write result.json with source, target, "
            "distance_m rounded to 3 decimals, and path_node_count. Verify it.",
            {"source": source, "target": target, "distance_m": distance, "path_node_count": path_nodes},
        ),
        BenchmarkTask(
            "error-recovery",
            {"input.csv": milktea},
            "input.csv contains deliberately appended malformed rows. Parse it robustly using "
            "the WGS84 longitude/latitude columns. Reject rows whose coordinates are missing, "
            "non-numeric, or outside valid ranges. Write result.json with exactly two keys: "
            "valid_rows and rejected_rows, both integer counts. Do not include row arrays, "
            "diagnostics, source paths, metadata, or any other keys. Verify it.",
            {"valid_rows": len(_read_csv(milktea)), "rejected_rows": 3},
            corrupt_rows=3,
        ),
        BenchmarkTask(
            "map-state-validation",
            {},
            "Call list_layers to read the live map state; do not infer it from this prompt. "
            "Write result.json with layer_count, visible_count and layer_ids in returned order. "
            "Verify the written file.",
            {"layer_count": 3, "visible_count": 2, "layer_ids": [x["id"] for x in map_layers]},
            map_state={"layers": map_layers},
        ),
    )


def _spatial_join_truth(points_path: Path, districts_path: Path) -> dict[str, Any]:
    import geopandas as gpd
    import pandas as pd

    frame = pd.read_csv(points_path)
    points = gpd.GeoDataFrame(
        frame,
        geometry=gpd.points_from_xy(frame["经度(WGS84)"], frame["纬度(WGS84)"]),
        crs="EPSG:4326",
    )
    polygons = gpd.read_file(districts_path)[["name", "geometry"]]
    joined = gpd.sjoin(points, polygons, how="inner", predicate="within")
    name_column = "name_right" if "name_right" in joined.columns else "name"
    counts = {str(key): int(value) for key, value in joined[name_column].value_counts().sort_index().items()}
    return {"matched_count": len(joined), "district_counts": counts}


def validate_result(path: Path, expected: dict[str, Any]) -> tuple[bool, str]:
    if not path.exists():
        return False, "result.json missing"
    try:
        actual = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, f"invalid JSON: {exc}"
    if actual != expected:
        return False, f"result mismatch: expected={expected!r}, actual={actual!r}"
    return True, ""


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


async def _run_one(
    *,
    registry: ToolRegistry,
    model_config: dict[str, str],
    profile_name: str,
    profile: AgentProfile,
    task: BenchmarkTask,
    output_root: Path,
    repeat: int = 1,
) -> tuple[EvaluationObservation, dict[str, Any]]:
    workspace = output_root / profile_name / task.task_id / f"repeat-{repeat}"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    for destination, source in task.sources.items():
        shutil.copy2(source, workspace / destination)
    if task.corrupt_rows:
        input_path = workspace / "input.csv"
        with input_path.open("a", encoding="utf-8", newline="") as stream:
            stream.write("\nBROKEN-1,损坏数据,,,,,,,,,,not-a-number,31.5,,,,,,,,,")
            stream.write("\nBROKEN-2,缺失经度,,,,,,,,,,,31.5,,,,,,,,,")
            stream.write("\nBROKEN-3,超出范围,,,,,,,,,,999,999,,,,,,,,,")

    async def request_fn(method: str, params: dict) -> Any:
        if method == "rpc.ui.map.list_layers" and task.map_state is not None:
            return task.map_state
        raise RuntimeError(f"benchmark has no mock response for {method}")

    context = ToolContext(
        conversation_id=f"benchmark-{profile_name}-{task.task_id}",
        request_fn=request_fn,
        meta={"workspace_path": str(workspace), "agent_profile": profile},
    )
    agent = OpenGISAgent(
        registry,
        protocol=model_config["provider"],
        model=model_config["model"],
        api_key=model_config["api_key"],
        base_url=model_config["base_url"],
    )
    started = time.perf_counter()
    agent_error = ""
    try:
        async for event in agent.run(task.prompt, context=context):
            data = event.data if isinstance(event.data, dict) else {}
            if str(getattr(event.type, "value", event.type)) == "error":
                agent_error = str(data.get("error") or data)
    except Exception as exc:
        agent_error = f"{type(exc).__name__}: {exc}"
    latency_ms = (time.perf_counter() - started) * 1000
    passed, validation_error = validate_result(workspace / "result.json", task.expected)
    run_dirs = sorted((workspace / ".opengis/runs").glob("*"), key=lambda p: p.stat().st_mtime)
    run_dir = run_dirs[-1] if run_dirs else None
    usage_rows = _jsonl(run_dir / "llm_usage.jsonl") if run_dir else []
    total_tokens = sum(int((row.get("usage") or {}).get("total_tokens") or 0) for row in usage_rows)
    tool_rows = _jsonl(run_dir / "tool_calls.jsonl") if run_dir else []
    errors = sum(bool(row.get("error")) for row in tool_rows) + int(bool(agent_error))
    observation = EvaluationObservation(
        candidate=profile_name,
        task_id=f"{task.task_id}#repeat-{repeat}",
        passed=passed and not agent_error,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        tool_calls=len(tool_rows),
        errors=errors,
    )
    detail = {
        **asdict(observation),
        "workspace": str(workspace),
        "validation_error": validation_error[:2000],
        "agent_error": agent_error[:2000],
    }
    return observation, detail


async def run_benchmark(
    repo_root: Path,
    settings_path: Path,
    output_root: Path,
    *,
    suite: str = "basic",
    repeats: int = 1,
    task_filter: set[str] | None = None,
) -> dict[str, Any]:
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    model = settings.get("model") or {}
    model_config = {
        "provider": str(model.get("provider") or "openai"),
        "model": str(model.get("modelName") or ""),
        "api_key": str(model.get("apiKey") or ""),
        "base_url": str(model.get("baseURL") or ""),
    }
    if not model_config["model"] or not model_config["api_key"]:
        raise RuntimeError("GeoVela model name or API key is missing")
    registry = ToolRegistry()
    await registry.discover_and_load()
    candidates = evolve_seed_profiles(AgentProfile.gis_build())
    tasks = build_complex_tasks(repo_root) if suite == "complex" else build_real_tasks(repo_root)
    if task_filter:
        tasks = tuple(task for task in tasks if task.task_id in task_filter)
        if not tasks:
            raise ValueError(f"no tasks match filter: {sorted(task_filter)}")
    observations: list[EvaluationObservation] = []
    details: list[dict[str, Any]] = []
    output_root.mkdir(parents=True, exist_ok=True)
    for candidate_name, profile in candidates.items():
        for task in tasks:
            for repeat in range(1, repeats + 1):
                observation, detail = await _run_one(
                    registry=registry,
                    model_config=model_config,
                    profile_name=candidate_name,
                    profile=profile,
                    task=task,
                    output_root=output_root,
                    repeat=repeat,
                )
                observations.append(observation)
                details.append(detail)
                # Windows terminals may use GBK; escaped JSON keeps progress
                # reporting from aborting an otherwise valid benchmark run.
                print(json.dumps(detail, ensure_ascii=True), flush=True)
    metrics = aggregate_observations(observations)
    report = select_representatives(metrics)
    payload = {
        "model": {k: v for k, v in model_config.items() if k != "api_key"},
        "tasks": [task.task_id for task in tasks],
        "suite": suite,
        "repeats": repeats,
        "details": details,
        "evolution": report.to_dict(),
    }
    (output_root / "benchmark_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--suite", choices=("basic", "complex"), default="basic")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--tasks", default="", help="comma-separated task ids")
    args = parser.parse_args()
    asyncio.run(
        run_benchmark(
            args.repo_root.resolve(),
            args.settings.resolve(),
            args.output.resolve(),
            suite=args.suite,
            repeats=max(1, args.repeats),
            task_filter={item.strip() for item in args.tasks.split(",") if item.strip()} or None,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
