from __future__ import annotations

import csv
from dataclasses import dataclass
from html import escape
from pathlib import Path

from .model import CaseResult, DMFCParameters, EffectiveProperties, summarise_results


@dataclass(frozen=True)
class SvgSeries:
    label: str
    x_values: tuple[float, ...]
    y_values: tuple[float, ...]
    color: str
    dashed: bool = False


def _slug_for_molarity(molarity: float) -> str:
    return f"{molarity:.1f}".replace(".", "p")


def _write_csv(path: Path, rows: tuple[dict[str, float], ...]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_case_csv(case_result: CaseResult, output_dir: Path) -> Path:
    file_name = f"dmfc_{_slug_for_molarity(case_result.methanol_bulk_molarity)}M.csv"
    path = output_dir / file_name
    _write_csv(path, case_result.rows())
    return path


def write_summary_csv(
    results: tuple[CaseResult, ...],
    output_dir: Path,
    params: DMFCParameters,
    props: EffectiveProperties,
) -> Path:
    path = output_dir / "summary.csv"
    _write_csv(path, summarise_results(results, params, props))
    return path


def _nice_bounds(series: tuple[SvgSeries, ...]) -> tuple[float, float, float, float]:
    x_values = [value for item in series for value in item.x_values]
    y_values = [value for item in series for value in item.y_values]
    x_min = min(x_values)
    x_max = max(x_values)
    y_min = min(y_values)
    y_max = max(y_values)

    if abs(x_max - x_min) < 1.0e-12:
        x_max = x_min + 1.0
    if abs(y_max - y_min) < 1.0e-12:
        y_max = y_min + 1.0

    y_padding = 0.05 * (y_max - y_min)
    return x_min, x_max, y_min - y_padding, y_max + y_padding


def write_svg_chart(
    path: Path,
    title: str,
    x_label: str,
    y_label: str,
    series: tuple[SvgSeries, ...],
) -> Path:
    width = 1040
    height = 680
    left = 110
    right = 40
    top = 70
    bottom = 90

    x_min, x_max, y_min, y_max = _nice_bounds(series)
    plot_width = width - left - right
    plot_height = height - top - bottom

    def map_x(value: float) -> float:
        return left + ((value - x_min) / (x_max - x_min)) * plot_width

    def map_y(value: float) -> float:
        return height - bottom - ((value - y_min) / (y_max - y_min)) * plot_height

    x_ticks = tuple(x_min + index * (x_max - x_min) / 5.0 for index in range(6))
    y_ticks = tuple(y_min + index * (y_max - y_min) / 5.0 for index in range(6))

    elements: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff" />',
        f'<text x="{width / 2:.1f}" y="38" text-anchor="middle" font-size="26" font-family="Georgia, serif" fill="#1f1f1f">{escape(title)}</text>',
    ]

    for tick in x_ticks:
        x_pos = map_x(tick)
        elements.append(
            f'<line x1="{x_pos:.2f}" y1="{top}" x2="{x_pos:.2f}" y2="{height - bottom}" stroke="#e3e3e3" stroke-width="1" />'
        )
        elements.append(
            f'<text x="{x_pos:.2f}" y="{height - bottom + 26}" text-anchor="middle" font-size="15" font-family="Arial, sans-serif" fill="#4b4b4b">{tick:.3f}</text>'
        )

    for tick in y_ticks:
        y_pos = map_y(tick)
        elements.append(
            f'<line x1="{left}" y1="{y_pos:.2f}" x2="{width - right}" y2="{y_pos:.2f}" stroke="#e3e3e3" stroke-width="1" />'
        )
        elements.append(
            f'<text x="{left - 16}" y="{y_pos + 5:.2f}" text-anchor="end" font-size="15" font-family="Arial, sans-serif" fill="#4b4b4b">{tick:.3f}</text>'
        )

    elements.append(
        f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#1f1f1f" stroke-width="2" />'
    )
    elements.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#1f1f1f" stroke-width="2" />'
    )

    for item in series:
        points = " ".join(
            f"{map_x(x_value):.2f},{map_y(y_value):.2f}"
            for x_value, y_value in zip(item.x_values, item.y_values)
        )
        dash = ' stroke-dasharray="10 7"' if item.dashed else ""
        elements.append(
            f'<polyline fill="none" stroke="{item.color}" stroke-width="3"{dash} stroke-linejoin="round" stroke-linecap="round" points="{points}" />'
        )

    legend_width = 250
    legend_height = 28 * len(series) + 22
    legend_x = width - right - legend_width
    legend_y = top + 10
    elements.append(
        f'<rect x="{legend_x}" y="{legend_y}" width="{legend_width}" height="{legend_height}" rx="8" fill="#ffffff" fill-opacity="0.92" stroke="#cccccc" />'
    )
    for index, item in enumerate(series):
        y_row = legend_y + 22 + index * 28
        dash = ' stroke-dasharray="10 7"' if item.dashed else ""
        elements.append(
            f'<line x1="{legend_x + 14}" y1="{y_row}" x2="{legend_x + 54}" y2="{y_row}" stroke="{item.color}" stroke-width="3"{dash} />'
        )
        elements.append(
            f'<text x="{legend_x + 64}" y="{y_row + 5}" font-size="15" font-family="Arial, sans-serif" fill="#303030">{escape(item.label)}</text>'
        )

    elements.append(
        f'<text x="{width / 2:.1f}" y="{height - 24}" text-anchor="middle" font-size="18" font-family="Arial, sans-serif" fill="#1f1f1f">{escape(x_label)}</text>'
    )
    elements.append(
        f'<text x="28" y="{height / 2:.1f}" text-anchor="middle" font-size="18" font-family="Arial, sans-serif" fill="#1f1f1f" transform="rotate(-90 28 {height / 2:.1f})">{escape(y_label)}</text>'
    )
    elements.append("</svg>")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements), encoding="utf-8")
    return path


