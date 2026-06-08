# COMMANDS.md

> **05-DEVELOPMENT** subsection · [← 5. Development](../05-DEVELOPMENT.md) · [Index](../README.md)

## Google App Engine Commands

### Deploy to App Engine

```bash
# Check without deploying: run same command GAE uses (from app dir, e.g. web/shellcast-web-nc)
# If this starts and http://localhost:8080 works, GAE should not 502. Stop with Ctrl+C.
# See 04-DEPLOY_GAE.md § "Check before deploying" for example successful log output.
gunicorn -b :8080 main:app

# Deploy and migrate traffic to new version
gcloud app deploy app.yaml cron.yaml

# Test on GAE without traffic: deploy --no-promote -v staging, then open version URL
gcloud app deploy app.yaml cron.yaml --no-promote -v staging
# After testing: gcloud app services set-traffic default --splits=staging=1

# Deploy without using cached images
gcloud app deploy --no-cache
```

See [04-DEPLOY_GAE.md](../04-DEPLOY_GAE.md) for full workflow (local check + test-before-commit on GAE).

### Clean Up Staging Storage

```bash
# Delete all staging files at once (replace PROJECT_NAME with your actual project)
gsutil -m rm "gs://staging.PROJECT_NAME.appspot.com/**"

# Delete only container images (more selective)
gsutil -m rm "gs://staging.PROJECT_NAME.appspot.com/containers/images/**"
```

### Cloud SQL Proxy Commands

From **repository root** (see [01-GETTING_STARTED.md](../01-GETTING_STARTED.md) §2):

```bash
# One-time: personal proxy script (gitignored)
cp my-cloud-sql-proxy.template.sh my-cloud-sql-proxy.sh
# Edit instance_connection_name, then:
chmod +x my-cloud-sql-proxy.sh

# One-time download of proxy binaries
sh cloud-sql-proxy-setup.sh

# Web local dev (Unix socket — leave running)
./my-cloud-sql-proxy.sh web

# Analysis local dev (TCP port 3306)
./my-cloud-sql-proxy.sh analysis

# Stop proxy: Ctrl+C
```

### OpenLayers build

```bash
cd web/shellcast-web-nc
npm install && npm run build   # OpenLayers 9.2.4 → static/lib/ol.js, ol.css
```

### Project Information

```bash
# Check current project and authentication
gcloud info

# List all projects
gcloud projects list

# Set active project
gcloud config set project PROJECT_NAME
```

## Development Commands

### Python Virtual Environment

```bash
# Activate virtual environment (from web directory)
source webenv/bin/activate

# Deactivate
deactivate
```

### Run Application Locally

```bash
# Navigate to specific state app
cd web/shellcast-web-{fl|nc|sc}

# Run the application
python main.py
```

### Testing Commands

```bash
# Run all tests
python -m pytest -v

# Run with coverage
python -m pytest -v --cov

# Generate HTML coverage report
coverage html
```

## Data Analysis Commands

### Run Analysis Scripts

```bash
# Navigate to analysis directory
cd analysis/shellcast-analysis

# Run specific analysis
python fl_main.py
python nc_main.py
python sc_main.py
```

## File Management

### Delete Files/Directories

```bash
# Delete all files in a directory
rm -rf directory_name/*

# Delete specific file types
find . -name "*.tmp" -delete
```

---

## Quick Reference

| Task                  | Command                                                   |
| --------------------- | --------------------------------------------------------- |
| Deploy to App Engine  | `gcloud app deploy`                                       |
| Clean staging storage | `gsutil -m rm "gs://staging.PROJECT_NAME.appspot.com/**"` |
| Start Cloud SQL proxy | `source my-cloud-sql-proxy-connection.sh`                 |
| Check project         | `gcloud info`                                             |
| Run tests             | `python -m pytest -v`                                     |

## Notes

- Replace `PROJECT_NAME` with your actual Google Cloud project name
- Always check `gcloud info` before deploying to ensure correct project
- Use `--no-cache` flag if you've deleted all staging files
- Remember to activate virtual environment before running Python commands
