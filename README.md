# FranchiseOps AI — Milestone 3 Build

This project is intentionally scoped to **Milestones 1, 2 and 3 only** for the Infosys Springboard project **Agentic AI for Franchise Management System with Performance Monitoring Assistance**.

The application keeps the earlier milestone dependencies needed by Milestone 3 and implements the current Milestone 3 tasks exactly: **Data Preparation & Validation, Staff Agent + Workforce Analytics, Marketing Agent + Marketing Effectiveness, Operational Insights, Milestone 3 Dashboard, and Integration & Testing**.

## Run locally

Python 3.10+ is enough for the default local application.

```bash
python run.py
```

Open **http://127.0.0.1:8000**. No login is required. On first launch the app creates synthetic demonstration data for six Gujarat outlets.

## Exact milestone scope

| Milestone | Included functionality | Main implementation |
|---|---|---|
| Milestone 1 — Outlet Performance Intelligence | Sales/outlet data, outlet benchmarking, performance score, Outlet Performance Agent, performance dashboard | `franchiseops/agents.py::performance()` |
| Milestone 2 — Inventory Intelligence & Optimization | Inventory Agent, 7-day demand forecast, stock monitoring, safety stock, reorder point, replenishment recommendation, waste/expiry metrics | `franchiseops/agents.py::inventory()` |
| Milestone 3 — Workforce & Marketing Intelligence | Staff Agent, workforce analytics, Marketing Agent, marketing effectiveness, operational insights, integrated M3 dashboard, data validation, integration/testing | `agents.py`, `operational_insights.py`, `imports.py`, browser dashboard, `tests/` |

### Milestone 3 team-task mapping

| Team member | Milestone 3 task | Where it appears in this build |
|---|---|---|
| Bharath | Data Preparation & Validation | Strict CSV schemas, type/date/foreign-key checks, atomic upserts, data coverage page |
| Nandini | Staff Agent + Workforce Analytics | Coverage %, attendance, roster gaps, orders/hour, workforce status |
| Nirma | Operational Insights | Evidence-based recommendations combining M1–M3 module outputs |
| Rajashri | Marketing Agent + Marketing Effectiveness | CTR, conversion rate, ROAS, margin-adjusted ROI, cost/conversion, effectiveness status |
| Narayandas | Milestone 3 Dashboard | Integrated browser dashboard with filters, KPIs, tables, trends and exports |
| Nishanth | Integration & Testing | Unified API pipeline, run history, unit tests, HTTP smoke test, JS smoke/syntax checks |

## Analytics agents through Milestone 3

There are **four analytics agents** in this build:

1. **Performance Agent** — Milestone 1
2. **Inventory Agent** — Milestone 2
3. **Staff Agent** — Milestone 3
4. **Marketing Agent** — Milestone 3

`operational_insights.py` is the Milestone 3 recommendation layer. It consumes the four agent outputs and generates traceable recommendations by source, severity, evidence and next action. It is not counted as an additional autonomous agent.

The **Run M3 analytics** button executes the four agents, generates operational insights, and stores a small integration run summary.

## Dashboard pages

- **Milestone 3 overview** — revenue, inventory reorder needs, workforce coverage, marketing ROI, outlet attention and current recommendations.
- **Outlet Performance · M1** — revenue trend, benchmark, peer index, performance score and health category.
- **Inventory Intelligence · M2** — stock level, 7-day demand, days cover, reorder point, suggested replenishment, waste and expiry.
- **Workforce Analytics · M3** — staff coverage, attendance, roster gap and orders/hour.
- **Marketing Effectiveness · M3** — spend, attributed revenue, CTR, conversion, ROAS, contribution, ROI and cost/conversion.
- **Operational Insights · M3** — source-specific issues and recommendations from Performance, Inventory, Workforce and Marketing.
- **Data Preparation & Validation · M3** — CSV contracts, import/export, joins and source table coverage.
- **Integration & Testing · M3** — end-to-end flow and recent analytics runs.

## Data contracts

Only datasets required through Milestone 3 are accepted:

- `franchises`
- `outlets`
- `sales`
- `inventory`
- `movements`
- `staff`
- `campaigns`

Join rules:

- `outlet_id` joins sales, inventory, staff and campaigns to outlets.
- `inventory_id` joins inventory movements to inventory items.
- CSV imports validate required headers, numeric values, dates, positive IDs, campaign funnel consistency and database foreign keys.
- Imports are atomic: a bad row rolls back the entire upload.

## Operational insight rules

The insight layer does not create a new composite franchise score. It uses direct evidence such as:

- low or missing outlet performance data;
- stock below reorder point, expiry risk or elevated waste;
- low workforce coverage or uncovered roster hours;
- negative campaign contribution ROI or low CTR.

Every generated insight includes its outlet, source module, severity, evidence and recommendation so the mentor can trace how the result was produced.

## Tests

Run:

```bash
python -m unittest discover -s tests -v
python tests/http_smoke.py
```

Optional JavaScript checks if Node.js is installed:

```bash
node --check franchiseops/static/app.js
node tests/frontend-smoke.cjs
```

The test suite verifies the four-agent scope, workforce metrics, marketing effectiveness, inventory forecasting, operational insights, CSV validation, filters, imports/exports and the absence of post-Milestone-3 application routes.

## Project structure

```text
FranchiseOps-AI/
  run.py
  wsgi.py
  franchiseops/
    agents.py                  # M1 Performance, M2 Inventory, M3 Staff + Marketing agents
    operational_insights.py    # M3 operational recommendation layer
    imports.py                 # M3 data preparation and validation
    schema.sql                 # Data model required through M3
    seed.py                    # Synthetic demo data
    server.py                  # Dashboard/API integration
    static/
      index.html
      app.js
      style.css
  data/samples/                # CSV examples for supported M1–M3 datasets
  tests/                       # Integration and validation tests
  docs/                        # API, architecture, deployment and validation notes
```

## Scope boundary

This ZIP intentionally stops at Milestone 3. It does not expose unrelated later-stage modules in the dashboard, API, import schemas or agent pipeline. The code is deterministic decision support: it does not automatically change staffing, purchase inventory or spend marketing budget.
