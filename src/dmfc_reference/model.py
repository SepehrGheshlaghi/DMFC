from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, log

EPSILON = 1.0e-12


def _positive(value: float, floor: float = EPSILON) -> float:
    return value if value > floor else floor


def _linear_space(start: float, stop: float, count: int) -> tuple[float, ...]:
    if count <= 1:
        return (stop,)
    step = (stop - start) / float(count - 1)
    return tuple(start + step * index for index in range(count))


@dataclass(frozen=True)
class DMFCParameters:
    temperature_k: float = 343.15
    gas_constant_j_mol_k: float = 8.314462618
    faraday_constant_c_mol: float = 96485.33212
    alpha_anode: float = 0.5
    alpha_cathode: float = 0.5
    n_electrons_methanol: int = 6
    n_electrons_oxygen: int = 4
    open_circuit_voltage_v: float = 1.21

    methanol_bulk_molarities: tuple[float, ...] = (0.5, 1.0, 3.0)
    methanol_reference_molarity: float = 1.0
    oxygen_partial_pressure_atm: float = 0.21
    oxygen_reference_pressure_atm: float = 1.0
    ideal_gas_constant_l_atm_mol_k: float = 0.082057

    diffusion_o2_cl_ref_cm2_s: float = 20.0e-4
    diffusion_o2_gdl_cm2_s: float = 50.0e-4
    diffusion_meoh_cl_ref_cm2_s: float = 2.8e-5
    diffusion_meoh_gdl_cm2_s: float = 8.7e-6
    diffusion_meoh_mem_ref_cm2_s: float = 4.9e-6

    exchange_current_meoh_ref_a_cm2: float = 9.425e-3
    exchange_current_o2_ref_a_cm2: float = 4.222e-3

    diffusion_activation_over_r_k: float = 2436.0
    exchange_current_meoh_activation_j_mol: float = 35570.0
    exchange_current_o2_activation_j_mol: float = 73200.0

    thickness_gdl_cm: float = 0.015
    thickness_cl_cm: float = 0.0023
    thickness_membrane_cm: float = 0.018
    membrane_conductivity_s_cm: float = 0.06

    drag_coefficient: float = 0.0
    n_points: int = 400
    safety_margin: float = 0.995

    higher_heating_value_j_mol: float = 733716.0
    lower_heating_value_j_mol: float = 644004.0

    def methanol_reference_concentration_mol_cm3(self) -> float:
        return self.methanol_reference_molarity / 1000.0

    def methanol_bulk_concentration_mol_cm3(self, molarity: float) -> float:
        return molarity / 1000.0

    def oxygen_bulk_concentration_mol_cm3(self) -> float:
        return (
            self.oxygen_partial_pressure_atm
            / (self.ideal_gas_constant_l_atm_mol_k * self.temperature_k)
        ) / 1000.0

    def oxygen_reference_concentration_mol_cm3(self) -> float:
        return (
            self.oxygen_reference_pressure_atm
            / (self.ideal_gas_constant_l_atm_mol_k * self.temperature_k)
        ) / 1000.0

    def voltage_equivalent_hhv(self) -> float:
        return self.higher_heating_value_j_mol / (
            self.n_electrons_methanol * self.faraday_constant_c_mol
        )

    def voltage_equivalent_lhv(self) -> float:
        return self.lower_heating_value_j_mol / (
            self.n_electrons_methanol * self.faraday_constant_c_mol
        )


@dataclass(frozen=True)
class EffectiveProperties:
    diffusion_o2_cl_cm2_s: float
    diffusion_o2_gdl_cm2_s: float
    diffusion_meoh_cl_cm2_s: float
    diffusion_meoh_gdl_cm2_s: float
    diffusion_meoh_membrane_cm2_s: float
    exchange_current_meoh_a_cm2: float
    exchange_current_o2_a_cm2: float


@dataclass(frozen=True)
class OperatingPoint:
    current_density_a_cm2: float
    total_cathode_current_density_a_cm2: float
    methanol_flux_total_mol_cm2_s: float
    methanol_crossover_flux_mol_cm2_s: float
    methanol_crossover_current_density_a_cm2: float
    methanol_concentration_gdl_cl_mol_cm3: float
    methanol_concentration_cl_mem_mol_cm3: float
    oxygen_concentration_cl_mem_mol_cm3: float


