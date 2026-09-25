"""Render the frozen attempt03 midpoint report without rebuilding CAD."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator

OUTPUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[5]
REPORT_PATH = (
    REPO_ROOT
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    / "current-midpoint-clearance-attempt03/report.json"
)
REPORT_RELATIVE_PATH = str(REPORT_PATH.relative_to(REPO_ROOT))
EXPECTED_REPORT_SHA256 = (
    "a7f7b15200421ad2f6527cf2248f70e7f424164a357a2e69afdf48ad538582e4"
)

GROUP_STYLE = {
    "LED / horizontal": {
        "family": "LED",
        "direction": "horizontal",
        "surface": "main",
        "marker": "o",
    },
    "LED / vertical": {
        "family": "LED",
        "direction": "vertical",
        "surface": "main",
        "marker": "s",
    },
    "T-nut / horizontal": {
        "family": "T-nut",
        "direction": "horizontal",
        "surface": "main",
        "marker": "^",
    },
    "T-nut / vertical": {
        "family": "T-nut",
        "direction": "vertical",
        "surface": "main",
        "marker": "D",
    },
    "kicker T-nut / horizontal": {
        "family": "kicker T-nut",
        "direction": "horizontal",
        "surface": "kicker",
        "marker": "P",
    },
}
STATUS_COLORS = {
    "no screened hit": "#c7d0dc",
    "existing T-nut/LED only": "#2563eb",
    "timber rear-projection-only hit": "#f59e0b",
    "timber flange hit": "#dc2626",
}
EXISTING_OVERLAY_COLOR = "#1d4ed8"


def _status(row: dict[str, Any]) -> str:
    hits = row["hits"]
    if hits["structural_hardware"]:
        raise ValueError(
            "attempt03 has structural-hardware hits; map categories must be revised"
        )
    if any(hit["envelope"] == "flange" for hit in hits["timber"]):
        return "timber flange hit"
    if hits["timber"]:
        return "timber rear-projection-only hit"
    if hits["existing_hold_or_LED"]:
        return "existing T-nut/LED only"
    return "no screened hit"


def _load_report() -> tuple[dict[str, Any], str]:
    report_bytes = REPORT_PATH.read_bytes()
    report_sha256 = hashlib.sha256(report_bytes).hexdigest()
    if report_sha256 != EXPECTED_REPORT_SHA256:
        raise RuntimeError(
            "frozen attempt03 report hash changed; do not map another report silently"
        )
    report = json.loads(report_bytes)
    if report.get("revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("frozen midpoint report is for a different geometry revision")
    if report.get("grid", {}).get("site_count") != 491:
        raise ValueError("frozen midpoint report must contain 491 site centers")
    if report.get("object_inventory", {}).get("tested_obstacle_shapes") != 904:
        raise ValueError("frozen midpoint report must bind the 904-shape obstacle pool")
    return report, report_sha256


def _validate_rows(report: dict[str, Any]) -> tuple[list[dict[str, Any]], Counter[str]]:
    rows = report["sites"]
    if not isinstance(rows, list) or len(rows) != 491:
        raise ValueError("frozen midpoint report site rows are missing or incomplete")
    site_ids = set()
    group_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    for row in rows:
        site_id = row.get("id")
        if not isinstance(site_id, str) or site_id in site_ids:
            raise ValueError("site IDs must be unique strings")
        site_ids.add(site_id)
        x = float(row["x_mm"])
        s = float(row["s_mm"])
        if not math.isfinite(x) or not math.isfinite(s):
            raise ValueError(f"{site_id}: site coordinates must be finite")
        group = f"{row['family']} / {row['direction']}"
        if group not in GROUP_STYLE:
            raise ValueError(f"{site_id}: unexpected site group {group!r}")
        if row["surface"] != GROUP_STYLE[group]["surface"]:
            raise ValueError(f"{site_id}: surface does not match its midpoint family")
        group_counts[group] += 1
        status_counts[_status(row)] += 1

    expected = report["grid"]["counts"]
    if dict(group_counts) != expected:
        raise ValueError(
            "plot group counts do not reconcile with the frozen grid summary"
        )
    if sum(status_counts.values()) != 491:
        raise ValueError("plot status categories do not partition all midpoint sites")
    expected_status_counts = {
        "timber flange hit": 44,
        "timber rear-projection-only hit": 7,
        "existing T-nut/LED only": 220,
        "no screened hit": 220,
    }
    if dict(status_counts) != expected_status_counts:
        raise ValueError("plot color counts differ from the frozen attempt03 site rows")
    return rows, status_counts


def _draw_rows(ax: Any, rows: list[dict[str, Any]], surface: str) -> None:
    visible_rows = [row for row in rows if row["surface"] == surface]
    for style in GROUP_STYLE.values():
        group_rows = [
            row
            for row in visible_rows
            if row["family"] == style["family"]
            and row["direction"] == style["direction"]
        ]
        if not group_rows:
            continue
        edgecolors = []
        linewidths = []
        for row in group_rows:
            hit_count = sum(len(group_hits) for group_hits in row["hits"].values())
            edgecolors.append("#111827" if hit_count > 1 else "#566273")
            linewidths.append(1.1 if hit_count > 1 else 0.55)
        ax.scatter(
            [row["x_mm"] for row in group_rows],
            [row["s_mm"] for row in group_rows],
            marker=style["marker"],
            c=[STATUS_COLORS[_status(row)] for row in group_rows],
            s=43,
            edgecolors=edgecolors,
            linewidths=linewidths,
            alpha=0.95,
            zorder=3,
        )
        overlap_rows = [
            row
            for row in group_rows
            if row["hits"]["timber"] and row["hits"]["existing_hold_or_LED"]
        ]
        if overlap_rows:
            ax.scatter(
                [row["x_mm"] for row in overlap_rows],
                [row["s_mm"] for row in overlap_rows],
                marker="o",
                s=100,
                facecolors="none",
                edgecolors=EXISTING_OVERLAY_COLOR,
                linewidths=1.2,
                zorder=4,
            )


def _legend_handles(
    report: dict[str, Any],
) -> tuple[list[Line2D], list[Line2D], list[Line2D]]:
    colors = [
        Line2D(
            [],
            [],
            marker="o",
            linestyle="none",
            markersize=8,
            markerfacecolor=color,
            markeredgecolor="#566273",
            label=label,
        )
        for label, color in STATUS_COLORS.items()
    ]
    group_counts = report["grid"]["counts"]
    groups = [
        Line2D(
            [],
            [],
            marker=style["marker"],
            linestyle="none",
            markersize=8,
            markerfacecolor="#e5e7eb",
            markeredgecolor="#566273",
            label=f"{label} ({group_counts[label]})",
        )
        for label, style in GROUP_STYLE.items()
    ]
    overlays = [
        Line2D(
            [],
            [],
            marker="o",
            linestyle="none",
            markersize=10,
            markerfacecolor="none",
            markeredgecolor=EXISTING_OVERLAY_COLOR,
            markeredgewidth=1.2,
            label="Blue ring: timber hit plus existing T-nut/LED hit",
        ),
        Line2D(
            [],
            [],
            marker="o",
            linestyle="none",
            markersize=8,
            markerfacecolor="#c7d0dc",
            markeredgecolor="#111827",
            markeredgewidth=1.1,
            label="Black edge: multiple BRep hit records at this site",
        ),
    ]
    return colors, groups, overlays


def render_map(report: dict[str, Any], status_counts: Counter[str]) -> None:
    rows = report["sites"]
    main_rows = [row for row in rows if row["surface"] == "main"]
    kicker_rows = [row for row in rows if row["surface"] == "kicker"]
    if (len(main_rows), len(kicker_rows)) != (482, 9):
        raise ValueError("plot requires 482 main-panel and 9 kicker site centers")

    fig = plt.figure(figsize=(15, 10))
    layout = fig.add_gridspec(
        2,
        2,
        left=0.07,
        right=0.97,
        top=0.91,
        bottom=0.14,
        wspace=0.22,
        hspace=0.30,
        width_ratios=(3.8, 1.55),
        height_ratios=(8, 1.3),
    )
    main_ax = fig.add_subplot(layout[0, 0])
    kicker_ax = fig.add_subplot(layout[1, 0])
    legend_ax = fig.add_subplot(layout[:, 1])
    legend_ax.axis("off")

    _draw_rows(main_ax, rows, "main")
    main_ax.set_title("Main panel site centers", loc="left", fontsize=12, pad=10)
    main_ax.set_xlabel("Panel-local X (mm)")
    main_ax.set_ylabel("Panel-local S (mm)")
    main_ax.set_xlim(100.0, 2300.0)
    main_ax.set_ylim(-80.0, 2420.0)
    main_ax.set_aspect("equal", adjustable="box")
    main_ax.xaxis.set_major_locator(MultipleLocator(500))
    main_ax.yaxis.set_major_locator(MultipleLocator(500))
    main_ax.grid(color="#dce3ea", linewidth=0.65, zorder=0)
    main_ax.set_axisbelow(True)

    _draw_rows(kicker_ax, rows, "kicker")
    kicker_ax.set_title("Kicker-local site centers", loc="left", fontsize=10, pad=5)
    kicker_ax.set_xlabel("Kicker-local X (mm)")
    kicker_ax.set_ylabel("Kicker-local S (mm)")
    kicker_ax.set_xlim(100.0, 2300.0)
    kicker_ax.set_ylim(-90.0, -60.0)
    kicker_ax.set_yticks([-75.0])
    kicker_ax.xaxis.set_major_locator(MultipleLocator(500))
    kicker_ax.grid(axis="x", color="#dce3ea", linewidth=0.65, zorder=0)
    kicker_ax.axhline(-75.0, color="#aab5c1", linewidth=0.75, zorder=1)
    kicker_ax.set_axisbelow(True)

    colors, groups, overlays = _legend_handles(report)
    legend_ax.text(
        0.0,
        1.0,
        "Color = reported screen result\nMarker = site family and direction",
        ha="left",
        va="top",
        fontsize=11,
        weight="bold",
        transform=legend_ax.transAxes,
    )
    color_legend = legend_ax.legend(
        handles=colors,
        title="Primary site category",
        loc="upper left",
        bbox_to_anchor=(0.0, 0.90),
        frameon=False,
        fontsize=9,
        title_fontsize=10,
    )
    legend_ax.add_artist(color_legend)
    group_legend = legend_ax.legend(
        handles=groups,
        title="Site groups (counts)",
        loc="upper left",
        bbox_to_anchor=(0.0, 0.58),
        frameon=False,
        fontsize=9,
        title_fontsize=10,
    )
    legend_ax.add_artist(group_legend)
    overlay_legend = legend_ax.legend(
        handles=overlays,
        title="Overlap outlines",
        loc="upper left",
        bbox_to_anchor=(0.0, 0.29),
        frameon=False,
        fontsize=9,
        title_fontsize=10,
    )
    legend_ax.add_artist(overlay_legend)
    legend_ax.text(
        0.0,
        0.10,
        "491 sites · 904 obstacle solids\n"
        f"{status_counts['timber flange hit']} flange-site hits · "
        f"{status_counts['timber rear-projection-only hit']} projection-only hits\n"
        f"{status_counts['existing T-nut/LED only']} existing-body-only hits · "
        f"{status_counts['no screened hit']} no-hit sites",
        ha="left",
        va="top",
        fontsize=9,
        transform=legend_ax.transAxes,
    )

    fig.suptitle(
        "Hypothetical nearest-neighbor midpoint screen — current WJ24",
        fontsize=16,
        weight="bold",
    )
    fig.text(
        0.5,
        0.035,
        "Provisional probes; wires, panels and service access excluded. No future-layout approval.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#344054",
    )
    fig.savefig(
        OUTPUT_DIR / "current-midpoint-clearance-map.png",
        dpi=220,
        facecolor="white",
        metadata={
            "Title": "Current WJ24 hypothetical midpoint clearance map",
            "Description": "Static visualization of frozen attempt03 report rows; no CAD is rebuilt.",
        },
    )
    fig.savefig(
        OUTPUT_DIR / "current-midpoint-clearance-map.svg",
        facecolor="white",
        metadata={
            "Title": "Current WJ24 hypothetical midpoint clearance map",
            "Description": "Static visualization of frozen attempt03 report rows; no CAD is rebuilt.",
        },
    )
    plt.close(fig)


def main() -> None:
    report, report_sha256 = _load_report()
    rows, status_counts = _validate_rows(report)
    render_map(report, status_counts)

    report_groups = report["groups"]
    manifest = {
        "schema": "wood_joint_current_midpoint_clearance_map_manifest/v1",
        "revision_id": report["revision_id"],
        "input_report": {
            "path": REPORT_RELATIVE_PATH,
            "sha256": report_sha256,
            "geometry_snapshot_sha256_canonical": report[
                "geometry_snapshot_sha256_canonical"
            ],
            "current_revision_report_sha256": report["current_revision_report_sha256"],
        },
        "producer": {
            "path": str(Path(__file__).relative_to(REPO_ROOT)),
            "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "outputs": {
            name: hashlib.sha256((OUTPUT_DIR / name).read_bytes()).hexdigest()
            for name in (
                "current-midpoint-clearance-map.png",
                "current-midpoint-clearance-map.svg",
                "README.md",
            )
        },
        "site_count": len(rows),
        "tested_obstacle_shapes": report["object_inventory"]["tested_obstacle_shapes"],
        "group_counts": report["grid"]["counts"],
        "timber_blocked_site_counts": {
            group: values["timber_blocked"] for group, values in report_groups.items()
        },
        "display_category_counts": dict(status_counts),
        "overlay_counts": {
            "existing_tnut_or_led_and_timber": sum(
                bool(row["hits"]["existing_hold_or_LED"] and row["hits"]["timber"])
                for row in rows
            ),
            "multiple_brep_hit_records": sum(
                sum(len(group_hits) for group_hits in row["hits"].values()) > 1
                for row in rows
            ),
        },
        "limits": [
            "Colors classify the provisional probe envelopes against only the obstacles present in the frozen report.",
            "Blue rings show existing T-nut/LED hits overlaid on timber-hit sites; black edges show multiple hit records.",
            "Wires, plywood-panel bodies, and service operations are outside this screen.",
            "This map does not establish actual product compatibility, physical blockage, or an approved future layout.",
        ],
    }
    (OUTPUT_DIR / "source-hashes.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
