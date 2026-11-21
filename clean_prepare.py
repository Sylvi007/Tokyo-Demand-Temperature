"""
Clean & prepare hourly Tokyo-area electricity demand (TEPCO) + JMA weather observations.

Source
------
Hourly dataset compiled by kaseee/tokyo-grid-lab (GitHub) from:
  * TEPCO Power Grid "でんき予報" past electricity usage data (area demand, supply capacity, solar), and
  * Japan Meteorological Agency (気象庁) "過去の気象データ・ダウンロード" hourly observations for
    Tokyo, Yokohama, Chiba, Kumagaya, Mito, Utsunomiya, Maebashi, Kofu (+ a population-weighted Kanto mean).
Period: 2022-04-01 00:00 to 2026-10-12 23:00 JST. Units in the raw file: power in 万kW (= 10 MW).

Usage (from the project root):
    python src/clean_prepare.py
"""
from __future__ import annotations

import json
from pathlib import Path

import holidays
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "tokyo_hourly_demand_weather_raw.csv.gz"
CLEAN_DIR = ROOT / "data" / "clean"
REPORT_DIR = ROOT / "reports"

STATIONS = ["tokyo", "yokohama", "chiba", "kumagaya", "mito", "utsunomiya", "maebashi", "kofu", "kanto"]
POWER_COLS = ["demand", "tepco_forecast", "supply", "demand_from_5min", "solar"]  # 万kW
MAX_INTERP_GAP_H = 3          # weather gaps up to this many hours are interpolated in time
MISMATCH_TOL = 0.03           # hourly demand vs mean of 5-minute demand: flag if they differ by >3 %
SPIKE_C = 6.0                 # hour-to-hour temperature change worth checking
TEMP_BAND_EDGES = list(range(-4, 42, 2))   # 2 °C bands from -4 to 40 °C

# Physical plausibility limits used to detect incorrect values.
LIMITS = {
    "temp": (-20.0, 45.0),     # °C, Kanto lowland stations
    "rh": (0.0, 100.0),        # %
    "sun": (0.0, 1.0),         # sunshine hours within one hour
    "demand": (1000.0, 7000.0),  # 万kW; TEPCO area record peak is ~6,000
}


# --------------------------------------------------------------------------------------
def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def _nan_runs(s: pd.Series) -> pd.Series:
    """Length of the run of consecutive NaN each NaN belongs to (0 for non-NaN)."""
    isna = s.isna()
    run_id = (isna != isna.shift()).cumsum()
    return isna.groupby(run_id).transform("sum").where(isna, 0).astype(int)


def profile(df: pd.DataFrame) -> dict:
    """Same checks for raw and clean data (handles both raw and renamed column names)."""
    ts = pd.to_datetime(df["datetime"]) if "datetime" in df else df.index.to_series()
    ts = ts.dt.tz_localize(None) if getattr(ts.dt, "tz", None) is not None else ts
    full = pd.date_range(ts.min(), ts.max(), freq="h")
    def meas(prefix):
        return [c for c in df.columns if c.startswith(prefix + "_") and not c.endswith("_imputed")
                and c != "temp_band"]
    temp, rh, sun = meas("temp"), meas("rh"), meas("sun")
    dem = "demand" if "demand" in df else "demand_gw"
    dem5 = "demand_from_5min" if "demand_from_5min" in df else "demand_5min_avg_gw"
    scale = 1 if dem == "demand" else 100  # clean data is in GW, raw in 万kW
    out_of_range = 0
    for cols, key in [(temp, "temp"), (rh, "rh"), (sun, "sun")]:
        lo, hi = LIMITS[key]
        out_of_range += int(((df[cols] < lo) | (df[cols] > hi)).sum().sum())
    lo, hi = LIMITS["demand"]
    out_of_range += int(((df[dem] * scale < lo) | (df[dem] * scale > hi)).sum())
    flagged = "demand_source_mismatch" in df
    gap = (df[dem] - df[dem5]).abs() / df[dem]
    measured = temp + rh + sun + [c for c in df.columns if c in POWER_COLS + [
        "usage_rate", "demand_gw", "supply_gw", "solar_gw", "tepco_forecast_gw", "demand_5min_avg_gw",
        "usage_rate_pct"]]
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "missing_cells": int(df[measured].isna().sum().sum()),
        "missing_hours_in_timeline": int(len(full.difference(ts))),
        "duplicate_timestamps": int(ts.duplicated().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "out_of_range_values": out_of_range,
        "demand_sources_disagree_gt3pct": int((gap > MISMATCH_TOL).sum()),
        "unflagged_demand_disagreements": 0 if flagged else int((gap > MISMATCH_TOL).sum()),
        "datetime_dtype": str(ts.dtype) if "datetime" not in df else str(df["datetime"].dtype),
        "power_unit": "万kW (10 MW)" if dem == "demand" else "GW",
        "analysis_columns_ready": int(sum(c in df for c in ["temp_band", "is_holiday", "is_workday", "hour"])),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1e6, 2),
    }


