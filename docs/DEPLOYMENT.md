# Deployment guide

Local execution is verified. Docker and remote infrastructure have not been exercised in this environment; these files are deployment starting points, not evidence of a live deployment.

## Small Linux installation

Use Python 3.10+ in a virtual environment. Set an absolute writable `FRANCHISEOPS_DB` if you want to override the local database path. Initialize the database before starting WSGI:

```bash
python -m pip install -r requirements-deploy.txt
python run.py --run-once
# For no demo data on first initialization: python run.py --empty --run-once
gunicorn --bind 127.0.0.1:8000 --workers 1 --threads 4 --timeout 90 wsgi:application
```

The default local launcher uses Python's development WSGI server. Use the supplied WSGI entry point behind your HTTPS reverse proxy for deployment. Keep one Gunicorn worker for a simple SQLite deployment. Run as an unprivileged OS account, restrict database permissions, and manage restarts/logs with your platform's service manager.

The optional LLM timeout is 45 seconds; the WSGI timeout is set higher. Rate limit expensive public routes at the reverse proxy for internet exposure. `/healthz` is liveness only, not a full database/readiness test.

## Docker

```bash
docker compose up --build -d
```

The host port binds to loopback. Docker creates a named data volume. The first startup seeds synthetic data and runs agents. For a clean production dataset change initialization to `python run.py --empty --run-once`, initialize/import your franchise data and retain the volume. Never run `docker compose down -v` on a volume containing needed data.

## Backup and restore

Use SQLite's backup API while the service is running; do not copy only the main file while WAL writes are in progress:

```python
import sqlite3
with sqlite3.connect('data/franchiseops.db') as source:
    with sqlite3.connect('franchiseops-backup.db') as target:
        source.backup(target)
```

To restore, stop web and worker processes, preserve the existing database and WAL files, and point `FRANCHISEOPS_DB` to your verified backup. Test a restore before relying on backups.

## Before real operational use

Configure HTTPS, a durable volume, backups, monitoring and upstream access restrictions if the data must be private. Replace synthetic data and validate metric assumptions with the operations team. Add per-franchise authorization before sharing independent organizations' data. Move to a managed SQL database for scale. Validate SMTP/SMS/push provider integration in a test account before enabling dispatch. No cloud resources have been provisioned as part of this deliverable.

## Render live demo

Upload the contents of this project folder to a GitHub repository, then create a Render Python Web Service:

- Build command: `pip install -r requirements-deploy.txt`
- Start command: `python run.py --run-once && gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 90 wsgi:application`
- Health check: `/healthz`

The dashboard opens directly from the generated public URL. No password environment variable is needed. On Render Free, local SQLite changes disappear on sleep, restart or redeploy. Use synthetic data for the public demo. Paid persistent disk: mount `/var/data` and set `FRANCHISEOPS_DB=/var/data/franchiseops.db`.
