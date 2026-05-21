# 4. ShellCast data preparation

> **Doc 4 of 9** · [← 3. State guides](03-STATE_GUIDES.md) · [Index](README.md) · [Next: 5. Daily operations →](05-DAILY_OPERATIONS.md)

ShellCast requires input data for analysis. North Carolina and South Carolina
occasionally require data updates, which are done manually. Florida's shellfish harvest
areas have seasonality dates. Most of them are all seasons, while some are spring or
fall, or both. In addition, the dates may change. To reflect seasonality changes to
ShellCast forecasting, shellfish harvest areas and leases data are downloaded from a
web map server. Then, they are processed for ShellCast analysis input. This repository
contains the scripts and data used to prepare the data for Florida ShellCast analysis.

Uploading results to a GCS bucket was meant to automate analysis input updates; that approach did not remain reliable (changing source URLs and field names). **Local** `data/pqpf/fl/inputs/` is the practical path for daily runs — see [02-CONFIGURATION.md](02-CONFIGURATION.md) (`[gcp.bucket]`).

> **Input dataset documentation** (shapefile layout, NC/SC manual updates, bucket layout, file lists) is planned as a separate guide. For daily analysis setup and how inputs are consumed at run time, see the [analysis documentation index](README.md) and [03-STATE_GUIDES.md](03-STATE_GUIDES.md).

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