class Log:
    def __init__(self):
        self.steps: list[dict] = []

    def add(self, step, action, affected):
        self.steps.append({"step": step, "action": action, "affected": affected})


# --------------------------------------------------------------------------------------
def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, Log]:
    df = raw.copy()
    log = Log()

    # 1. Timestamps -----------------------------------------------------------------------
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S")
    log.add("Data types", "datetime: text -> datetime64 (format %Y-%m-%d %H:%M:%S), localised to Asia/Tokyo", 1)

    # 2. Duplicates ------------------------------------------------------------------------
    n_rows = int(df.duplicated().sum())
    n_ts = int(df["datetime"].duplicated().sum())
    df = df.drop_duplicates().drop_duplicates(subset="datetime", keep="first")
    log.add("Duplicates", f"Checked full-row duplicates ({n_rows}) and duplicate timestamps ({n_ts}); "
            "dropped any found, keeping the first", n_rows + n_ts)

    # 3. Complete hourly timeline -----------------------------------------------------------
    df = df.sort_values("datetime").set_index("datetime")
    full = pd.date_range(df.index.min(), df.index.max(), freq="h")
    missing_hours = len(full.difference(df.index))
    df = df.reindex(full)
    df.index.name = "datetime"
    log.add("Missing values", "Re-indexed to a complete hourly timeline (missing hours would appear as NA rows)",
            missing_hours)

    # 4. Out-of-range values -> NA ---------------------------------------------------------
    n = 0
    for prefix in ["temp", "rh", "sun"]:
        lo, hi = LIMITS[prefix]
        for c in [x for x in df.columns if x.startswith(prefix + "_")]:
            bad = (df[c] < lo) | (df[c] > hi)
            n += int(bad.sum())
            df.loc[bad, c] = np.nan
    lo, hi = LIMITS["demand"]
    bad = (df["demand"] < lo) | (df["demand"] > hi)
    n += int(bad.sum())
    df.loc[bad, "demand"] = np.nan
    log.add("Incorrect values", f"Range checks (temp {LIMITS['temp']} °C, RH 0-100 %, sunshine 0-1 h, "
            f"demand {LIMITS['demand']} 万kW); values outside set to NA", n)

    # 5. Consistency checks ----------------------------------------------------------------
    calc_rate = df["demand"] / df["supply"] * 100
    rate_bad = int(((calc_rate - df["usage_rate"]).abs() > 1).sum())
    log.add("Consistency", "usage_rate matches demand / supply x 100 (within 1 point) - checked", rate_bad)
    night = (df.index.hour < 4) | (df.index.hour >= 20)
    solar_night = int((df.loc[night, "solar"] > 0).sum())
    log.add("Consistency", "Solar output is 0 between 20:00 and 04:00 - checked", solar_night)
    log.add("Consistency", "Demand never exceeds supply capacity - checked", int((df["demand"] > df["supply"]).sum()))

    gap = (df["demand"] - df["demand_from_5min"]).abs() / df["demand"]
    df["demand_source_mismatch"] = (gap > MISMATCH_TOL).fillna(False)
    log.add("Inconsistent values", "Hourly demand and the mean of TEPCO's 5-minute readings differ by >3 % "
            "(2025-01-23, 2026-02-09 cold snaps). Kept the official hourly value; flagged in "
            "demand_source_mismatch", int(df["demand_source_mismatch"].sum()))

    # Sudden temperature drops: confirm with the neighbouring station before treating as errors.
    neighbours = {"maebashi": "kumagaya", "kofu": "kumagaya", "kumagaya": "maebashi", "tokyo": "yokohama",
                  "yokohama": "tokyo", "chiba": "tokyo", "mito": "utsunomiya", "utsunomiya": "mito"}
    spikes, confirmed = 0, 0
    for st, nb in neighbours.items():
        d = df[f"temp_{st}"].diff().abs()
        for t in df.index[d > SPIKE_C]:
            spikes += 1
            window = df.loc[t - pd.Timedelta(hours=1): t + pd.Timedelta(hours=3), f"temp_{nb}"]
            if window.max() - window.min() > 3:   # neighbour also cooled sharply -> real (thunderstorm)
                confirmed += 1
            else:
                df.loc[t, f"temp_{st}"] = np.nan
    log.add("Incorrect values", f"Hour-to-hour temperature jumps > {SPIKE_C} °C: {spikes} found; {confirmed} "
            "confirmed as real (a nearby station cooled at the same time, e.g. summer thunderstorms) and kept, "
            "the rest set to NA", spikes - confirmed)

    # 6. Missing weather values ------------------------------------------------------------
    weather = [c for c in df.columns if c.split("_")[0] in {"temp", "rh", "sun"}]
    filled, left = 0, 0
    for c in weather:
        runs = _nan_runs(df[c])
        short = (runs > 0) & (runs <= MAX_INTERP_GAP_H)
        if short.any():
            interp = df[c].interpolate(method="time", limit_area="inside")
            df[f"{c}_imputed"] = short
            df.loc[short, c] = interp[short]
            filled += int(short.sum())
        left += int((runs > MAX_INTERP_GAP_H).sum())
    log.add("Missing values", f"Weather gaps of <= {MAX_INTERP_GAP_H} h filled by time interpolation "
            "(flagged in <column>_imputed)", filled)
    long_gaps = {c: int((_nan_runs(df[c]) > MAX_INTERP_GAP_H).sum()) for c in weather
                 if (_nan_runs(df[c]) > MAX_INTERP_GAP_H).any()}
    log.add("Missing values", f"Longer gaps left as NA on purpose (station outages of 1-3 days; "
            f"interpolating would invent data): {long_gaps}", left)
    log.add("Missing values", "Demand and Tokyo temperature (the analysis columns) have no missing values",
            int(df[["demand", "temp_tokyo"]].isna().sum().sum()))

    # 7. Units, names, types ---------------------------------------------------------------
    for c in POWER_COLS:
        df[c] = (df[c] / 100).round(4)  # 万kW -> GW
    df = df.rename(columns={"demand": "demand_gw", "tepco_forecast": "tepco_forecast_gw", "supply": "supply_gw",
                            "demand_from_5min": "demand_5min_avg_gw", "solar": "solar_gw",
                            "usage_rate": "usage_rate_pct"})
    df = df.rename(columns={c: f"{c}_c" if c.startswith("temp_") and not c.endswith("_imputed") else c
                            for c in df.columns})
    df = df.rename(columns={c: f"{c}_pct" if c.startswith("rh_") and not c.endswith("_imputed") else c
                            for c in df.columns})
    df = df.rename(columns={c: f"{c}_h" if c.startswith("sun_") and not c.endswith("_imputed") else c
                            for c in df.columns})
    df["usage_rate_pct"] = df["usage_rate_pct"].astype("Int16")
    float_cols = df.select_dtypes("float64").columns
    df[float_cols] = df[float_cols].astype("float32")
    df.index = df.index.tz_localize("Asia/Tokyo")
    log.add("Units", "Power columns converted from 万kW (10 MW) to GW; columns renamed with units "
            "(_gw, _c, _pct, _h)", len(POWER_COLS))
    log.add("Data types", "Measurements float64 -> float32 (0.1 °C / 0.01 GW precision is kept); usage_rate -> "
            "Int16; flags -> bool", len(float_cols))

    # 8. Analysis features ------------------------------------------------------------------
    jp = holidays.Japan(years=range(df.index.year.min(), df.index.year.max() + 1))
    local = df.index.tz_localize(None)
    df["date"] = local.normalize()
    df["year"] = local.year.astype("int16")
    df["month"] = local.month.astype("int8")
    df["hour"] = local.hour.astype("int8")
    df["weekday"] = pd.Categorical(local.day_name(), categories=[
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], ordered=True)
    df["is_holiday"] = pd.Series(local.date, index=df.index).map(lambda d: d in jp).astype(bool)
    # New-year (Dec 29 - Jan 3) and Obon (Aug 13-16) are de-facto holidays for business demand.
    md = local.month * 100 + local.day
    df["is_holiday"] |= np.isin(md, [1229, 1230, 1231, 101, 102, 103, 813, 814, 815, 816])
    df["is_workday"] = (local.dayofweek < 5) & ~df["is_holiday"]
    df["season"] = pd.Categorical(
        pd.Series(local.month, index=df.index).map({12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring",
                                                    5: "Spring", 6: "Summer", 7: "Summer", 8: "Summer",
                                                    9: "Autumn", 10: "Autumn", 11: "Autumn"}),
        categories=["Winter", "Spring", "Summer", "Autumn"], ordered=True)
    labels = [f"{a} to {a + 2}" for a in TEMP_BAND_EDGES[:-1]]
    df["temp_band"] = pd.cut(df["temp_tokyo_c"], bins=TEMP_BAND_EDGES, labels=labels, right=False, ordered=True)
    log.add("Derived", "Added date, year, month, hour, weekday, season, is_holiday (JP national holidays + "
            "New Year + Obon), is_workday, temp_band (2 °C bands of Tokyo temperature)", 9)
    out_band = int(df["temp_band"].isna().sum() - df["temp_tokyo_c"].isna().sum())
    if out_band:
        log.add("Derived", "Tokyo temperatures outside the -4 to 40 °C band range", out_band)

    flags = ["demand_source_mismatch"] + [c for c in df.columns if c.endswith("_imputed")]
    df[flags] = df[flags].astype(bool)
    front = ["date", "year", "month", "hour", "weekday", "season", "is_holiday", "is_workday",
             "demand_gw", "tepco_forecast_gw", "supply_gw", "usage_rate_pct", "demand_5min_avg_gw", "solar_gw",
             "temp_tokyo_c", "temp_band"]
    rest = [c for c in df.columns if c not in front and c not in flags]
    df = df[front + rest + flags]
    return df, log


