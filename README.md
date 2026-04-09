# DMFC Reference Model

This repository turns the original assignment scripts into a cleaner, academic-style Python reference for the 1D DMFC model.

The code keeps the assignment scope intentionally simple:

- steady-state, isothermal, 1D transport
- MEA treated as `GDL / CL / membrane / CL / GDL`
- catalyst layers treated as interfaces rather than spatially resolved domains
- Nernst voltage, activation loss, mass-transport loss, ohmic loss, and methanol crossover
- output curves for `0.5 M`, `1.0 M`, and `3.0 M` methanol feeds

The implementation is dependency-light, so it runs in a plain Python installation without NumPy or Matplotlib. It exports CSV data plus SVG figures.

## What Improved

Compared with the original MATLAB and Python drafts, this version fixes several modelling issues:

- transport fluxes are handled consistently instead of summing layer-by-layer fluxes into an inflated limiting current
- methanol crossover is treated as a parasitic internal current, which then raises cathode demand
- cell efficiency includes a fuel-utilization penalty from crossover
- equations, parameters, outputs, and assumptions are documented explicitly
- the model is packaged, testable, and reproducible

## Run

From the project root:

```powershell
python scripts/run_assignment_reference.py
```

Optional arguments:

```powershell
python scripts/run_assignment_reference.py --points 500 --drag-coefficient 0.2
```

Generated files are written to `outputs/`:

- `outputs/data/*.csv`
- `outputs/figures/*.svg`
- `outputs/summary.csv`

## Project Layout

- `src/dmfc_reference/model.py`: governing equations and simulation workflow
- `src/dmfc_reference/export.py`: CSV and SVG export helpers
- `scripts/run_assignment_reference.py`: command-line entry point
- `docs/model_notes.md`: model assumptions and equations
- `tests/test_model.py`: regression and sanity tests

## Important Note

This is a strong assignment/reference implementation, not a fully validated research-grade DMFC solver. It is appropriate for transparent coursework modelling and for building on later with richer kinetics, water management, two-phase transport, or experimental calibration.