def export_assignment_outputs(
    results: tuple[CaseResult, ...],
    output_dir: Path,
    params: DMFCParameters,
    props: EffectiveProperties,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir = output_dir / "data"
    figure_dir = output_dir / "figures"

    case_files = tuple(write_case_csv(result, data_dir) for result in results)
    summary_file = write_summary_csv(results, output_dir, params, props)

    colors = ("#1f4e79", "#b5514a", "#4f7c43")

    anode_series = tuple(
        SvgSeries(
            label=f"{result.methanol_bulk_molarity:.1f} M",
            x_values=result.current_density_a_cm2,
            y_values=result.anode_overpotential_v,
            color=colors[index],
        )
        for index, result in enumerate(results)
    )
    cathode_series = tuple(
        SvgSeries(
            label=f"{result.methanol_bulk_molarity:.1f} M",
            x_values=result.current_density_a_cm2,
            y_values=result.cathode_overpotential_v,
            color=colors[index],
        )
        for index, result in enumerate(results)
    )
    polarization_series = tuple(
        SvgSeries(
            label=f"{result.methanol_bulk_molarity:.1f} M",
            x_values=result.current_density_a_cm2,
            y_values=result.cell_voltage_v,
            color=colors[index],
        )
        for index, result in enumerate(results)
    )

    efficiency_series: list[SvgSeries] = []
    for index, result in enumerate(results):
        efficiency_series.append(
            SvgSeries(
                label=f"HHV {result.methanol_bulk_molarity:.1f} M",
                x_values=result.current_density_a_cm2,
                y_values=result.efficiency_hhv,
                color=colors[index],
            )
        )
        efficiency_series.append(
            SvgSeries(
                label=f"LHV {result.methanol_bulk_molarity:.1f} M",
                x_values=result.current_density_a_cm2,
                y_values=result.efficiency_lhv,
                color=colors[index],
                dashed=True,
            )
        )

    figure_files = (
        write_svg_chart(
            figure_dir / "anode_overpotential.svg",
            "Anode Overpotential vs Current Density",
            "Current density (A cm^-2)",
            "Anode overpotential (V)",
            anode_series,
        ),
        write_svg_chart(
            figure_dir / "cathode_overpotential.svg",
            "Cathode Overpotential vs Current Density",
            "Current density (A cm^-2)",
            "Cathode overpotential (V)",
            cathode_series,
        ),
        write_svg_chart(
            figure_dir / "polarization_curve.svg",
            "DMFC Polarization Curve",
            "Current density (A cm^-2)",
            "Cell voltage (V)",
            polarization_series,
        ),
        write_svg_chart(
            figure_dir / "efficiency_curve.svg",
            "DMFC Efficiency vs Current Density",
            "Current density (A cm^-2)",
            "Efficiency",
            tuple(efficiency_series),
        ),
    )

    return {
        "output_dir": output_dir,
        "data_dir": data_dir,
        "figures_dir": figure_dir,
        "case_files": case_files,
        "summary_file": summary_file,
        "figure_files": figure_files,
    }
