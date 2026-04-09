# Model Notes

## Scope

The code implements the simplified part C model from the assignment:

- predict anode overpotential versus current density
- predict cathode overpotential versus current density
- predict cell voltage versus current density
- predict HHV and LHV efficiency versus current density

All results are generated for methanol feeds of `0.5 M`, `1.0 M`, and `3.0 M` at `70 C`, with air at `1 atm` on the cathode side.

## Main Assumptions

1. The model is steady-state, isothermal, and one-dimensional.
2. Flow-channel losses are neglected, matching the assignment brief.
3. Each catalyst layer is treated as an interface, not as a distributed reaction zone.
4. Diffusion is represented by Fickian layer resistances.
5. Methanol crossover is represented as a parasitic flux through the membrane.
6. Electro-osmotic drag is optional and defaults to zero.
7. Kinetics are written in Tafel form with first-order dependence on the local reactant concentration.

## Governing Equations

### 1. Effective transport and kinetic parameters

The temperature-dependent properties are evaluated with the same Arrhenius-style relationships used in the assignment data:

- `D(T) = D_ref * exp[(E_D / R) * (1 / T_ref - 1 / T)]`
- `j0(T) = j0_ref * exp[(E_a / R) * (1 / T_ref - 1 / T)]`

### 2. Methanol transport on the anode side

Define the total anode methanol transport resistance:

- `R_a = delta_GDL / D_MeOH,GDL + delta_CL / D_MeOH,CL`

and the membrane diffusion resistance:

- `R_M = delta_M / D_MeOH,M`

For an external current density `j`, the electrochemical methanol consumption is:

- `N_rxn = j / (6 F)`

If electro-osmotic drag is included:

- `N_drag = xi_drag * j / F`

The total methanol flux from the anode bulk to the reaction interface is then:

- `N_a = (N_rxn + N_drag + c_B / R_M) / (1 + R_a / R_M)`

The interface concentrations become:

- `c_1 = c_B - N_a * delta_GDL / D_MeOH,GDL`
- `c_2 = c_1 - N_a * delta_CL / D_MeOH,CL`

The crossover flux is:

- `N_cross = N_a - N_rxn`

and the corresponding parasitic current density is:

- `j_cross = 6 F N_cross`

### 3. Oxygen transport on the cathode side

The cathode resistance is:

- `R_c = delta_GDL / D_O2,GDL + delta_CL / D_O2,CL`

The cathode must sustain both the useful current and the parasitic mixed current:

- `j_c,tot = j + j_cross`

The oxygen concentration at the cathode reaction interface is:

- `c_4 = c_O2,bulk - R_c * j_c,tot / (4 F)`

### 4. Reversible voltage

The reversible voltage is evaluated from the operating bulk conditions:

- `E_rev = E0 + (R T / 6 F) * ln[(c_B / c_ref,MeOH) * (c_O2,bulk / c_ref,O2)^(3/2)]`

This keeps the reversible term separate from the explicit mass-transport losses.

### 5. Overpotentials

Anode activation:

- `eta_a,act = (R T / alpha_a 6 F) * ln[j / (j0,a * c_B / c_ref,MeOH)]`

Anode mass transport:

- `eta_a,mt = (R T / alpha_a 6 F) * ln(c_B / c_2)`

Cathode activation:

- `eta_c,act = (R T / alpha_c 4 F) * ln[j_c,tot / (j0,c * c_O2,bulk / c_ref,O2)]`

Cathode mass transport:

- `eta_c,mt = (R T / alpha_c 4 F) * ln(c_O2,bulk / c_4)`

Ohmic loss:

- `eta_ohm = j * delta_M / kappa`

Cell voltage:

- `V_cell = E_rev - eta_a,act - eta_a,mt - eta_c,act - eta_c,mt - eta_ohm`

## Crossover Loss as a Diagnostic

The code also reports a crossover-loss diagnostic:

- `eta_cross = V_no_cross - V_with_cross`

where `V_no_cross` is computed for the same external current but with membrane crossover disabled. This is not double-counted in the cell voltage; it is only a diagnostic quantity.

## Efficiency

The thermodynamic voltage equivalents are:

- `V_HHV = DeltaH_HHV / (6 F)`
- `V_LHV = DeltaH_LHV / (6 F)`

Fuel utilization is reduced by crossover:

- `eta_fuel = j / (j + j_cross)`

Electrical efficiencies are then:

- `eta_HHV = (V_cell / V_HHV) * eta_fuel`
- `eta_LHV = (V_cell / V_LHV) * eta_fuel`

## Why This Is Better Than the Original Draft

The original scripts were useful first attempts, but they mixed several ideas together:

- they summed equal steady-state diffusion fluxes across multiple layers, which overestimates limiting current
- the reversible-voltage expression was inconsistent with the DMFC stoichiometry
- crossover was partly treated as a separate voltage penalty and partly inside the cathode expression
- efficiency ignored the fuel penalty from methanol crossover

This reference version resolves those inconsistencies while keeping the model within the assignment's simplified 1D framework.
