# Getting started with ShellCast

ShellCast is a Python Flask web application that helps shellfish growers make harvesting decisions based on predicted rainfall. See [README.md](README.md) for project overview, architecture, and documentation index.

Choose the path below that matches what you are doing:

| Goal | Section |
|------|---------|
| Change code and open a pull request | [Contributors: fork, remotes, and pre-commit](#contributors-fork-remotes-and-pre-commit) |
| Run analysis or the web app locally (read-only or experiments) | [Run locally: clone and setup](#run-locally-clone-and-setup) |

The project lives on [GitHub](https://github.com/Biosystems-Analytics-Lab/shellcast). NCSU campus GitHub (`github.ncsu.edu`) has been retired.

New to Git? See GitHub’s [Hello World guide](https://docs.github.com/en/get-started/start-your-journey/hello-world).

## Contributors: fork, remotes, and pre-commit

Use this path if you will **edit code** and submit changes for review (students, collaborators without direct push access, or anyone working via pull requests).

### 1. Fork and clone your fork

1. Install [Git](https://git-scm.com/downloads).
2. On GitHub, [fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) [Biosystems-Analytics-Lab/shellcast](https://github.com/Biosystems-Analytics-Lab/shellcast) to your account.
3. Clone **your fork** (replace `YOUR_USERNAME`):

```bash
git clone https://github.com/YOUR_USERNAME/shellcast.git
cd shellcast
```

### 2. Add the upstream remote

The lab repo is **upstream**. Your fork is **origin**. Add upstream once so you can pull latest team changes:

```bash
git remote add upstream https://github.com/Biosystems-Analytics-Lab/shellcast.git
git fetch upstream
```

Before starting new work, sync from upstream (example using `main`):

```bash
git checkout main
git pull upstream main
git push origin main
```

### 3. Install pre-commit (required for contributors)

This project runs automatic checks on every commit. One-time setup from the repo root:

```bash
pip install pre-commit
pre-commit install
```

Or run `./setup-precommit.sh` if your team uses that script. Details: [pre-commit.com](https://pre-commit.com/#introduction).

### 4. Save and share changes

```bash
git status
git add path/to/files/you/changed
git commit -m "Short description of what you changed"
git push origin your-branch-name
```

Open a **pull request** on GitHub from your fork into `Biosystems-Analytics-Lab/shellcast`. Ask a project lead if you are unsure which branch to target.

To run checks before committing:

```bash
pre-commit run --all-files
```

### Where to edit code

| If you are changing… | Work in this folder | Read |
|---------------------|---------------------|------|
| Daily forecast math, database upload, morning emails | `analysis/` (especially `analysis/shellcast-analysis/`) | [docs/analysis/README.md](docs/analysis/README.md) |
| The public website (map, sign-in, preferences, SMS) | `web/` (`shellcast-web-nc`, `shellcast-web-sc`, or `shellcast-web-fl`) | [docs/web/README.md](docs/web/README.md) |

Florida-only data prep: `data_prep/`. Database scripts: `analysis/shellcast-analysis/db_scripts/` ([docs/DATABASE.md](docs/DATABASE.md)).

---

## Run locally: clone and setup

Use this path if you only need a **working copy on your machine** (investigate data, run a state app, try analysis) and are **not** setting up the fork → pull request workflow. You do not need pre-commit unless you also plan to contribute code.

### 1. Clone the lab repository

```bash
git clone https://github.com/Biosystems-Analytics-Lab/shellcast.git
cd shellcast
```

Use a relatively short folder path; very long paths can break Cloud SQL Unix socket paths on the web apps.

### 2. Run analysis locally

Full walkthrough: [docs/analysis/01-GETTING_STARTED.md](docs/analysis/01-GETTING_STARTED.md).

Summary:

```bash
cd analysis/shellcast-analysis
cp analysis_settings.template.ini analysis_settings.ini
cp analysis_paths.template.sh analysis_paths.sh
# Edit both files for your machine (see docs/analysis/02-CONFIGURATION.md)

cd ..
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

In a **separate terminal**, start the Cloud SQL proxy (credentials from a project administrator):

```bash
./cloud-sql-proxy --port 3306 your-project:region:instance-name
```

Smoke test one state (with proxy running and venv active):

```bash
cd analysis/shellcast-analysis
source analysis_paths.sh
source "$VENV_ACTIVATE_PATH"
python nc_main.py
```

Use `sc_main.py` or `fl_main.py` for other states when inputs are ready. Dev machines often set `SAVE_TO_DB = false` in `analysis_settings.ini` until you intend to write to the database.

### 3. Run a web app locally

Full walkthrough: [docs/web/01-GETTING_STARTED.md](docs/web/01-GETTING_STARTED.md).

Summary:

```bash
cd web
python3 -m venv venv && source venv/bin/activate
pip install -r shellcast-web-nc/requirements.txt

# Cloud SQL proxy + OpenLayers (once per machine)
sh ../cloud-sql-proxy-setup.sh
cp ../my-cloud-sql-proxy.template.sh ../my-cloud-sql-proxy.sh
# Edit instance_connection_name in my-cloud-sql-proxy.sh, then:
chmod +x ../my-cloud-sql-proxy.sh
cd shellcast-web-nc && npm install && npm run build

cd ../..   # repo root
./my-cloud-sql-proxy.sh web    # leave running (Terminal 1)

cd web/shellcast-web-nc
cp env.template .env           # edit with secrets from a project administrator
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/firebase-admin-sdk-credentials.json"
python main.py                 # Terminal 2
```

For deployment, create **`app.yaml`** from `app.yaml.template` (gitignored) — see [docs/web/04-DEPLOY_GAE.md](docs/web/04-DEPLOY_GAE.md).

Open the URL in the console (NC often uses port **3361** — check `PORT` in `.env`). Repeat under `shellcast-web-sc` or `shellcast-web-fl` for other states.

---

## Documentation (docs directory)

- [docs/analysis/README.md](docs/analysis/README.md) – analysis docs (`01-` … `09-`, read in order)
- [docs/analysis/09-ANALYSIS.md](docs/analysis/09-ANALYSIS.md) – PQPF/XMRG specs and compile notes (legacy detail)
- [docs/web/README.md](docs/web/README.md) – web apps (`01-` … `07-`, read in order)
- [docs/DATABASE.md](docs/DATABASE.md) – database access and management
- [docs/CITATION.md](docs/CITATION.md) – how to cite and give attribution
- [LICENSE.md](LICENSE.md) – ShellCast license (CC BY 4.0)

## Contact

If you have any questions, feedback, or suggestions please submit [GitHub issues](https://github.com/Biosystems-Analytics-Lab/shellcast/issues). You can also reach out to Natalie Nelson (nnelson4 at ncsu dot edu).
