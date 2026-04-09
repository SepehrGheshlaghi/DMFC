from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dmfc_reference import DMFCParameters, compute_effective_properties, simulate_assignment, summarise_results
from dmfc_reference.export import export_assignment_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the assignment-focused DMFC reference model and export CSV/SVG outputs."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs",
        help="Directory used for generated figures and data.",
    )
    parser.add_argument(
        "--points",
        type=int,
        default=400,
        help="Number of current-density points per methanol case.",
    )
    parser.add_argument(
        "--drag-coefficient",
        type=float,
        default=0.0,
        help="Optional electro-osmotic drag coefficient for methanol crossover.",
    )
    parser.add_argument(
        "--methanol-molarities",
        type=float,
        nargs="+",
        default=[0.5, 1.0, 3.0],
        help="Methanol feed molarities in mol L^-1.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    params = DMFCParameters(
        n_points=args.points,
        drag_coefficient=args.drag_coefficient,
        methanol_bulk_molarities=tuple(args.methanol_molarities),
    )
    props = compute_effective_properties(params)
    results = simulate_assignment(params, props)
    generated = export_assignment_outputs(results, args.output_dir, params, props)

    print("Generated DMFC reference outputs")
    for row in summarise_results(results, params, props):
        print(
            "  "
            f"{row['methanol_bulk_molarity_M']:.1f} M | "
            f"j_max = {row['max_current_density_A_cm2']:.3f} A/cm^2 | "
            f"peak power = {row['peak_power_density_W_cm2']:.3f} W/cm^2 at "
            f"{row['peak_power_current_density_A_cm2']:.3f} A/cm^2 | "
            f"OC crossover = {row['open_circuit_crossover_current_density_A_cm2']:.3f} A/cm^2"
        )

    print(f"Summary: {Path(generated['summary_file']).resolve()}")
    print(f"Data:    {Path(generated['data_dir']).resolve()}")
    print(f"Figures: {Path(generated['figures_dir']).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
