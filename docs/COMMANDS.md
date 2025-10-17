# ShellCast Useful Commands

## Google App Engine Commands

### Deploy to App Engine

```bash
# Deploy and migrate traffic to new version
gcloud app deploy

# Deploy without migrating traffic
gcloud app deploy --no-promote

# Deploy without using cached images
gcloud app deploy --no-cache
```

### Clean Up Staging Storage

```bash
# Delete all staging files at once (replace PROJECT_NAME with your actual project)
gsutil -m rm "gs://staging.PROJECT_NAME.appspot.com/**"

# Delete only container images (more selective)
gsutil -m rm "gs://staging.PROJECT_NAME.appspot.com/containers/images/**"
```

### Cloud SQL Proxy Commands

```bash
# Start Cloud SQL proxy with TCP connection
source my-cloud-sql-proxy-connection.sh

# Stop proxy: Ctrl+C
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
