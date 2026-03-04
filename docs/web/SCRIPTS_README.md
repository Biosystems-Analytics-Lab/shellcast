# ShellCast Scripts

This directory contains utility scripts for managing ShellCast deployments and Google Cloud Storage cleanup.

## Scripts Overview

### 1. `cleanup-staging-enhanced.sh`

An enhanced version of the staging cleanup script with multiple options and better error handling.

**Features:**

- Support for multiple projects
- Force cleanup option
- List staging files without deleting
- Clean specific staging directories only
- Comprehensive error handling and colored output

**Usage:**

```bash
# Basic usage (with confirmation)
./scripts/cleanup-staging-enhanced.sh

# Force cleanup without confirmation
./scripts/cleanup-staging-enhanced.sh -f

# Clean staging for specific project
./scripts/cleanup-staging-enhanced.sh -p ncsu-shellcast

# List staging files instead of deleting
./scripts/cleanup-staging-enhanced.sh -l

# Clean only specific staging directories
./scripts/cleanup-staging-enhanced.sh -s

# Clean staging for all known ShellCast projects
./scripts/cleanup-staging-enhanced.sh -a

# Show help
./scripts/cleanup-staging-enhanced.sh -h
```

**Options:**

- `-p, --project PROJECT_NAME`: Specify project name (default: current gcloud project)
- `-f, --force`: Force cleanup without confirmation
- `-l, --list`: List staging files instead of deleting
- `-s, --specific`: Clean only specific staging directories
- `-a, --all-projects`: Clean staging for all known ShellCast projects
- `-h, --help`: Show help message

### 2. `deploy-and-cleanup.sh`

A comprehensive deployment script that combines App Engine deployment with automatic staging cleanup.

**Features:**

- Deploy to Google App Engine
- Automatic staging cleanup after deployment
- Support for all gcloud app deploy options
- Validation of deployment directory
- Option to skip cleanup or run cleanup only

**Usage:**

```bash
# Deploy FL app and cleanup staging
./scripts/deploy-and-cleanup.sh -d web/shellcast-web-fl

# Deploy NC app without promoting traffic
./scripts/deploy-and-cleanup.sh -d web/shellcast-web-nc --no-promote

# Deploy SC app with force cleanup
./scripts/deploy-and-cleanup.sh -d web/shellcast-web-sc -f

# Deploy without cleanup
./scripts/deploy-and-cleanup.sh -d web/shellcast-web-fl -n

# Only run cleanup (skip deployment)
./scripts/deploy-and-cleanup.sh -c -p ncsu-shellcast

# Deploy with no-cache option
./scripts/deploy-and-cleanup.sh -d web/shellcast-web-fl --no-cache
```

**Options:**

- `-d, --directory DIR`: Specify the web app directory to deploy
- `-p, --project PROJECT_NAME`: Specify project name (default: current gcloud project)
- `-f, --force`: Force cleanup without confirmation
- `-n, --no-cleanup`: Skip staging cleanup after deployment
- `-c, --cleanup-only`: Only run cleanup, skip deployment
- `-h, --help`: Show help message

**Deploy Options:**

- `--no-promote`: Deploy without promoting traffic
- `--no-cache`: Deploy without using cached files
- `--version VERSION`: Deploy specific version

### 3. `cleanup-staging.sh` (Original)

The original staging cleanup script with basic functionality.

**Usage:**

```bash
./scripts/cleanup-staging.sh
```

## Prerequisites

Before using these scripts, ensure you have:

1. **Google Cloud SDK installed:**

   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   ```

2. **Authenticated with Google Cloud:**

   ```bash
   gcloud auth login
   ```

3. **Set the correct project:**
   ```bash
   gcloud config set project YOUR_PROJECT_NAME
   ```

## Common Workflows

### Standard Deployment with Cleanup

```bash
# Deploy and cleanup staging files
./scripts/deploy-and-cleanup.sh -d web/shellcast-web-fl
```

### Force Cleanup After Manual Deployment

```bash
# If you deployed manually and want to clean up staging
./scripts/cleanup-staging-enhanced.sh -f
```

### Deploy to Multiple Projects

```bash
# Deploy FL app
./scripts/deploy-and-cleanup.sh -d web/shellcast-web-fl -p shellcast-fl

# Deploy NC app
./scripts/deploy-and-cleanup.sh -d web/shellcast-web-nc -p shellcast-nc

# Deploy SC app
./scripts/deploy-and-cleanup.sh -d web/shellcast-web-sc -p shellcast-sc
```

### Clean All Projects at Once

```bash
# Clean staging for all known ShellCast projects
./scripts/cleanup-staging-enhanced.sh -a -f
```

## Important Notes

1. **Staging Bucket Format:** Staging files are stored in buckets with the format `staging.PROJECT_NAME.appspot.com`

2. **No-Cache Deployment:** After cleaning staging files, you may need to use `--no-cache` for the next deployment to avoid issues with cached files.

3. **Project Names:** The scripts support these project names:

   - `ncsu-shellcast` (main project)
   - `shellcast-fl` (Florida)
   - `shellcast-nc` (North Carolina)
   - `shellcast-sc` (South Carolina)

4. **Safety:** The scripts include confirmation prompts by default. Use `-f` flag to skip confirmation for automated workflows.

## Troubleshooting

### "No project configured" Error

```bash
# Set your project
gcloud config set project YOUR_PROJECT_NAME

# Or specify project in command
./scripts/cleanup-staging-enhanced.sh -p YOUR_PROJECT_NAME
```

### "Not authenticated" Error

```bash
# Login to Google Cloud
gcloud auth login
```

### "Permission denied" Error

```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Staging Files Not Found

This is normal if:

- The project hasn't been deployed yet
- Staging files were already cleaned up
- You don't have access to the staging bucket

## Integration with CI/CD

For automated deployments, you can use the force flag:

```bash
# In your CI/CD pipeline
./scripts/deploy-and-cleanup.sh -d web/shellcast-web-fl -f
```

This will deploy and clean up staging files without requiring user interaction.
