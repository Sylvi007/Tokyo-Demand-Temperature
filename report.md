# Tokyo electricity demand vs JMA temperature — cleaning & temperature-band report

## Key findings

- **Low demand:** average demand bottoms out at **26.6 GW** when Tokyo is **16 to 18 °C**: no heating and no cooling. Days whose mean temperature is 16 to 18 °C have the lowest daily peaks.
- **Peak demand:** the highest hourly peak, **59.3 GW**, falls in the **34 to 36 °C** band. Average demand there is 50.2 GW, 1.88x the mild-weather level.
- **Winter peaks:** cold hours also lift demand (peak 51.8 GW at 0 to 2 °C), but less than summer heat.
- **All-time hour:** 2022-08-02 13:00 JST, 59.3 GW at 34.9 °C. Lowest hour: 2025-05-04 06:00 JST, 18.5 GW at 15.9 °C (Golden Week).

![Demand by temperature band](figures/demand_by_temperature_band.png)

![Daily peak vs temperature](figures/daily_peak_vs_temperature.png)

Caveat: hot hours are mostly afternoons and cold hours mostly early mornings or evenings, so part of each band's level reflects time of day as well as temperature. The workday-only table removes the weekend effect.

## Demand by temperature band (all hours)

`thin_sample` = fewer than 30 hours in the band, so treat those rows with caution.

| temp_band   |   hours |   low_gw |   p5_gw |   mean_gw |   p95_gw |   peak_gw | thin_sample   |
|:------------|--------:|---------:|--------:|----------:|---------:|----------:|:--------------|
| -4 to -2    |      10 |    33.71 |   33.93 |     37.86 |    44.78 |     46.49 | True          |
| -2 to 0     |      70 |    27.06 |   31.53 |     38.12 |    47.32 |     50.5  | False         |
| 0 to 2      |     406 |    25.63 |   28.68 |     35.12 |    49.19 |     51.79 | False         |
| 2 to 4      |    1249 |    23.56 |   27.14 |     34.1  |    44.68 |     50.29 | False         |
| 4 to 6      |    2101 |    23.63 |   26.36 |     34.42 |    44.81 |     48.39 | False         |
| 6 to 8      |    2284 |    21.99 |   25.55 |     34.4  |    42.93 |     46.2  | False         |
| 8 to 10     |    2442 |    21.19 |   24.21 |     33.08 |    41.12 |     44.61 | False         |
| 10 to 12    |    2634 |    19.95 |   22.63 |     30.78 |    39.16 |     42.96 | False         |
| 12 to 14    |    2605 |    18.71 |   21.63 |     28.82 |    36.92 |     42.16 | False         |
| 14 to 16    |    2555 |    18.53 |   21    |     27.31 |    34.6  |     40.57 | False         |
| 16 to 18    |    2858 |    18.64 |   20.81 |     26.64 |    33.46 |     36.02 | False         |
| 18 to 20    |    2971 |    18.55 |   21.14 |     26.76 |    32.77 |     37.58 | False         |
| 20 to 22    |    3080 |    19.27 |   21.84 |     27.29 |    33.09 |     41.43 | False         |
| 22 to 24    |    3035 |    19.91 |   22.71 |     28.76 |    34.98 |     43.32 | False         |
| 24 to 26    |    3054 |    20.37 |   24.21 |     30.63 |    38.45 |     45.94 | False         |
| 26 to 28    |    3363 |    22.9  |   25.58 |     32.61 |    41.49 |     49.43 | False         |
| 28 to 30    |    2325 |    25.46 |   28.8  |     38.13 |    46.09 |     52.68 | False         |
| 30 to 32    |    1363 |    28.3  |   34.86 |     43.35 |    50.44 |     57.5  | False         |
| 32 to 34    |     959 |    35.4  |   39.45 |     47.7  |    53.35 |     58.48 | False         |
| 34 to 36    |     351 |    39.67 |   42.49 |     50.2  |    56.28 |     59.3  | False         |
| 36 to 38    |      28 |    45.9  |   46.53 |     53.02 |    57.02 |     57.38 | True          |
| 38 to 40    |       1 |    46.67 |   46.67 |     46.67 |    46.67 |     46.67 | True          |