@dataclass(frozen=True)
class VoltageBreakdown:
    reversible_voltage_v: float
    anode_activation_overpotential_v: float
    anode_mass_transport_overpotential_v: float
    cathode_activation_overpotential_v: float
    cathode_mass_transport_overpotential_v: float
    ohmic_overpotential_v: float
    cell_voltage_v: float
    fuel_utilization: float
    efficiency_hhv: float
    efficiency_lhv: float


@dataclass(frozen=True)
class CaseResult:
    methanol_bulk_molarity: float
    methanol_bulk_concentration_mol_cm3: float
    reversible_voltage_v: float
    max_current_density_a_cm2: float
    peak_power_density_w_cm2: float
    peak_power_current_density_a_cm2: float
    operating_points: tuple[OperatingPoint, ...]
    anode_activation_overpotential_v: tuple[float, ...]
    anode_mass_transport_overpotential_v: tuple[float, ...]
    anode_overpotential_v: tuple[float, ...]
    cathode_activation_overpotential_v: tuple[float, ...]
    cathode_mass_transport_overpotential_v: tuple[float, ...]
    cathode_overpotential_v: tuple[float, ...]
    ohmic_overpotential_v: tuple[float, ...]
    crossover_loss_v: tuple[float, ...]
    cell_voltage_v: tuple[float, ...]
    efficiency_hhv: tuple[float, ...]
    efficiency_lhv: tuple[float, ...]

    @property
    def current_density_a_cm2(self) -> tuple[float, ...]:
        return tuple(point.current_density_a_cm2 for point in self.operating_points)

    @property
    def methanol_crossover_current_density_a_cm2(self) -> tuple[float, ...]:
        return tuple(
            point.methanol_crossover_current_density_a_cm2
            for point in self.operating_points
        )

    @property
    def methanol_concentration_cl_mem_mol_cm3(self) -> tuple[float, ...]:
        return tuple(
            point.methanol_concentration_cl_mem_mol_cm3
            for point in self.operating_points
        )

    @property
    def oxygen_concentration_cl_mem_mol_cm3(self) -> tuple[float, ...]:
        return tuple(
            point.oxygen_concentration_cl_mem_mol_cm3 for point in self.operating_points
        )

    def rows(self) -> tuple[dict[str, float], ...]:
        rows: list[dict[str, float]] = []
        for index, point in enumerate(self.operating_points):
            rows.append(
                {
                    "methanol_bulk_molarity_M": self.methanol_bulk_molarity,
                    "current_density_A_cm2": point.current_density_a_cm2,
                    "total_cathode_current_density_A_cm2": point.total_cathode_current_density_a_cm2,
                    "methanol_crossover_current_density_A_cm2": point.methanol_crossover_current_density_a_cm2,
                    "methanol_concentration_gdl_cl_mol_cm3": point.methanol_concentration_gdl_cl_mol_cm3,
                    "methanol_concentration_cl_mem_mol_cm3": point.methanol_concentration_cl_mem_mol_cm3,
                    "oxygen_concentration_cl_mem_mol_cm3": point.oxygen_concentration_cl_mem_mol_cm3,
                    "anode_activation_overpotential_V": self.anode_activation_overpotential_v[index],
                    "anode_mass_transport_overpotential_V": self.anode_mass_transport_overpotential_v[index],
                    "anode_overpotential_V": self.anode_overpotential_v[index],
                    "cathode_activation_overpotential_V": self.cathode_activation_overpotential_v[index],
                    "cathode_mass_transport_overpotential_V": self.cathode_mass_transport_overpotential_v[index],
                    "cathode_overpotential_V": self.cathode_overpotential_v[index],
                    "ohmic_overpotential_V": self.ohmic_overpotential_v[index],
                    "crossover_loss_V": self.crossover_loss_v[index],
                    "cell_voltage_V": self.cell_voltage_v[index],
                    "efficiency_HHV": self.efficiency_hhv[index],
                    "efficiency_LHV": self.efficiency_lhv[index],
                }
            )
        return tuple(rows)


