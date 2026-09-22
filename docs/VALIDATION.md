# Validation report

## Passed

- 25 automated Python tests using temporary SQLite databases. Exact output is in `test-results.txt`.
- All eight dataset types export and reimport correctly.
- Invalid data and missing foreign keys roll back the entire CSV import.
- Critical audit overrides, missing data behavior, forecast quantities, marketing ROI, escalation and alert identity tested.
- Authentication, viewer restrictions, logout, login throttling, closure evidence and spreadsheet formula escaping tested.
- Optional LLM success parsing and failure fallback tested with mocked network responses. No model was actually loaded.
- Node syntax check and dependency-free smoke rendering of all nine dashboard/workflow pages; HTML escaping checked. This uses a minimal DOM stand-in, not a browser.
- Real local HTTP smoke test launches an isolated server, logs in, requests dashboards and filtered data, runs agents, generates the offline briefing and requests HTML/CSS/JavaScript.

## Not verified in this environment

- Browser visual appearance, responsive layout, interactive DOM events and downloads: Chromium was unavailable, and its download timed out under network restrictions. No screenshot or browser-pass claim is supplied.
- Docker build, Gunicorn launch, cloud deployment, multiuser load, disaster recovery and live external notification delivery.
- Real Ollama inference or performance on your hardware.

## Reproduce

```bash
python -m unittest discover -s tests -v
python tests/http_smoke.py
node --check franchiseops/static/app.js
node tests/frontend-smoke.cjs
```

Node is optional and only needed for the JavaScript smoke checks; it is not needed to run the application. Review the actual browser at desktop and phone sizes before presenting the project.
