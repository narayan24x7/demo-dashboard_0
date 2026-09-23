# Deployment guide

## Local

```bash
python run.py
```

Open `http://127.0.0.1:8000`.

## Gunicorn

```bash
python -m pip install -r requirements-deploy.txt
python run.py --run-once
gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 90 wsgi:application
```

Use one worker for the supplied SQLite setup. Set `FRANCHISEOPS_DB` to an absolute writable path when persistent storage is needed.

## Docker

```bash
docker compose up --build -d
```

The container seeds demonstration data on first initialization and runs the Milestones 1–3 analytics pipeline before starting Gunicorn.

## Streamlit note

This ZIP is the dependency-free WSGI/browser build, not a Streamlit application. If your team branch uses Streamlit, reuse the same M1–M3 analytics functions and data contracts rather than adding later milestone modules.
