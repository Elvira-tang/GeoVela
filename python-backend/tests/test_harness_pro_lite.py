import unittest
from pathlib import Path

from opengis_backend.agent.evolution.benchmark import (
    build_complex_tasks,
    build_real_tasks,
    validate_result,
)
from opengis_backend.agent.evolution.harness_pro_lite import (
    EvaluationObservation,
    aggregate_observations,
    evolve_seed_profiles,
    select_representatives,
)
from opengis_backend.agent.governance.profile import AgentProfile


class HarnessProLiteTests(unittest.TestCase):
    def test_real_benchmark_tasks_have_deterministic_expected_results(self) -> None:
        root = Path(__file__).resolve().parents[2]
        tasks = build_real_tasks(root)

        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0].expected["row_count"], 234)
        self.assertEqual(tasks[1].expected["row_count"], 1654)
        self.assertEqual(tasks[2].expected["row_count"], 5500)

    def test_complex_benchmark_covers_five_capabilities(self) -> None:
        root = Path(__file__).resolve().parents[2]
        tasks = build_complex_tasks(root)

        self.assertEqual(
            {task.task_id for task in tasks},
            {
                "coordinate-transform",
                "spatial-join",
                "network-shortest-path",
                "error-recovery",
                "map-state-validation",
            },
        )
        self.assertEqual(next(x for x in tasks if x.task_id == "map-state-validation").expected["layer_count"], 3)

    def test_result_validator_is_exact(self) -> None:
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text(json.dumps({"row_count": 3}), encoding="utf-8")
            self.assertEqual(validate_result(path, {"row_count": 3}), (True, ""))
            passed, message = validate_result(path, {"row_count": 4})
            self.assertFalse(passed)
            self.assertIn("mismatch", message)

    def test_candidates_preserve_safety_contract(self) -> None:
        seed = AgentProfile.gis_build()
        candidates = evolve_seed_profiles(seed)

        self.assertEqual(set(candidates), {"baseline", "lite", "medium", "heavy"})
        self.assertIs(candidates["baseline"], seed)
        self.assertEqual(candidates["baseline"].prompt_suffix, seed.prompt_suffix)
        self.assertEqual(candidates["baseline"].metadata, seed.metadata)
        for name, profile in candidates.items():
            self.assertEqual(profile.permission_level, seed.permission_level)
            self.assertEqual(profile.tool_groups, seed.tool_groups)
            if name != "baseline":
                self.assertIn("verify", profile.prompt_suffix.lower())
        self.assertEqual(candidates["lite"].metadata["max_work_steps"], 10)
        self.assertEqual(candidates["heavy"].metadata["max_work_steps"], 30)

    def test_aggregate_observations(self) -> None:
        observations = [
            EvaluationObservation("baseline", "load", True, 100, 1000, 2, 0),
            EvaluationObservation("baseline", "style", False, 300, 3000, 4, 1),
        ]
        metric = aggregate_observations(observations)[0]

        self.assertEqual(metric.pass_rate, 0.5)
        self.assertEqual(metric.mean_tokens, 200)
        self.assertEqual(metric.mean_latency_ms, 2000)
        self.assertEqual(metric.mean_errors, 0.5)

    def test_selection_applies_floor_and_pareto_frontier(self) -> None:
        rows = []
        values = {
            "baseline": ([True, True, False, False], 1000),
            "cheap_but_bad": ([True, False, False, False], 100),
            "lite_candidate": ([True, True, False, False], 500),
            "balanced_candidate": ([True, True, True, False], 700),
            "heavy_candidate": ([True, True, True, True], 1200),
            "dominated": ([True, True, False, False], 900),
        }
        for candidate, (passes, tokens) in values.items():
            for index, passed in enumerate(passes):
                rows.append(EvaluationObservation(candidate, f"task-{index}", passed, tokens))

        report = select_representatives(aggregate_observations(rows))

        self.assertNotIn("cheap_but_bad", report.eligible)
        self.assertNotIn("baseline", report.pareto_frontier)
        self.assertNotIn("dominated", report.pareto_frontier)
        self.assertEqual(
            set(report.pareto_frontier),
            {"lite_candidate", "balanced_candidate", "heavy_candidate"},
        )
        self.assertEqual(report.selected["lite"], "lite_candidate")
        self.assertEqual(report.selected["medium"], "balanced_candidate")
        self.assertEqual(report.selected["heavy"], "heavy_candidate")

    def test_selection_rejects_unequal_task_counts(self) -> None:
        metrics = aggregate_observations(
            [
                EvaluationObservation("baseline", "a", True),
                EvaluationObservation("candidate", "a", True),
                EvaluationObservation("candidate", "b", True),
            ]
        )
        with self.assertRaisesRegex(ValueError, "same number"):
            select_representatives(metrics)


if __name__ == "__main__":
    unittest.main()