## Demand by temperature band (workdays only)

| temp_band   |   hours |   low_gw |   p5_gw |   mean_gw |   p95_gw |   peak_gw | thin_sample   |
|:------------|--------:|---------:|--------:|----------:|---------:|----------:|:--------------|
| -4 to -2    |      10 |    33.71 |   33.93 |     37.86 |    44.78 |     46.49 | True          |
| -2 to 0     |      44 |    31.44 |   32.11 |     38.23 |    48.93 |     50.5  | False         |
| 0 to 2      |     258 |    27.31 |   30.05 |     36.7  |    49.69 |     51.79 | False         |
| 2 to 4      |     763 |    25.14 |   28.5  |     35.45 |    45.79 |     50.29 | False         |
| 4 to 6      |    1301 |    25.28 |   27.56 |     36.06 |    45.49 |     48.39 | False         |
| 6 to 8      |    1511 |    22.74 |   26.15 |     35.86 |    43.54 |     46.2  | False         |
| 8 to 10     |    1636 |    21.26 |   24.39 |     34.39 |    41.58 |     44.61 | False         |
| 10 to 12    |    1778 |    20.03 |   23    |     32.01 |    39.51 |     42.96 | False         |
| 12 to 14    |    1713 |    19.96 |   22.18 |     30.16 |    37.45 |     42.16 | False         |
| 14 to 16    |    1687 |    19.78 |   21.61 |     28.39 |    35.12 |     40.57 | False         |
| 16 to 18    |    1940 |    19.49 |   21.67 |     27.73 |    33.72 |     36.02 | False         |
| 18 to 20    |    2028 |    20.24 |   21.75 |     27.88 |    33.09 |     37.58 | False         |
| 20 to 22    |    1949 |    20.42 |   22.47 |     28.59 |    33.48 |     41.43 | False         |
| 22 to 24    |    1963 |    21.75 |   23.57 |     30.14 |    35.71 |     43.32 | False         |
| 24 to 26    |    1996 |    22.54 |   25.08 |     31.99 |    39.61 |     45.94 | False         |
| 26 to 28    |    2135 |    23.84 |   26.74 |     34.03 |    42.49 |     49.43 | False         |
| 28 to 30    |    1569 |    25.46 |   29.84 |     39.76 |    46.66 |     52.68 | False         |
| 30 to 32    |     893 |    28.3  |   37.59 |     45.78 |    50.93 |     57.5  | False         |
| 32 to 34    |     647 |    40.06 |   45.9  |     50.28 |    53.85 |     58.48 | False         |
| 34 to 36    |     221 |    46.09 |   50.16 |     53.39 |    57.41 |     59.3  | False         |
| 36 to 38    |      22 |    51.71 |   52.35 |     54.71 |    57.03 |     57.38 | True          |

## Daily peak and low demand by daily mean temperature

| daily_mean_temp_band   |   days |   avg_daily_peak_gw |   highest_daily_peak_gw |   avg_daily_low_gw |   lowest_daily_low_gw |
|:-----------------------|-------:|--------------------:|------------------------:|-------------------:|----------------------:|
| -2 to 0                |      2 |               49.44 |                   51.37 |              32.69 |                 31.67 |
| 0 to 2                 |      1 |               51.79 |                   51.79 |              30.07 |                 30.07 |
| 2 to 4                 |     23 |               45.31 |                   50.29 |              30.69 |                 26.88 |
| 4 to 6                 |     94 |               42.18 |                   48.37 |              29.19 |                 23.86 |
| 6 to 8                 |    141 |               40.16 |                   46.85 |              27.81 |                 22    |
| 8 to 10                |    113 |               37.89 |                   45.29 |              26.77 |                 22.25 |
| 10 to 12               |     96 |               35.41 |                   41.54 |              25.1  |                 21.62 |
| 12 to 14               |     94 |               33.06 |                   36.87 |              23.41 |                 20.03 |
| 14 to 16               |    113 |               31.5  |                   36.57 |              22.57 |                 19.09 |
| 16 to 18               |    117 |               30.54 |                   36.06 |              21.79 |                 18.61 |
| 18 to 20               |    136 |               30.87 |                   36.2  |              21.56 |                 18.53 |
| 20 to 22               |    143 |               31.91 |                   37.89 |              21.8  |                 18.55 |
| 22 to 24               |    130 |               34.76 |                   43.04 |              22.57 |                 19.18 |
| 24 to 26               |     92 |               37.59 |                   45.45 |              23.5  |                 20.24 |
| 26 to 28               |    123 |               43.11 |                   50.98 |              25.22 |                 21.83 |
| 28 to 30               |    165 |               47.7  |                   54.62 |              26.52 |                 22.91 |
| 30 to 32               |     70 |               51.14 |                   59.3  |              27.42 |                 24.28 |
| 32 to 34               |      3 |               57.19 |                   57.54 |              29.45 |                 28.3  |