def _arrhenius_transport(
    reference_value: float,
    reference_temperature_k: float,
    temperature_k: float,
    activation_over_r_k: float,
) -> float:
    return reference_value * exp(
        activation_over_r_k * ((1.0 / reference_temperature_k) - (1.0 / temperature_k))
    )


def _arrhenius_exchange_current(
    reference_value: float,
    reference_temperature_k: float,
    temperature_k: float,
    activation_energy_j_mol: float,
    gas_constant_j_mol_k: float,
) -> float:
    return reference_value * exp(
        (activation_energy_j_mol / gas_constant_j_mol_k)
        * ((1.0 / reference_temperature_k) - (1.0 / temperature_k))
    )


def compute_effective_properties(params: DMFCParameters) -> EffectiveProperties:
    return EffectiveProperties(
        diffusion_o2_cl_cm2_s=_arrhenius_transport(
            params.diffusion_o2_cl_ref_cm2_s,
            353.0,
            params.temperature_k,
            params.diffusion_activation_over_r_k,
        ),
        diffusion_o2_gdl_cm2_s=params.diffusion_o2_gdl_cm2_s,
        diffusion_meoh_cl_cm2_s=_arrhenius_transport(
            params.diffusion_meoh_cl_ref_cm2_s,
            353.0,
            params.temperature_k,
            params.diffusion_activation_over_r_k,
        ),
        diffusion_meoh_gdl_cm2_s=params.diffusion_meoh_gdl_cm2_s,
        diffusion_meoh_membrane_cm2_s=_arrhenius_transport(
            params.diffusion_meoh_mem_ref_cm2_s,
            333.0,
            params.temperature_k,
            params.diffusion_activation_over_r_k,
        ),
        exchange_current_meoh_a_cm2=_arrhenius_exchange_current(
            params.exchange_current_meoh_ref_a_cm2,
            353.0,
            params.temperature_k,
            params.exchange_current_meoh_activation_j_mol,
            params.gas_constant_j_mol_k,
        ),
        exchange_current_o2_a_cm2=_arrhenius_exchange_current(
            params.exchange_current_o2_ref_a_cm2,
            353.0,
            params.temperature_k,
            params.exchange_current_o2_activation_j_mol,
            params.gas_constant_j_mol_k,
        ),
    )


def _anode_resistance_s_cm(params: DMFCParameters, props: EffectiveProperties) -> float:
    return (
        params.thickness_gdl_cm / props.diffusion_meoh_gdl_cm2_s
        + params.thickness_cl_cm / props.diffusion_meoh_cl_cm2_s
    )


def _membrane_resistance_s_cm(
    params: DMFCParameters, props: EffectiveProperties
) -> float:
    return params.thickness_membrane_cm / props.diffusion_meoh_membrane_cm2_s


def _cathode_resistance_s_cm(params: DMFCParameters, props: EffectiveProperties) -> float:
    return (
        params.thickness_gdl_cm / props.diffusion_o2_gdl_cm2_s
        + params.thickness_cl_cm / props.diffusion_o2_cl_cm2_s
    )


