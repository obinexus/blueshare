#!/usr/bin/env python3
"""Command-line runner for the BlueShare spatial MVP acceptance scenario."""

from __future__ import annotations

import argparse
from pathlib import Path

from spatial_mvp.scenario import run_acceptance


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run BlueShare metre-based spatial MMUKO acceptance"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "reports",
        help="Directory for timestamped JSON and CSV evidence",
    )
    parser.add_argument(
        "--tolerance-m",
        type=float,
        default=0.01,
        help="Maximum simulated distance and symmetry error in metres",
    )
    args = parser.parse_args()

    report, json_path, csv_path = run_acceptance(
        args.output_dir, tolerance_m=args.tolerance_m
    )
    summary = report["summary"]
    print(f"BlueShare spatial acceptance: {summary['status']}")
    print(f"Measurement source: {report['measurement_source']}")
    print(f"Units: {report['units']}")
    print(f"Distance samples: {summary['distance_samples']}")
    print(f"Max absolute error: {summary['max_absolute_error_m']:.6f} m")
    print(f"Max symmetry delta: {summary['max_symmetry_delta_m']:.6f} m")
    print(f"JSON report: {json_path.resolve()}")
    print(f"CSV report: {csv_path.resolve()}")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