def daily_table(df: pd.DataFrame) -> pd.DataFrame:
    """One row per day: peak and low demand with the day's Tokyo temperatures."""
    g = df.groupby("date", observed=True)
    out = pd.DataFrame({
        "peak_demand_gw": g["demand_gw"].max(),
        "peak_hour": g.apply(lambda x: int(x.loc[x["demand_gw"].idxmax(), "hour"]), include_groups=False),
        "low_demand_gw": g["demand_gw"].min(),
        "mean_demand_gw": g["demand_gw"].mean().round(3),
        "max_temp_c": g["temp_tokyo_c"].max(),
        "min_temp_c": g["temp_tokyo_c"].min(),
        "mean_temp_c": g["temp_tokyo_c"].mean().round(2),
        "is_workday": g["is_workday"].first(),
        "season": g["season"].first(),
    })
    out.index = pd.to_datetime(out.index)
    return out


# --------------------------------------------------------------------------------------
def export(df: pd.DataFrame, daily: pd.DataFrame, out_dir: Path = CLEAN_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "hourly_csv": out_dir / "tokyo_hourly_clean.csv",
        "hourly_parquet": out_dir / "tokyo_hourly_clean.parquet",
        "daily_csv": out_dir / "tokyo_daily_peak_low.csv",
        "schema": out_dir / "schema.json",
    }
    df.to_csv(paths["hourly_csv"], date_format="%Y-%m-%d %H:%M:%S%z")
    df.to_parquet(paths["hourly_parquet"])
    daily.to_csv(paths["daily_csv"], date_format="%Y-%m-%d")
    paths["schema"].write_text(json.dumps({"index": "datetime (Asia/Tokyo)",
                                           **{c: str(t) for c, t in df.dtypes.items()}}, indent=2))
    return paths


def main():
    raw = load_raw()
    before = profile(raw)
    clean_df, log = clean(raw)
    after = profile(clean_df)
    daily = daily_table(clean_df)
    paths = export(clean_df, daily)
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "quality_metrics.json").write_text(json.dumps({"before": before, "after": after}, indent=2))
    pd.DataFrame(log.steps).to_csv(REPORT_DIR / "cleaning_log.csv", index=False)
    print(pd.DataFrame({"before": before, "after": after}).to_string())
    print("\nSaved:", *[str(p.relative_to(ROOT)) for p in paths.values()], sep="\n  ")
    return raw, clean_df, daily, before, after, log


if __name__ == "__main__":
    main()