def operating_point(
    methanol_bulk_concentration_mol_cm3: float,
    current_density_a_cm2: float,
    params: DMFCParameters,
    props: EffectiveProperties,
    include_crossover: bool = True,
) -> OperatingPoint:
    n_rxn = current_density_a_cm2 / (
        params.n_electrons_methanol * params.faraday_constant_c_mol
    )
    anode_resistance = _anode_resistance_s_cm(params, props)
    membrane_resistance = _membrane_resistance_s_cm(params, props)
    gdl_resistance = params.thickness_gdl_cm / props.diffusion_meoh_gdl_cm2_s
    cl_resistance = params.thickness_cl_cm / props.diffusion_meoh_cl_cm2_s

    if include_crossover:
        drag_flux = params.drag_coefficient * current_density_a_cm2 / params.faraday_constant_c_mol
        total_flux = (
            n_rxn + drag_flux + methanol_bulk_concentration_mol_cm3 / membrane_resistance
        ) / (1.0 + anode_resistance / membrane_resistance)
        crossover_flux = total_flux - n_rxn
    else:
        total_flux = n_rxn
        crossover_flux = 0.0

    concentration_gdl_cl = methanol_bulk_concentration_mol_cm3 - total_flux * gdl_resistance
    concentration_cl_mem = concentration_gdl_cl - total_flux * cl_resistance
    crossover_current = (
        params.n_electrons_methanol
        * params.faraday_constant_c_mol
        * crossover_flux
    )
    total_cathode_current = current_density_a_cm2 + crossover_current

    oxygen_bulk = params.oxygen_bulk_concentration_mol_cm3()
    cathode_resistance = _cathode_resistance_s_cm(params, props)
    oxygen_flux = total_cathode_current / (
        params.n_electrons_oxygen * params.faraday_constant_c_mol
    )
    concentration_oxygen_cl_mem = oxygen_bulk - oxygen_flux * cathode_resistance

    return OperatingPoint(
        current_density_a_cm2=current_density_a_cm2,
        total_cathode_current_density_a_cm2=total_cathode_current,
        methanol_flux_total_mol_cm2_s=total_flux,
        methanol_crossover_flux_mol_cm2_s=crossover_flux,
        methanol_crossover_current_density_a_cm2=crossover_current,
        methanol_concentration_gdl_cl_mol_cm3=concentration_gdl_cl,
        methanol_concentration_cl_mem_mol_cm3=concentration_cl_mem,
        oxygen_concentration_cl_mem_mol_cm3=concentration_oxygen_cl_mem,
    )


def reversible_voltage(
    methanol_bulk_concentration_mol_cm3: float, params: DMFCParameters
) -> float:
    methanol_ratio = methanol_bulk_concentration_mol_cm3 / _positive(
        params.methanol_reference_concentration_mol_cm3()
    )
    oxygen_ratio = params.oxygen_bulk_concentration_mol_cm3() / _positive(
        params.oxygen_reference_concentration_mol_cm3()
    )
    return params.open_circuit_voltage_v + (
        params.gas_constant_j_mol_k
        * params.temperature_k
        / (params.n_electrons_methanol * params.faraday_constant_c_mol)
    ) * log(_positive(methanol_ratio * (oxygen_ratio ** 1.5)))


def evaluate_operating_point(
    methanol_bulk_concentration_mol_cm3: float,
    point: OperatingPoint,
    params: DMFCParameters,
    props: EffectiveProperties,
) -> VoltageBreakdown:
    methanol_reference = _positive(params.methanol_reference_concentration_mol_cm3())
    oxygen_bulk = params.oxygen_bulk_concentration_mol_cm3()
    oxygen_reference = _positive(params.oxygen_reference_concentration_mol_cm3())

    anode_exchange_current = props.exchange_current_meoh_a_cm2 * (
        methanol_bulk_concentration_mol_cm3 / methanol_reference
    )
    cathode_exchange_current = props.exchange_current_o2_a_cm2 * (
        oxygen_bulk / oxygen_reference
    )

    anode_activation = (
        params.gas_constant_j_mol_k
        * params.temperature_k
        / (
            params.alpha_anode
            * params.n_electrons_methanol
            * params.faraday_constant_c_mol
        )
    ) * log(_positive(point.current_density_a_cm2 / _positive(anode_exchange_current)))

    anode_mass_transport = (
        params.gas_constant_j_mol_k
        * params.temperature_k
        / (
            params.alpha_anode
            * params.n_electrons_methanol
            * params.faraday_constant_c_mol
        )
    ) * log(
        _positive(
            methanol_bulk_concentration_mol_cm3
            / _positive(point.methanol_concentration_cl_mem_mol_cm3)
        )
    )

    cathode_activation = (
        params.gas_constant_j_mol_k
        * params.temperature_k
        / (
            params.alpha_cathode
            * params.n_electrons_oxygen
            * params.faraday_constant_c_mol
        )
    ) * log(
        _positive(
            point.total_cathode_current_density_a_cm2
            / _positive(cathode_exchange_current)
        )
    )

    cathode_mass_transport = (
        params.gas_constant_j_mol_k
        * params.temperature_k
        / (
            params.alpha_cathode
            * params.n_electrons_oxygen
            * params.faraday_constant_c_mol
        )
    ) * log(
        _positive(oxygen_bulk / _positive(point.oxygen_concentration_cl_mem_mol_cm3))
    )

    ohmic_overpotential = (
        point.current_density_a_cm2
        * params.thickness_membrane_cm
        / params.membrane_conductivity_s_cm
    )

    reversible = reversible_voltage(methanol_bulk_concentration_mol_cm3, params)
    cell_voltage = (
        reversible
        - anode_activation
        - anode_mass_transport
        - cathode_activation
        - cathode_mass_transport
        - ohmic_overpotential
    )

    fuel_utilization = point.current_density_a_cm2 / _positive(
        point.total_cathode_current_density_a_cm2
    )
    efficiency_hhv = cell_voltage / params.voltage_equivalent_hhv() * fuel_utilization
    efficiency_lhv = cell_voltage / params.voltage_equivalent_lhv() * fuel_utilization

    return VoltageBreakdown(
        reversible_voltage_v=reversible,
        anode_activation_overpotential_v=anode_activation,
        anode_mass_transport_overpotential_v=anode_mass_transport,
        cathode_activation_overpotential_v=cathode_activation,
        cathode_mass_transport_overpotential_v=cathode_mass_transport,
        ohmic_overpotential_v=ohmic_overpotential,
        cell_voltage_v=cell_voltage,
        fuel_utilization=fuel_utilization,
        efficiency_hhv=efficiency_hhv,
        efficiency_lhv=efficiency_lhv,
    )