## Data quality: before vs after

| Check                                                    |       Before |          After |
|:---------------------------------------------------------|-------------:|---------------:|
| Rows (hours)                                             |       39,744 |         39,744 |
| Columns                                                  |           34 |             45 |
| Missing measurement cells                                |          229 |            225 |
| Hours missing from the timeline                          |            0 |              0 |
| Duplicate timestamps                                     |            0 |              0 |
| Duplicate rows                                           |            0 |              0 |
| Values outside physical limits                           |            0 |              0 |
| Hours where TEPCO's two demand figures disagree by > 3 % |            8 |              8 |
| …of which not flagged                                    |            8 |              0 |
| Timestamp type                                           |          str | datetime64[us] |
| Power unit                                               | 万kW (10 MW) |             GW |
| Analysis columns (temp band, hour, holiday, workday)     |            0 |              4 |
| Memory in pandas (MB)                                    |        11.57 |           6.32 |

![Missing values](figures/missing_before_after.png)

## Cleaning log

| Step                | Action                                                                                                                                                                        |   Affected |
|:--------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------:|
| Data types          | datetime: text -> datetime64 (format %Y-%m-%d %H:%M:%S), localised to Asia/Tokyo                                                                                              |          1 |
| Duplicates          | Checked full-row duplicates (0) and duplicate timestamps (0); dropped any found, keeping the first                                                                            |          0 |
| Missing values      | Re-indexed to a complete hourly timeline (missing hours would appear as NA rows)                                                                                              |          0 |
| Incorrect values    | Range checks (temp (-20.0, 45.0) °C, RH 0-100 %, sunshine 0-1 h, demand (1000.0, 7000.0) 万kW); values outside set to NA                                                      |          0 |
| Consistency         | usage_rate matches demand / supply x 100 (within 1 point) - checked                                                                                                           |          0 |
| Consistency         | Solar output is 0 between 20:00 and 04:00 - checked                                                                                                                           |          0 |
| Consistency         | Demand never exceeds supply capacity - checked                                                                                                                                |          0 |
| Inconsistent values | Hourly demand and the mean of TEPCO's 5-minute readings differ by >3 % (2025-01-23, 2026-02-09 cold snaps). Kept the official hourly value; flagged in demand_source_mismatch |          8 |
| Incorrect values    | Hour-to-hour temperature jumps > 6.0 °C: 2 found; 2 confirmed as real (a nearby station cooled at the same time, e.g. summer thunderstorms) and kept, the rest set to NA      |          0 |
| Missing values      | Weather gaps of <= 3 h filled by time interpolation (flagged in <column>_imputed)                                                                                             |          4 |
| Missing values      | Longer gaps left as NA on purpose (station outages of 1-3 days; interpolating would invent data): {'rh_chiba': 71, 'rh_kumagaya': 32, 'rh_utsunomiya': 82, 'rh_maebashi': 40} |        225 |
| Missing values      | Demand and Tokyo temperature (the analysis columns) have no missing values                                                                                                    |          0 |
| Units               | Power columns converted from 万kW (10 MW) to GW; columns renamed with units (_gw, _c, _pct, _h)                                                                               |          5 |
| Data types          | Measurements float64 -> float32 (0.1 °C / 0.01 GW precision is kept); usage_rate -> Int16; flags -> bool                                                                      |         32 |
| Derived             | Added date, year, month, hour, weekday, season, is_holiday (JP national holidays + New Year + Obon), is_workday, temp_band (2 °C bands of Tokyo temperature)                  |          9 |
