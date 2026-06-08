# 4. ShellCast data preparation

> **Doc 4 of 9** · [← 3. State guides](03-STATE_GUIDES.md) · [Index](README.md) · [Next: 5. Daily operations →](05-DAILY_OPERATIONS.md)

ShellCast analysis depends on **processed spatial inputs**, not raw agency datasets. For each state, source organizations publish growing areas, leases, and related boundaries on their own schedules. Those sources change over time — geometry, seasonality rules (notably in Florida), file names, and attribute field names can all shift. ShellCast cannot read those files directly; they must be prepared so the pipeline can load shapefiles under `data/pqpf/{nc,sc,fl}/inputs/`, identify **shellfish growing units (CMUs)** and **leases**, and write forecasts to the database.

**All three states need periodic input updates** when upstream data changes. Today that work is **manual** (or ad hoc scripts on a developer machine). Fully automating fetch → process → deploy would be ideal but was not completed — it would need dedicated time to build and maintain.

**Florida** is where automation was attempted: `data_prep/fl/` downloads harvest areas and leases from a web map service, processes them with ArcPy, and was designed to upload results to Google Cloud Storage so the analysis server could pull fresh files. In practice, upstream **URL, dataset name, and field-name changes** broke the pipeline often enough that automatic updates are **not reliable** for now. The bucket path remains in code as an optional experiment; **local** `data/pqpf/fl/inputs/` (same idea as NC and SC) is the practical choice for daily runs — see [02-CONFIGURATION.md](02-CONFIGURATION.md) (`[gcp.bucket]`).

This document focuses on the **Florida ArcPy data-prep** scripts in the repository. North Carolina and South Carolina input updates follow similar manual steps (replace shapefiles under `data/pqpf/nc/inputs/` and `data/pqpf/sc/inputs/` when agencies publish revisions). Detailed file lists and layout for each state are still being documented separately.

## Requirements

- ESRI ArcPy Python library
- Google Cloud Storage Service Credential

## Google Cloud Storage

You will need to log in to the Google Cloud Platform and create a service account to
access the storage bucket. The service account will have a JSON file that contains the
credentials. This JSON file should be stored securely and should not be shared.

### Creating a storage bucket

The data storage bucket is already created for the ShellCast project. However, if you
need to create a new bucket, follow the steps below:
Cloud Storage > Bucket > Create Bucket > follow steps

### Creating a service account

1. API & Services > activate "Cloud Storage API"
2. API & Services > Credentials > Create Credentials > Service Account > follow steps
3. API \* Services > Credentials > Click the service account just created > Add Key >
   JSON > Create
4. Downloaded JSON file is the credential file. This file should not be shared and
   need to be stored securely. In any case, if the file is shared, the service account
   should be deleted and a new one should be created.

### Encrypting the JSON file

The JSON file should be encrypted and stored securely.

## ToDo

This data processing should be done with an open source library. At first, the
developer used ArcPy due to its familiarity.
