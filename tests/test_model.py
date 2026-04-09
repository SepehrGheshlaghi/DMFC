from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dmfc_reference import (
    DMFCParameters,
    compute_effective_properties,
    evaluate_operating_point,
    operating_point,
    simulate_assignment,
    simulate_case,
)


class DMFCReferenceModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = DMFCParameters(n_points=60)
        self.props = compute_effective_properties(self.params)

    def test_effective_properties_are_positive(self) -> None:
        self.assertGreater(self.props.diffusion_meoh_cl_cm2_s, 0.0)
        self.assertGreater(self.props.diffusion_meoh_membrane_cm2_s, 0.0)
        self.assertGreater(self.props.diffusion_o2_cl_cm2_s, 0.0)
        self.assertGreater(self.props.exchange_current_meoh_a_cm2, 0.0)
        self.assertGreater(self.props.exchange_current_o2_a_cm2, 0.0)

    def test_assignment_cases_are_returned(self) -> None:
        results = simulate_assignment(self.params, self.props)
        self.assertEqual(len(results), 3)
        self.assertEqual(
            tuple(result.methanol_bulk_molarity for result in results),
            (0.5, 1.0, 3.0),
        )

    def test_open_circuit_crossover_increases_with_methanol_feed(self) -> None:
        low = operating_point(0.5 / 1000.0, 0.0, self.params, self.props, True)
        high = operating_point(3.0 / 1000.0, 0.0, self.params, self.props, True)
        self.assertGreater(
            high.methanol_crossover_current_density_a_cm2,
            low.methanol_crossover_current_density_a_cm2,
        )

    def test_crossover_reduces_cell_voltage(self) -> None:
        methanol_bulk = 1.0 / 1000.0
        current_density = 0.15
        with_crossover = operating_point(
            methanol_bulk, current_density, self.params, self.props, True
        )
        without_crossover = operating_point(
            methanol_bulk, current_density, self.params, self.props, False
        )
        voltage_with_crossover = evaluate_operating_point(
            methanol_bulk, with_crossover, self.params, self.props
        )
        voltage_without_crossover = evaluate_operating_point(
            methanol_bulk, without_crossover, self.params, self.props
        )
        self.assertGreater(
            voltage_without_crossover.cell_voltage_v, voltage_with_crossover.cell_voltage_v
        )

    def test_simulated_points_remain_physically_feasible(self) -> None:
        result = simulate_case(1.0, self.params, self.props)
        self.assertGreater(result.max_current_density_a_cm2, 0.0)
        for point in result.operating_points:
            self.assertGreater(point.methanol_concentration_cl_mem_mol_cm3, 0.0)
            self.assertGreater(point.oxygen_concentration_cl_mem_mol_cm3, 0.0)
            self.assertGreater(point.total_cathode_current_density_a_cm2, 0.0)


if __name__ == "__main__":
    unittest.main()