def _is_feasible_current(
    methanol_bulk_concentration_mol_cm3: float,
    current_density_a_cm2: float,
    params: DMFCParameters,
    props: EffectiveProperties,
) -> bool:
    point = operating_point(
        methanol_bulk_concentration_mol_cm3,
        current_density_a_cm2,
        params,
        props,
        include_crossover=True,
    )
    values = (
        point.total_cathode_current_density_a_cm2,
        point.methanol_concentration_gdl_cl_mol_cm3,
        point.methanol_concentration_cl_mem_mol_cm3,
        point.oxygen_concentration_cl_mem_mol_cm3,
    )
    return all(value > EPSILON and isfinite(value) for value in values)


def _maximum_feasible_current_density(
    methanol_bulk_concentration_mol_cm3: float,
    params: DMFCParameters,
    props: EffectiveProperties,
) -> float:
    low = 0.0
    high = 0.1
    while _is_feasible_current(
        methanol_bulk_concentration_mol_cm3, high, params, props
    ) and high < 10.0:
        low = high
        high *= 2.0

    for _ in range(80):
        midpoint = 0.5 * (low + high)
        if _is_feasible_current(
            methanol_bulk_concentration_mol_cm3, midpoint, params, props
        ):
            low = midpoint
        else:
            high = midpoint

    return low * params.safety_margin


