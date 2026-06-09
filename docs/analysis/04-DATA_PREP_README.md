# 4. ShellCast data preparation

> **Doc 4 of 9** · [← 3. State guides](03-STATE_GUIDES.md) · [Index](README.md) · [Next: 5. Daily operations →](05-DAILY_OPERATIONS.md)

ShellCast analysis depends on **processed spatial inputs**, not raw upstream datasets. For each state, organizations publish growing areas, leases, and related boundaries on their own schedules. Those exports change over time — geometry, seasonality rules (notably in Florida), file names, and attribute field names can all shift. ShellCast cannot read those files directly; they must be prepared so the pipeline can load shapefiles under `data/pqpf/{nc,sc,fl}/inputs/`, identify **shellfish growing units (CMUs)** and **leases**, and write forecasts to the database.

**All three states need periodic input updates** when upstream data changes. Today that work is **manual** (or ad hoc scripts on an operator machine). Fully automating fetch → process → deploy would be ideal but is not part of this repository.

**Florida** previously experimented with an automated ArcPy pipeline and optional Google Cloud Storage upload so the analysis server could pull fresh files. Upstream endpoint and schema changes made that path unreliable. **Local** `data/pqpf/fl/inputs/` (same idea as NC and SC) is the practical choice for daily runs — see [02-CONFIGURATION.md](02-CONFIGURATION.md) (`[gcp.bucket]`).

North Carolina and South Carolina input updates follow similar manual steps (replace shapefiles under `data/pqpf/nc/inputs/` and `data/pqpf/sc/inputs/` when revisions are available).

## Optional GCS bucket (Florida legacy)

Some deployments still support downloading prepared Florida inputs from a bucket before PQPF runs. Operators who use **local files only** should not call `get_input_files()` in the Florida analysis flow.

## ToDo

- Document per-state shapefile schemas and refresh cadence in operator notes.
- Consider an open-source GIS stack for any future automated prep workflow.
