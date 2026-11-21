"""Peak vs low electricity demand by Tokyo temperature band, plus the before/after quality report.

Run from the project root:
    python src/analysis.py        # runs the cleaning pipeline first
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clean_prepare as cp  # noqa: E402

FIG_DIR = cp.REPORT_DIR / "figures"
MIN_HOURS = 30  # bands with fewer hours are reported but marked as thin

# Validated palette (light surface). Aqua is below 3:1 contrast, so every line is direct-labelled
# and the numbers are also given as a table in the report.
PEAK, AVG, LOW = "#eb6834", "#2a78d6", "#1baf7a"
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"


def band_summary(df: pd.DataFrame, workdays_only: bool = False) -> pd.DataFrame:
    d = df[df["is_workday"]] if workdays_only else df
    g = d.groupby("temp_band", observed=True)["demand_gw"]
    out = pd.DataFrame({
        "hours": g.size(),
        "low_gw": g.min(),
        "p5_gw": g.quantile(0.05),
        "mean_gw": g.mean(),
        "p95_gw": g.quantile(0.95),
        "peak_gw": g.max(),
    }).round(2)
    out["thin_sample"] = out["hours"] < MIN_HOURS
    out.index = out.index.astype(str)
    return out


def daily_band_summary(daily: pd.DataFrame) -> pd.DataFrame:
    bands = pd.cut(daily["mean_temp_c"], bins=cp.TEMP_BAND_EDGES, right=False,
                   labels=[f"{a} to {a + 2}" for a in cp.TEMP_BAND_EDGES[:-1]])
    g = daily.groupby(bands, observed=True)
    out = pd.DataFrame({
        "days": g.size(),
        "avg_daily_peak_gw": g["peak_demand_gw"].mean(),
        "highest_daily_peak_gw": g["peak_demand_gw"].max(),
        "avg_daily_low_gw": g["low_demand_gw"].mean(),
        "lowest_daily_low_gw": g["low_demand_gw"].min(),
    }).round(2)
    out.index = out.index.astype(str).rename("daily_mean_temp_band")
    return out


def findings(df: pd.DataFrame, hourly: pd.DataFrame, daily: pd.DataFrame, daily_bands: pd.DataFrame) -> dict:
    solid = hourly[~hourly["thin_sample"]]
    top = df.loc[df["demand_gw"].idxmax()]
    bottom = df.loc[df["demand_gw"].idxmin()]
    keys = {
        "lowest_mean_demand_band": solid["mean_gw"].idxmin(),
        "lowest_mean_demand_gw": float(solid["mean_gw"].min()),
        "highest_mean_demand_band": solid["mean_gw"].idxmax(),
        "highest_mean_demand_gw": float(solid["mean_gw"].max()),
        "highest_peak_band": solid["peak_gw"].idxmax(),
        "highest_peak_gw": float(solid["peak_gw"].max()),
        "coldest_band_mean_gw": float(solid["mean_gw"].iloc[0]),
        "coldest_band": solid.index[0],
        "winter_peak_band": solid.loc[solid.index[:8], "peak_gw"].idxmax(),
        "winter_peak_gw": float(solid.loc[solid.index[:8], "peak_gw"].max()),
        "record_hour": str(df["demand_gw"].idxmax()),
        "record_gw": float(top["demand_gw"]),
        "record_temp_c": float(top["temp_tokyo_c"]),
        "lowest_hour": str(df["demand_gw"].idxmin()),
        "lowest_gw": float(bottom["demand_gw"]),
        "lowest_temp_c": float(bottom["temp_tokyo_c"]),
        "daily_lowest_band": daily_bands["avg_daily_peak_gw"].idxmin(),
        "summer_vs_mild_peak_ratio": round(float(solid["mean_gw"].max() / solid["mean_gw"].min()), 2),
    }
    return {k: round(v, 2) if isinstance(v, float) else v for k, v in keys.items()}


# --------------------------------------------------------------------------------------
def _style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_2, length=0, labelsize=8.5)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot_bands(hourly: pd.DataFrame, path: Path):
    h = hourly[~hourly["thin_sample"]]
    x = range(len(h))
    fig, ax = plt.subplots(figsize=(10, 5.4), facecolor=SURFACE)
    _style(ax)
    ax.fill_between(x, h["p5_gw"], h["p95_gw"], color=AVG, alpha=0.10, linewidth=0)
    for col, color, name in [("peak_gw", PEAK, "Peak (highest hour)"), ("mean_gw", AVG, "Average"),
                             ("low_gw", LOW, "Low (lowest hour)")]:
        ax.plot(x, h[col], color=color, linewidth=2, marker="o", markersize=4.5,
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=name)
        ax.text(len(h) - 0.6, h[col].iloc[-1], name.split(" (")[0], color=INK, fontsize=9, va="center")
    imin = int(h["mean_gw"].values.argmin())
    ax.annotate(f"Lowest average\n{h['mean_gw'].iloc[imin]:.1f} GW at {h.index[imin]} °C",
                xy=(imin, h["mean_gw"].iloc[imin]), xytext=(imin - 2.5, 16.3), fontsize=8.5, color=INK_2,
                ha="center", va="top", arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.8))
    ipk = int(h["peak_gw"].values.argmax())
    ax.annotate(f"Highest peak {h['peak_gw'].iloc[ipk]:.1f} GW\nat {h.index[ipk]} °C",
                xy=(ipk, h["peak_gw"].iloc[ipk]), xytext=(ipk - 4, 62.5), fontsize=8.5, color=INK_2,
                ha="center", arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.8))
    ax.set_xticks(list(x), [s.replace(" to ", "–") for s in h.index], rotation=45, ha="right")
    ax.set_xlim(-0.5, len(h) + 0.6)
    ax.set_ylim(10, 66)
    ax.set_xlabel("Tokyo air temperature in that hour (°C, JMA Tokyo station)", color=INK_2, fontsize=9)
    ax.set_ylabel("TEPCO area demand (GW)", color=INK_2, fontsize=9)
    ax.set_title("Electricity demand by temperature band: lowest at 16–20 °C, highest in the 30s",
                 loc="left", color=INK, fontsize=12, fontweight="bold", pad=26)
    ax.text(0, 1.015, f"Hourly data, Apr 2022 – Oct 2026 (n = {int(h['hours'].sum()):,} h). Shaded: middle 90 % of "
            f"hours. Bands with < {MIN_HOURS} h omitted.", transform=ax.transAxes, fontsize=8.5,
            color=INK_2, va="bottom")
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)


def plot_daily(daily: pd.DataFrame, path: Path):
    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=SURFACE)
    _style(ax)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    for mask, color, name in [(daily["is_workday"], AVG, "Workdays"),
                              (~daily["is_workday"], PEAK, "Weekends & holidays")]:
        d = daily[mask]
        ax.scatter(d["mean_temp_c"], d["peak_demand_gw"], s=16, color=color, alpha=0.75,
                   edgecolors=SURFACE, linewidths=0.6, label=f"{name} (n = {len(d):,})")
    ax.set_xlabel("Daily mean temperature in Tokyo (°C)", color=INK_2, fontsize=9)
    ax.set_ylabel("Daily peak demand (GW)", color=INK_2, fontsize=9)
    ax.set_title("Each day's peak demand vs that day's temperature", loc="left", color=INK, fontsize=12,
                 fontweight="bold", pad=24)
    ax.text(0, 1.015, "A U-shape: heating drives winter peaks, air-conditioning drives bigger summer peaks. "
            "Days off sit ~4–8 GW lower.", transform=ax.transAxes, fontsize=8.5, color=INK_2, va="bottom")
    ax.legend(loc="upper center", frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)


def plot_missing(raw: pd.DataFrame, clean: pd.DataFrame, path: Path):
    cols = [c for c in raw.columns if raw[c].isna().any()]
    ren = {"temp_maebashi": "temp_maebashi_c"}
    after = [int(clean[ren.get(c, c + "_pct" if c.startswith("rh_") else c)].isna().sum()) for c in cols]
    before = [int(raw[c].isna().sum()) for c in cols]
    y = range(len(cols))
    fig, ax = plt.subplots(figsize=(7.5, 3.2), facecolor=SURFACE)
    _style(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    off = 0.2
    ax.barh([i - off for i in y], before, height=0.36, color=AVG, label="Before")
    ax.barh([i + off for i in y], after, height=0.36, color=PEAK, label="After")
    for i, (b, a) in enumerate(zip(before, after)):
        ax.text(b + 1, i - off, str(b), va="center", fontsize=8.5, color=INK_2)
        ax.text(a + 1, i + off, str(a), va="center", fontsize=8.5, color=INK_2)
    ax.set_yticks(list(y), cols, color=INK)
    ax.invert_yaxis()
    ax.set_xlabel("Missing hours", color=INK_2, fontsize=9)
    ax.set_title("Missing values before vs after", loc="left", color=INK, fontsize=12, fontweight="bold",
                 pad=22)
    ax.text(0, 1.02, "Short gaps (≤ 3 h) interpolated; multi-day humidity outages left blank on purpose.",
            transform=ax.transAxes, fontsize=8.5, color=INK_2, va="bottom")
    ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)


# --------------------------------------------------------------------------------------
LABELS = {
    "rows": "Rows (hours)",
    "columns": "Columns",
    "missing_cells": "Missing measurement cells",
    "missing_hours_in_timeline": "Hours missing from the timeline",
    "duplicate_timestamps": "Duplicate timestamps",
    "duplicate_rows": "Duplicate rows",
    "out_of_range_values": "Values outside physical limits",
    "demand_sources_disagree_gt3pct": "Hours where TEPCO's two demand figures disagree by > 3 %",
    "unflagged_demand_disagreements": "…of which not flagged",
    "datetime_dtype": "Timestamp type",
    "power_unit": "Power unit",
    "analysis_columns_ready": "Analysis columns (temp band, hour, holiday, workday)",
    "memory_mb": "Memory in pandas (MB)",
}


def summary_table(before, after):
    def f(v):
        return f"{v:,}" if isinstance(v, int) else str(v)
    return pd.DataFrame([{"Check": LABELS[k], "Before": f(before[k]), "After": f(after[k])} for k in LABELS])


def build(raw, clean, daily, before, after, log) -> dict:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    hourly = band_summary(clean)
    hourly_work = band_summary(clean, workdays_only=True)
    daily_bands = daily_band_summary(daily)
    keys = findings(clean, hourly, daily, daily_bands)
    hourly.to_csv(cp.REPORT_DIR / "demand_by_temp_band_hourly.csv")
    hourly_work.to_csv(cp.REPORT_DIR / "demand_by_temp_band_workdays.csv")
    daily_bands.to_csv(cp.REPORT_DIR / "daily_peak_low_by_temp_band.csv")
    (cp.REPORT_DIR / "key_findings.json").write_text(json.dumps(keys, indent=2, ensure_ascii=False))
    plot_bands(hourly, FIG_DIR / "demand_by_temperature_band.png")
    plot_daily(daily, FIG_DIR / "daily_peak_vs_temperature.png")
    plot_missing(raw, clean, FIG_DIR / "missing_before_after.png")

    log_df = pd.DataFrame(log.steps).rename(columns=str.capitalize)
    k = keys
    md = [
        "# Tokyo electricity demand vs JMA temperature — cleaning & temperature-band report",
        "",
        "## Key findings",
        "",
        f"- **Low demand:** average demand bottoms out at **{k['lowest_mean_demand_gw']:.1f} GW** when Tokyo is "
        f"**{k['lowest_mean_demand_band']} °C**: no heating and no cooling. Days whose mean temperature is "
        f"{k['daily_lowest_band']} °C have the lowest daily peaks.",
        f"- **Peak demand:** the highest hourly peak, **{k['highest_peak_gw']:.1f} GW**, falls in the "
        f"**{k['highest_peak_band']} °C** band. Average demand there is "
        f"{k['highest_mean_demand_gw']:.1f} GW, {k['summer_vs_mild_peak_ratio']}x the mild-weather level.",
        f"- **Winter peaks:** cold hours also lift demand (peak {k['winter_peak_gw']:.1f} GW at {k['winter_peak_band']} °C), "
        "but less than summer heat.",
        f"- **All-time hour:** {k['record_hour'][:16]} JST, {k['record_gw']:.1f} GW at {k['record_temp_c']:.1f} °C. "
        f"Lowest hour: {k['lowest_hour'][:16]} JST, {k['lowest_gw']:.1f} GW at {k['lowest_temp_c']:.1f} °C "
        "(Golden Week).",
        "",
        "![Demand by temperature band](figures/demand_by_temperature_band.png)",
        "",
        "![Daily peak vs temperature](figures/daily_peak_vs_temperature.png)",
        "",
        "Caveat: hot hours are mostly afternoons and cold hours mostly early mornings or evenings, so part of each "
        "band's level reflects time of day as well as temperature. The workday-only table removes the weekend effect.",
        "",
        "## Demand by temperature band (all hours)",
        "",
        f"`thin_sample` = fewer than {MIN_HOURS} hours in the band, so treat those rows with caution.",
        "",
        hourly.to_markdown(),
        "",
        "## Demand by temperature band (workdays only)",
        "",
        hourly_work.to_markdown(),
        "",
        "## Daily peak and low demand by daily mean temperature",
        "",
        daily_bands.to_markdown(),
        "",
        "## Data quality: before vs after",
        "",
        summary_table(before, after).to_markdown(index=False, disable_numparse=True,
                                                 colalign=("left", "right", "right")),
        "",
        "![Missing values](figures/missing_before_after.png)",
        "",
        "## Cleaning log",
        "",
        log_df.to_markdown(index=False),
        "",
    ]
    (cp.REPORT_DIR / "report.md").write_text("\n".join(md))
    return keys


if __name__ == "__main__":
    raw, clean_df, daily, before, after, log = cp.main()
    print(json.dumps(build(raw, clean_df, daily, before, after, log), indent=2, ensure_ascii=False))
