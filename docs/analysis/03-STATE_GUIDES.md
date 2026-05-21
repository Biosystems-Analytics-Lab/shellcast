# 3. State guides (NC, SC, FL)

> **Doc 3 of 9** · [← 2. Configuration](02-CONFIGURATION.md) · [Index](README.md) · [Next: 4. Data prep →](04-DATA_PREP_README.md)

Each state has its own Cloud SQL database, shapefile inputs, and Python module under `src/{state}_pqpf/`. All three share `pqpf_procs.py` and `utils.py`.

## Comparison

| | North Carolina | South Carolina | Florida |
|--|----------------|----------------|---------|
| **Main** | `nc_main.py` | `sc_main.py` | `fl_main.py` |
| **Module** | `nc_pqpf/nc_pqpf.py` | `sc_pqpf/sc_pqpf.py` | `fl_pqpf/fl_pqpf.py` |
| **Database** | `shellcast_nc` | `shellcast_sc` | `shellcast_fl` |
| **Forecast days in email** | Today + 2 days | Today + 2 days | Today only |
| **CMU + lease** | Yes (points) | Lease polygons only | Yes (season-aware CMU) |
| **Extra weather data** | PQPF only | PQPF only | PQPF + XMRG accumulation (`tp_xmrg.py`) |
| **Spatial inputs** | Local `data/pqpf/nc/inputs/` | Local `data/pqpf/sc/inputs/` | Local `data/pqpf/fl/inputs/` (GCS bucket optional; see [02-CONFIGURATION.md](02-CONFIGURATION.md)) |
| **PQPF thresholds (inches)** | 1.0, 1.5, 2.0, 2.5, 3.0, 4.0 | 4.0 (zonal) | Duration-based via rainfall rules |
| **Web app** | shellcast-web-nc | shellcast-web-sc | shellcast-web-fl |

## North Carolina

**Flow (`NCPQPF.main`):**

1. Download today's PQPF GRIBs from NOAA FTP
2. Crop/subset/process GRIB → GeoTIFF
3. Sample probabilities at lease points; mean within CMU
4. Map to categories 1–5 (Very Low → Very High)
5. Write CSV → MySQL if `SAVE_TO_DB`
6. `EmailNotification` — 3-day lease text in body

**Key config (`[NC]`):** `CMU_SHP`, `LEASE_SHP`, column names, `LON_WE`, `LAT_SN`.

## South Carolina

**Flow (`SCPQPF.main`):**

1. PQPF download and TIFF pipeline (shared)
2. **Zonal statistics** on lease polygons (`rasterstats`)
3. Single threshold from `[SC] THRESHOLD`
4. Save to DB; email with 3-day probabilities

**Note:** SHA boundaries are treated as lease areas (no separate CMU layer like NC).

## Florida

**Flow (`fl_main.py`):**

1. **`TPXMRG`** — download/process daily rainfall accumulation (XMRG), inventory in `data/tp/`
2. **`FLPQPF.main`:**
   - Optional `get_input_files()` — may download from GCS into `data/pqpf/fl/inputs/` if enabled; **local files are the normal path** (same idea as NC/SC)
   - PQPF pipeline
   - Combine accumulation with PQPF thresholds (season logic in `get_season_now`)
   - Save lease + CMU CSVs to DB
3. **`EmailNotification`** with `prob_only_today=True`
4. Optional **`DevEmailNotificationFL`** — CSV attachments to developers

**Key config (`[FL]`):** `LEASE_SHP`, `LEASE_CSV`, `LEASE_SHP_COL_CMU_NAME`, etc.

## Probability categories

All states map numeric model output to categories **1–5** for display and email:

| Value | Label |
|-------|--------|
| 1 | Very Low |
| 2 | Low |
| 3 | Moderate |
| 4 | High |
| 5 | Very High |

User `prob_pref` in the database is a minimum category (1–5). Analysis includes a user when today's (and for NC/SC, tomorrow's or day+2) forecast **meets or exceeds** that preference.

## Code entry points

```text
analysis_run.sh
  → nc_main.py  → DirectoryConfig("NC") → NCPQPF → EmailNotification
  → sc_main.py  → DirectoryConfig("SC") → SCPQPF → EmailNotification
  → fl_main.py  → TPXMRG → FLPQPF → EmailNotification (+ DevEmailNotificationFL)
```

## Related

- [09-ANALYSIS.md](09-ANALYSIS.md) — PQPF and XMRG data specifications
- Input shapefiles — your input-dataset documentation (in progress)
- [06-NOTIFICATIONS_ANALYSIS.md](06-NOTIFICATIONS_ANALYSIS.md)
