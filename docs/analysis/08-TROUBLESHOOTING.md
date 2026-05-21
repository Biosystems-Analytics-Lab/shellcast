# 8. Troubleshooting analysis

> **Doc 8 of 9** · [← 7. Development](07-DEVELOPMENT.md) · [Index](README.md) · [Next: 9. Background & compile →](09-ANALYSIS.md)

Common issues when running `shellcast-analysis` on a workstation or the production iMac.

## Cloud SQL / proxy

| Symptom | Things to check |
|---------|------------------|
| Connection refused on 3306 | Cloud SQL proxy running? `analysis_settings.ini` `HOST`/`PORT` match proxy |
| Access denied | `DB_USER` / `DB_PASS` in `[gcp.mysql]` |
| Wrong data | `DB_NAME` in `[NC]`/`[SC]`/`[FL]` matches intended state |

## PQPF / GRIB

| Symptom | Things to check |
|---------|------------------|
| GRB download failed | NOAA FTP reachable; today's files not yet published (run after ~6:40 ET after 06Z cycle) |
| wgrib2 not found | Installed and on `PATH`; cron may need **full path** (see [09-ANALYSIS.md](09-ANALYSIS.md) §5) |
| wgrib2 fails under cron only | macOS Full Disk Access for Terminal; full path to wgrib2 in code |
| Empty or missing TIFFs | Earlier GRIB step failed — check `error.log` |

## Florida-specific

| Symptom | Things to check |
|---------|------------------|
| No TP outputs | XMRG step in `fl_main.py` / `tp_xmrg.py`; `data/tp/` inventory |
| Download failed / “19 files” | See [GCS bucket download (19 files)](#gcs-bucket-download-19-files) below |
| cnvgrib / CDO errors | [09-ANALYSIS.md](09-ANALYSIS.md) §4.7–4.8 compile steps |

### GCS bucket download (19 files)

When `FLPQPF.main()` calls `get_input_files()` in `pqpf_procs.py`, it downloads **every object** in the configured GCS bucket into `data/pqpf/fl/inputs/` (flat filenames), then checks:

```python
if len(os.listdir(self.inputs_dir)) == 19:
```

**What “19 files” means:** That number is the **expected count of Florida spatial input artifacts** after a full **data prep** upload (`data_prep/fl/` → bucket). It is not 19 days of weather data. A complete set at one time looked like:

| Group | Typical files (basename in `inputs/`) |
|-------|----------------------------------------|
| CMU shapefile | `fl_cmus.shp` plus sidecars (`.dbf`, `.shx`, `.prj`, `.cpg`, `.sbn`, `.sbx`, …) |
| Lease shapefile | `fl_leases.shp` plus the same kinds of sidecars |
| Other outputs | e.g. `fl_cmus.geojson`, `fl_leases.csv`, `fl_leases_boundary.geojson` |

The analysis run only **requires** the shapefiles/CSV named in `[FL]` in `analysis_settings.ini` (e.g. `LEASE_SHP = fl_leases.shp`, `LEASE_CSV = …`). The **19** check is a brittle “everything from the bucket arrived” guard from the automated-upload era.

| If you see this | Things to check |
|-----------------|------------------|
| Count ≠ 19 after download | GCS credentials; bucket empty or out of date; extra/missing blobs (hidden files in `inputs/` also count toward the total) |
| You use **local** inputs only | Place files under `data/pqpf/fl/inputs/` manually (like NC/SC) and **do not** call `get_input_files()` — see [02-CONFIGURATION.md](02-CONFIGURATION.md) `[gcp.bucket]` |
| Upload set changed | Update the `== 19` check in `pqpf_procs.py` or stop using bucket download |

## Database / SAVE_TO_DB

| Symptom | Things to check |
|---------|------------------|
| No rows for today in `cmu_probabilities` | `[*.SaveToDB] SAVE_TO_DB = true` in **production** `analysis_settings.ini` |
| Analysis completes but map stale | Same; or wrong state DB |
| Notification: "No notifications today" | No today's probabilities in DB; procedure `SelectUserLeaseProbsToday` returns empty |

## Email notifications

| Symptom | Things to check |
|---------|------------------|
| Notifications disabled in log | `[STATE.Notification] ENABLE_NOTIFICATIONS = true` |
| Gmail auth error | `gmail-api-token.json` valid; re-run OAuth flow |
| No users after filter | `email_pref = 1` and email set; probabilities meet `prob_pref` |
| Unsubscribe link invalid | `EMAIL_SECRET_KEY` matches between analysis `analysis_settings.ini` and GAE app |
| NC unsubscribe 404 | Deploy `shellcast-web-nc` with `/u/<token>` route |

## Permissions / cron

| Symptom | Things to check |
|---------|------------------|
| Permission denied on `data/` | `chmod` on `shellcast-analysis/data` (see [09-ANALYSIS.md](09-ANALYSIS.md) §5.3) |
| Script not executable | `chmod +x analysis_run.sh` |
| Cron silent failure | Redirect output: `>> ~/Desktop/cron.log 2>&1` |

## Python environment

| Symptom | Things to check |
|---------|------------------|
| `No module named pygrib` | Activate correct venv; `pip install -r analysis/requirements.txt` |
| GDAL/rasterio errors | GDAL system libraries; version pins in `requirements.txt` |

## After git pull on production

| Symptom | Things to check |
|---------|------------------|
| Everything broke | Accidentally overwrote `analysis_settings.ini` — restore from backup |
| No DB writes | Pulled repo `analysis_settings.ini` with `SAVE_TO_DB = false` — restore production config |

## Getting help

- Logs: `analysis/logs/{nc,sc,fl}/error.log`
- Issues: [GitHub](https://github.com/Biosystems-Analytics-Lab/shellcast/issues)
- Contacts in [09-ANALYSIS.md](09-ANALYSIS.md) §8

## Related

- [05-DAILY_OPERATIONS.md](05-DAILY_OPERATIONS.md)
- [02-CONFIGURATION.md](02-CONFIGURATION.md)
- [06-NOTIFICATIONS_ANALYSIS.md](06-NOTIFICATIONS_ANALYSIS.md)
