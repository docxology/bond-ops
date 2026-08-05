"""Deterministic fleet-operations visualizations (headless Agg PNG).

The QUARTERMASTER renders four canonical figures:

- ``roster_composition`` — infrastructure vs film packages, from the frozen
  roster constants (no subprocess);
- ``fleet_health`` — the real per-package health sweep over every roster
  package (git + files + lineage + layout probes);
- ``gate_coverage`` / ``gate_verdicts`` — a real gate report's measured
  coverage bars and per-check verdict heatmap.

Every figure is byte-deterministic for the same inputs (fixed sizes, dpi,
Agg backend, colourblind-safe palette). Figures are rendered from canonical
data and real reports — never from fabricated values.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from .gates import COVERAGE_FLOOR, AggregateGateReport
from .health import HealthReport
from .inventory import FILM_COUNT, INFRA_COUNT, SUITE_NAME, SUITE_SIZE

#: Colourblind-safe palette (Wong 2011).
BLUE = "#0072B2"
ORANGE = "#E69F00"
GREEN = "#009E73"
RED = "#D55E00"
GREY = "#999999"

#: Default figure output directory, relative to the working directory.
DEFAULT_FIGURE_DIR = Path("output") / "figures"

#: Figure filenames (manuscript references these under ``../output/figures/``).
ROSTER_COMPOSITION = "roster_composition.png"
FLEET_HEALTH = "fleet_health.png"
GATE_COVERAGE = "gate_coverage.png"
GATE_VERDICTS = "gate_verdicts.png"


def _prepare(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _text_only(target: Path, message: str) -> Path:
    """Render a deterministic placeholder figure (no data to plot)."""
    figure, axis = plt.subplots(figsize=(6.0, 2.0))
    axis.text(0.5, 0.5, message, ha="center", va="center", fontsize=12, color=GREY)
    axis.axis("off")
    figure.savefig(target, dpi=200, bbox_inches="tight")
    plt.close(figure)
    return target.resolve()


def plot_roster_composition(path: str | Path | None = None) -> Path:
    """Render the infrastructure-vs-films roster composition bar chart.

    Data comes from the frozen ``inventory`` constants
    (``INFRA_COUNT + FILM_COUNT == SUITE_SIZE``); fully deterministic.
    """
    target = _prepare(path or (DEFAULT_FIGURE_DIR / ROSTER_COMPOSITION))
    figure, axis = plt.subplots(figsize=(5.6, 3.0))
    counts = [INFRA_COUNT, FILM_COUNT]
    labels = [f"infrastructure ({INFRA_COUNT})", f"film packages ({FILM_COUNT})"]
    bars = axis.bar(labels, counts, color=[BLUE, ORANGE], width=0.5)
    axis.set_ylim(0, SUITE_SIZE + 2)
    axis.set_ylabel("packages")
    axis.set_title(f"{SUITE_NAME} roster composition — {SUITE_SIZE} packages")
    for bar, count in zip(bars, counts, strict=True):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            count + 0.6,
            str(count),
            ha="center",
            fontweight="bold",
        )
    figure.savefig(target, dpi=200, bbox_inches="tight")
    plt.close(figure)
    return target.resolve()


def plot_fleet_health(
    reports: list[HealthReport] | tuple[HealthReport, ...], path: str | Path | None = None
) -> Path:
    """Render per-package fleet health as a coloured status bar.

    One row per report: green = healthy, red = present but unhealthy, grey =
    absent. Rows follow the canonical roster order, so the chart is
    deterministic for a given fleet state.
    """
    target = _prepare(path or (DEFAULT_FIGURE_DIR / FLEET_HEALTH))
    if not reports:
        return _text_only(target, "no health reports to plot")
    rows = [r.slug for r in reports]
    colors: list[str] = []
    for r in reports:
        if not r.present:
            colors.append(GREY)
        elif r.healthy:
            colors.append(GREEN)
        else:
            colors.append(RED)
    figure, axis = plt.subplots(figsize=(7.0, max(3.0, 0.32 * len(rows))))
    axis.barh(rows, [1] * len(rows), color=colors, height=0.7)
    axis.set_xlim(0, 1)
    axis.set_xticks([])
    axis.set_title(f"{SUITE_NAME} fleet health ({len(rows)} packages)")
    axis.set_xlabel("green = healthy · red = unhealthy · grey = missing")
    figure.savefig(target, dpi=200, bbox_inches="tight")
    plt.close(figure)
    return target.resolve()


def plot_gate_coverage(report: AggregateGateReport, path: str | Path | None = None) -> Path:
    """Render measured coverage bars for the gated packages.

    Bars are green when they meet the ``COVERAGE_FLOOR`` floor and red
    otherwise; a vertical reference line marks the floor. Deterministic for a
    given report.
    """
    target = _prepare(path or (DEFAULT_FIGURE_DIR / GATE_COVERAGE))
    measured = [(r.slug, r.coverage) for r in report.results if r.coverage is not None]
    if not measured:
        return _text_only(target, "no coverage measured in this gate report")
    slugs = [slug for slug, _ in measured]
    values = [cov for _, cov in measured]
    colors = [GREEN if cov >= COVERAGE_FLOOR else RED for cov in values]
    figure, axis = plt.subplots(figsize=(max(4.5, 0.9 * len(slugs)), 3.0))
    axis.bar(slugs, values, color=colors, width=0.5)
    axis.axhline(COVERAGE_FLOOR, color=GREY, linestyle="--", linewidth=1.2)
    axis.text(
        len(slugs) - 0.45,
        COVERAGE_FLOOR + 1.0,
        f"floor {COVERAGE_FLOOR}%",
        ha="right",
        fontsize=8,
        color=GREY,
    )
    axis.set_ylim(0, 100)
    axis.set_ylabel("coverage (%)")
    axis.set_title("Aggregate gate — measured coverage")
    figure.savefig(target, dpi=200, bbox_inches="tight")
    plt.close(figure)
    return target.resolve()


def plot_gate_verdicts(report: AggregateGateReport, path: str | Path | None = None) -> Path:
    """Render the per-package gate verdict heatmap (pytest / ruff / mypy /
    passed). Green = pass, red = fail. Deterministic for a given report."""
    target = _prepare(path or (DEFAULT_FIGURE_DIR / GATE_VERDICTS))
    rows = [r.slug for r in report.results if r.present]
    if not rows:
        return _text_only(target, "no present packages in this gate report")
    checks = ["pytest", "ruff", "mypy", "passed"]
    matrix: list[list[int]] = []
    for r in report.results:
        if r.slug not in rows:
            continue
        matrix.append(
            [
                1 if r.pytest_passed else 0,
                1 if r.ruff_passed else 0,
                1 if r.mypy_passed else 0,
                1 if r.passed else 0,
            ]
        )
    figure, axis = plt.subplots(figsize=(max(3.6, 1.1 * len(checks)), max(2.0, 0.5 * len(rows))))
    axis.imshow(matrix, cmap=plt.get_cmap("RdYlGn"), vmin=0, vmax=1, aspect="auto")
    axis.set_xticks(range(len(checks)), checks)
    axis.set_yticks(range(len(rows)), rows)
    axis.set_title("Aggregate gate verdicts (green = pass)")
    figure.savefig(target, dpi=200, bbox_inches="tight")
    plt.close(figure)
    return target.resolve()


__all__ = [
    "BLUE",
    "ORANGE",
    "GREEN",
    "RED",
    "GREY",
    "DEFAULT_FIGURE_DIR",
    "ROSTER_COMPOSITION",
    "FLEET_HEALTH",
    "GATE_COVERAGE",
    "GATE_VERDICTS",
    "plot_roster_composition",
    "plot_fleet_health",
    "plot_gate_coverage",
    "plot_gate_verdicts",
]