def simulate_case(
    methanol_bulk_molarity: float,
    params: DMFCParameters,
    props: EffectiveProperties | None = None,
) -> CaseResult:
    properties = props or compute_effective_properties(params)
    methanol_bulk_concentration = params.methanol_bulk_concentration_mol_cm3(
        methanol_bulk_molarity
    )
    max_current = _maximum_feasible_current_density(
        methanol_bulk_concentration, params, properties
    )
    min_current = max(1.0e-5, max_current * 1.0e-4)
    current_grid = _linear_space(min_current, max_current, params.n_points)

    operating_points: list[OperatingPoint] = []
    anode_activation: list[float] = []
    anode_mass_transport: list[float] = []
    anode_total: list[float] = []
    cathode_activation: list[float] = []
    cathode_mass_transport: list[float] = []
    cathode_total: list[float] = []
    ohmic: list[float] = []
    crossover_loss: list[float] = []
    cell_voltage: list[float] = []
    efficiency_hhv: list[float] = []
    efficiency_lhv: list[float] = []

    peak_power_density = float("-inf")
    peak_power_current = min_current
    reversible = reversible_voltage(methanol_bulk_concentration, params)

    for current_density in current_grid:
        point = operating_point(
            methanol_bulk_concentration,
            current_density,
            params,
            properties,
            include_crossover=True,
        )
        point_no_crossover = operating_point(
            methanol_bulk_concentration,
            current_density,
            params,
            properties,
            include_crossover=False,
        )
        breakdown = evaluate_operating_point(
            methanol_bulk_concentration, point, params, properties
        )
        breakdown_no_crossover = evaluate_operating_point(
            methanol_bulk_concentration, point_no_crossover, params, properties
        )

        operating_points.append(point)
        anode_activation.append(breakdown.anode_activation_overpotential_v)
        anode_mass_transport.append(breakdown.anode_mass_transport_overpotential_v)
        anode_total.append(
            breakdown.anode_activation_overpotential_v
            + breakdown.anode_mass_transport_overpotential_v
        )
        cathode_activation.append(breakdown.cathode_activation_overpotential_v)
        cathode_mass_transport.append(breakdown.cathode_mass_transport_overpotential_v)
        cathode_total.append(
            breakdown.cathode_activation_overpotential_v
            + breakdown.cathode_mass_transport_overpotential_v
        )
        ohmic.append(breakdown.ohmic_overpotential_v)
        crossover_loss.append(
            breakdown_no_crossover.cell_voltage_v - breakdown.cell_voltage_v
        )
        cell_voltage.append(breakdown.cell_voltage_v)
        efficiency_hhv.append(breakdown.efficiency_hhv)
        efficiency_lhv.append(breakdown.efficiency_lhv)

        power_density = current_density * breakdown.cell_voltage_v
        if power_density > peak_power_density:
            peak_power_density = power_density
            peak_power_current = current_density

    return CaseResult(
        methanol_bulk_molarity=methanol_bulk_molarity,
        methanol_bulk_concentration_mol_cm3=methanol_bulk_concentration,
        reversible_voltage_v=reversible,
        max_current_density_a_cm2=max_current,
        peak_power_density_w_cm2=peak_power_density,
        peak_power_current_density_a_cm2=peak_power_current,
        operating_points=tuple(operating_points),
        anode_activation_overpotential_v=tuple(anode_activation),
        anode_mass_transport_overpotential_v=tuple(anode_mass_transport),
        anode_overpotential_v=tuple(anode_total),
        cathode_activation_overpotential_v=tuple(cathode_activation),
        cathode_mass_transport_overpotential_v=tuple(cathode_mass_transport),
        cathode_overpotential_v=tuple(cathode_total),
        ohmic_overpotential_v=tuple(ohmic),
        crossover_loss_v=tuple(crossover_loss),
        cell_voltage_v=tuple(cell_voltage),
        efficiency_hhv=tuple(efficiency_hhv),
        efficiency_lhv=tuple(efficiency_lhv),
    )


def simulate_assignment(
    params: DMFCParameters | None = None,
    props: EffectiveProperties | None = None,
) -> tuple[CaseResult, ...]:
    model_params = params or DMFCParameters()
    properties = props or compute_effective_properties(model_params)
    return tuple(
        simulate_case(molarity, model_params, properties)
        for molarity in model_params.methanol_bulk_molarities
    )


def summarise_results(
    results: tuple[CaseResult, ...],
    params: DMFCParameters,
    props: EffectiveProperties | None = None,
) -> tuple[dict[str, float], ...]:
    properties = props or compute_effective_properties(params)
    rows: list[dict[str, float]] = []
    for result in results:
        open_circuit_point = operating_point(
            result.methanol_bulk_concentration_mol_cm3,
            0.0,
            params,
            properties,
            include_crossover=True,
        )
        peak_hhv = max(result.efficiency_hhv)
        rows.append(
            {
                "methanol_bulk_molarity_M": result.methanol_bulk_molarity,
                "reversible_voltage_V": result.reversible_voltage_v,
                "max_current_density_A_cm2": result.max_current_density_a_cm2,
                "peak_power_density_W_cm2": result.peak_power_density_w_cm2,
                "peak_power_current_density_A_cm2": result.peak_power_current_density_a_cm2,
                "peak_efficiency_HHV": peak_hhv,
                "open_circuit_crossover_current_density_A_cm2": open_circuit_point.methanol_crossover_current_density_a_cm2,
            }
        )
    return tuple(rows)
