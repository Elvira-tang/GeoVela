"""CLI for selecting GeoVela agent profile candidates from JSON observations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from opengis_backend.agent.evolution.harness_pro_lite import (
    EvaluationObservation,
    aggregate_observations,
    select_representatives,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path, help="JSON array of evaluation observations")
    parser.add_argument("--baseline", default="baseline")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    raw = json.loads(args.observations.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise SystemExit("observations must be a JSON array")
    observations = [EvaluationObservation.from_dict(item) for item in raw]
    report = select_representatives(aggregate_observations(observations), baseline=args.baseline)
    text = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
