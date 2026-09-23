# Validation report — Milestone 3

Verification targets the exact Milestones 1–3 scope:

- performance, inventory, staff and marketing agent outputs;
- inventory forecasting and replenishment;
- workforce coverage and roster gaps;
- marketing ROAS and margin-adjusted ROI;
- operational insights sourced only from Performance, Inventory, Workforce and Marketing;
- absence of composite franchise scoring in the M3 summary;
- strict CSV validation, rollback and upsert behavior;
- dashboard outlet filters and supported data schemas;
- HTTP health, dashboard and analytics run routes;
- removed post-Milestone-3 application routes;
- HTML/JavaScript render smoke checks when Node.js is available.

Reproduce:

```bash
python -m unittest discover -s tests -v
python tests/http_smoke.py
node --check franchiseops/static/app.js
node tests/frontend-smoke.cjs
```

See `test-results.txt` for the captured Python unit-test output from this package.
