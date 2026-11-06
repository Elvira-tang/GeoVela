"""A safe first version of HarnessPro-style evolution for GeoVela.

This module deliberately evolves only declarative :class:`AgentProfile`
settings.  It does not rewrite Python source, permissions, or tool
implementations.  Candidate profiles are evaluated externally and selected
using a correctness floor followed by performance/cost Pareto filtering.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Iterable, Mapping, Sequence

from opengis_backend.agent.governance.profile import AgentProfile


EVOLUTION_PROMPT = """
## GeoVela execution profile

Use the available GIS tools directly and verify their structured results.
Do not repeat successful read-only calls. Prefer an existing Operation over
new Python for reusable analysis. Before finishing, verify every durable
artifact or map mutation once; avoid redundant verification after success.
When the user specifies an exact output schema, emit only those keys and no
diagnostic arrays, provenance blocks, or additional metadata.
""".strip()


@dataclass(frozen=True)
class EvaluationObservation:
    """One repeatable task result for one candidate profile."""

    candidate: str
    task_id: str
    passed: bool
    total_tokens: int = 0
    latency_ms: float = 0.0
    tool_calls: int = 0
    errors: int = 0

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "EvaluationObservation":
        return cls(
            candidate=str(value["candidate"]),
            task_id=str(value["task_id"]),
            passed=bool(value["passed"]),
            total_tokens=max(0, int(value.get("total_tokens") or 0)),
            latency_ms=max(0.0, float(value.get("latency_ms") or 0.0)),
            tool_calls=max(0, int(value.get("tool_calls") or 0)),
            errors=max(0, int(value.get("errors") or 0)),
        )


@dataclass(frozen=True)
class CandidateMetrics:
    candidate: str
    task_count: int
    pass_rate: float
    mean_tokens: float
    mean_latency_ms: float
    mean_tool_calls: float
    mean_errors: float

    @property
    def cost_score(self) -> float:
        """Provider-neutral cost proxy suitable for offline evaluation."""

        return self.mean_tokens

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvolutionReport:
    baseline: str
    performance_floor: float
    metrics: tuple[CandidateMetrics, ...]
    eligible: tuple[str, ...]
    pareto_frontier: tuple[str, ...]
    selected: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline": self.baseline,
            "performance_floor": self.performance_floor,
            "metrics": [metric.to_dict() for metric in self.metrics],
            "eligible": list(self.eligible),
            "pareto_frontier": list(self.pareto_frontier),
            "selected": dict(self.selected),
        }


def evolve_seed_profiles(seed: AgentProfile) -> dict[str, AgentProfile]:
    """Generate a fixed, auditable first population from ``seed``.

    Budgets are intentionally conservative.  Permission level and tool groups
    are inherited exactly, keeping evolution out of GeoVela's safety boundary.
    """

    variants = {
        "baseline": {},
        "lite": {
            "max_provider_turns": 6,
            "max_code_steps": 2,
            "max_tool_steps": 10,
            "max_work_steps": 10,
        },
        "medium": {
            "max_provider_turns": 10,
            "max_code_steps": 4,
            "max_tool_steps": 18,
            "max_work_steps": 18,
        },
        "heavy": {
            "max_provider_turns": 16,
            "max_code_steps": 8,
            "max_tool_steps": 30,
            "max_work_steps": 30,
        },
    }
    candidates: dict[str, AgentProfile] = {}
    for name, budget in variants.items():
        if name == "baseline":
            # The control must remain byte-for-byte equivalent to the seed
            # behavior.  Adding the evolution prompt to the baseline would
            # contaminate the comparison and understate the treatment effect.
            candidates[name] = seed
            continue
        metadata = dict(seed.metadata)
        metadata.update(budget)
        candidates[name] = replace(
            seed,
            name=f"{seed.name}-{name}",
            prompt_suffix=(seed.prompt_suffix.rstrip() + "\n\n" + EVOLUTION_PROMPT).strip(),
            metadata=metadata,
        )
    return candidates


def aggregate_observations(
    observations: Iterable[EvaluationObservation],
) -> tuple[CandidateMetrics, ...]:
    grouped: dict[str, list[EvaluationObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.candidate, []).append(observation)
    metrics: list[CandidateMetrics] = []
    for candidate, rows in sorted(grouped.items()):
        count = len(rows)
        if count == 0:
            continue
        metrics.append(
            CandidateMetrics(
                candidate=candidate,
                task_count=count,
                pass_rate=sum(row.passed for row in rows) / count,
                mean_tokens=sum(row.total_tokens for row in rows) / count,
                mean_latency_ms=sum(row.latency_ms for row in rows) / count,
                mean_tool_calls=sum(row.tool_calls for row in rows) / count,
                mean_errors=sum(row.errors for row in rows) / count,
            )
        )
    return tuple(metrics)


def _dominates(left: CandidateMetrics, right: CandidateMetrics) -> bool:
    no_worse = left.pass_rate >= right.pass_rate and left.cost_score <= right.cost_score
    strictly_better = left.pass_rate > right.pass_rate or left.cost_score < right.cost_score
    return no_worse and strictly_better


def _normalized_distance(
    metric: CandidateMetrics,
    frontier: Sequence[CandidateMetrics],
    *,
    performance_weight: float,
) -> float:
    pass_values = [item.pass_rate for item in frontier]
    cost_values = [item.cost_score for item in frontier]
    pass_span = max(pass_values) - min(pass_values)
    cost_span = max(cost_values) - min(cost_values)
    performance_gap = (max(pass_values) - metric.pass_rate) / pass_span if pass_span else 0.0
    cost_gap = (metric.cost_score - min(cost_values)) / cost_span if cost_span else 0.0
    cost_weight = 1.0 - performance_weight
    return performance_weight * performance_gap**2 + cost_weight * cost_gap**2


def select_representatives(
    metrics: Sequence[CandidateMetrics], *, baseline: str = "baseline"
) -> EvolutionReport:
    """Apply a baseline floor, Pareto filter, then select three operating modes."""

    by_name = {metric.candidate: metric for metric in metrics}
    if baseline not in by_name:
        raise ValueError(f"baseline candidate not found: {baseline}")
    task_counts = {metric.task_count for metric in metrics}
    if len(task_counts) > 1:
        raise ValueError("all candidates must be evaluated on the same number of tasks")
    floor = by_name[baseline].pass_rate
    eligible_metrics = [metric for metric in metrics if metric.pass_rate >= floor]
    frontier = [
        metric
        for metric in eligible_metrics
        if not any(_dominates(other, metric) for other in eligible_metrics if other != metric)
    ]
    if not frontier:
        raise ValueError("no candidate remains after filtering")
    frontier.sort(key=lambda item: item.candidate)
    # The outer modes intentionally sit close to the two Pareto extremes;
    # otherwise a squared-distance objective can collapse Lite/Medium or
    # Medium/Heavy onto the same compromise candidate on a small frontier.
    weights = {"lite": 0.05, "medium": 0.5, "heavy": 0.95}
    selected = {
        mode: min(
            frontier,
            key=lambda item: (
                _normalized_distance(item, frontier, performance_weight=weight),
                item.cost_score,
                item.candidate,
            ),
        ).candidate
        for mode, weight in weights.items()
    }
    return EvolutionReport(
        baseline=baseline,
        performance_floor=floor,
        metrics=tuple(metrics),
        eligible=tuple(sorted(item.candidate for item in eligible_metrics)),
        pareto_frontier=tuple(item.candidate for item in frontier),
        selected=selected,
    )
