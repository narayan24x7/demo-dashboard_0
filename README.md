# FranchiseOps AI

A runnable franchise operations project covering all four milestones in the supplied **Agentic Franchise Operations Intelligence Platform** specification. Includes a Python backend, SQLite database, responsive browser dashboard, five specialist analytics agents, a franchise intelligence engine, action workflows, data imports and reporting.

**Run locally with Python 3.10 or newer. No npm, paid API key or pip packages are required for the default application.**

## Quick start — Windows

1. Extract this ZIP.
2. Open a terminal inside the `FranchiseOps-AI` folder.
3. Run:

```powershell
python run.py
```

4. Open **http://127.0.0.1:8000**.
5. The dashboard opens immediately. No account or password is needed.

You can also double-click `start.bat`. On macOS/Linux, use `python3 run.py` or `./start.sh`. Keep the terminal open while using the app. Press Ctrl+C to stop.

The first run generates synthetic data for six Gujarat outlets: 90 days of sales, 24 stock items, 35 days of inventory movements, 30 staff records, 12 campaigns and 18 audit checks. Dates are generated relative to the day you first launch. Your database persists in `data/franchiseops.db`; later starts preserve your edits. This is demonstration data, not a real company dataset.

## What is included

| Milestone | Implemented capabilities | Main code |
|---|---|---|
| 1: Outlet performance | Sales monitoring, equal-period trends, regional/network peer benchmarking, health scores, performance dashboard | `agents.py`: `performance()` |
| 2: Inventory | Stock monitoring, trailing-demand forecast, safety stock, replenishment quantity, expiry and waste alerts | `agents.py`: `inventory()` |
| 3: Workforce & marketing | Attendance, shift roster, uncovered hours, orders/hour, campaign CTR, conversion, ROAS, margin-adjusted ROI | `agents.py`: `staff()`, `marketing()` |
| 4: Audit & intelligence | Latest compliance checks, critical findings, weighted franchise health, risk bands, opportunities, executive dashboard, orchestrated findings | `agents.py`: `audit()`, `analyze()`, `run_agents()` |
| Shared workflow | In-app alerts, assignment, deadlines, escalation, closure evidence, activity log, external delivery adapters | `server.py`, `notifications.py` |
| Data & deployment | Validated transactional CSV upserts, exports, demo data, tests, Docker/WSGI configuration, scheduled worker | `imports.py`, `tests/`, `Dockerfile`, `worker.py` |

There are six domain dashboards plus Action center, Data & reports and Methodology. Sales dates, outlet and region filters are supported. The browser refreshes analytics every 60 seconds except while you are editing actions or importing data. New source records must first reach the database through imports; there is no live POS connector.

## How the agents work

Each specialist observes its database records, derives metrics, detects issues and proposes actions. `run_agents()` executes the five specialists and intelligence aggregation, stores deduplicated findings, queues notifications and escalates overdue work. The **Run agents** button and background worker share this pipeline. Every purchase, staffing change and marketing budget decision remains a human action.

The default engine uses deterministic rules and statistical forecasts, **not a trained ML model or autonomous LLM planner**. Numerical outputs remain inspectable in the Methodology page. Optional Ollama narration can turn the evidence into a management briefing; it cannot change records or execute recommendations.

### Optional local LLM briefing

Install Ollama separately and download a model suitable for your computer. Set its installed model name before starting:

```powershell
$env:OLLAMA_MODEL="your-installed-model-name"
python run.py
```

Use **Generate briefing** on the Executive page. Without a model, an evidence-based deterministic summary works immediately. The briefing is network-wide and uses the default last-30-days period; dashboard filters do not apply. Model errors return a clearly labeled deterministic fallback. No model weights are included, and live model inference was not validated in this build.

The adapter uses Ollama's documented [`/api/generate` API](https://docs.ollama.com/api/generate), with streaming disabled. `OLLAMA_URL` defaults to `http://127.0.0.1:11434`. Only configure servers you trust: summarized operating evidence is sent to that endpoint. Model output is rendered as plain text and should be reviewed against the metrics.

## Import your team's data

Go to **Data & reports**, choose a dataset, and export it to see the exact column contract. Replace the example values with your data, keep the headers and upload the CSV. Sample CSVs are also in `data/samples/`.

- Import order into an empty database: franchises → outlets → sales/inventory/staff/campaigns/audits → movements.
- `outlet_id` joins sales, inventory, staff, campaigns and audits to outlets. `inventory_id` joins movements to inventory.
- IDs must be positive; foreign keys must exist. Never repurpose an existing ID for an unrelated entity.
- Sales upsert on `(outlet_id,date)`; movements upsert on `(inventory_id,date)`; the other datasets upsert on `id`.
- Invalid files roll back completely. Dates use `YYYY-MM-DD`. Numerics must be finite and non-negative; further database constraints are enforced.
- Up to 10,000 records per import; maximum JSON request 5 MB. Imports update/add records and do not delete rows absent from a file.
- Run the agents after import to update stored alerts. Dashboard analytics recalculate on load.
- The header **Export view** button downloads the current filtered analytics/action report. Data & reports CSV exports include the whole source dataset, independent of dashboard filters. Formula-like text is escaped for spreadsheet safety; review that escape before importing it again.

For a clean database, point `FRANCHISEOPS_DB` to a new path and run `python run.py --empty`. Do not delete a database containing work you need. The app does not add demo outlets if any outlet already exists.

## Action plans and notifications

Open **Action center**, assign an owner, choose a deadline, update progress and save. Mark an action resolved only after adding evidence in Notes. An unresolved action whose due date has passed becomes critical on the next run.

Alert identity is stable by outlet/entity/issue, preventing repeated rows every run. Resolved actions stay resolved until a manager reopens them. Current findings remain visible in analytics even if someone closes their action; closing an action does not repair source records. Findings that disappear are not automatically closed: managers verify completion.

In-app notifications are available immediately. Email, SMS and mobile notifications are queued, but **no external messages are sent by starting the app, importing data or clicking Run agents**.

Configure SMTP or HTTPS webhook settings shown in `.env.example`, then explicitly opt in:

```bash
python run.py --run-once --dispatch
```

SMTP uses STARTTLS. SMS and mobile channels are generic authenticated webhook adapters: connect your own service that actually delivers SMS or mobile push. No native mobile application, phone-number directory or push subscription manager is bundled. The configured target is a central operations recipient; per-outlet routing is not implemented. Delivery retries up to three attempts; provider credentials and live delivery need validation in your environment. Webhooks include idempotency keys; SMTP cannot guarantee exactly-once delivery after a crash.

## Continuous agent monitoring

In another terminal, after initializing the app:

```bash
python worker.py --interval 300
```

This runs agents every five minutes. Add `--dispatch` only when you want actual external delivery. Run only one dispatcher instance to avoid concurrent deliveries. Alternatively schedule `python run.py --run-once` with Windows Task Scheduler or cron. This worker is provided as code, not installed as a service on your computer.

## Open access

The dashboard and API have no login or authorization. Anyone who can reach the deployed link can see reports and staff records, download data, import CSVs, run agents, and change actions. For a public portfolio demo, use synthetic data only. If you need private business data, configure access restrictions outside this app before sharing its link.

The `.env.example` file documents optional integrations and paths. Python does not load that file automatically.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests cover score and forecast calculations, critical audit overrides, ROI, missing data, duplicate prevention, escalation, CSV transactions, open dashboard access, action evidence and export safety. See `docs/VALIDATION.md` for the actual verification results and limits.

## Project structure

```text
FranchiseOps-AI/
  run.py                   Local launcher and one-shot agents
  worker.py                Scheduled agent and notification worker
  wsgi.py                  WSGI deployment entry point
  franchiseops/
    schema.sql             Database schema with foreign keys and checks
    db.py                  Persistence and activity log
    seed.py                Synthetic demonstration records
    agents.py              Five agents plus franchise intelligence
    imports.py             CSV contracts and atomic upserts
    notifications.py       Opt-in email / SMS / mobile adapters
    briefing.py            Optional Ollama narrative and offline fallback
    server.py              Open API, reports and static delivery
    static/                HTML, CSS and JavaScript dashboard
  data/samples/            Example CSVs for all data contracts
  tests/                   Standard-library automated tests
  docs/                    Architecture, API, deployment and verification
```

## Important scope boundaries

This is a complete runnable educational implementation of the specified modules, not a certified enterprise production system. Docker/WSGI deployment files are included, but no public deployment has been performed. Production adoption needs HTTPS, durable backups, access controls outside this app if data must be private, operational monitoring, load testing and real provider validation. SQLite and one web worker suit a small installation; distributed deployments need a server database.

Inventory forecasts assume recorded usage is representative and ignore seasonality, holidays, promotions and censored demand. Missing movement days are not imputed. Roster and campaign records are snapshots, not a historical scheduling or campaign attribution system. The engine identifies risk heuristically, not with a calibrated predictive model. Sample data is intentionally small.

The supplied PDF's architecture image is labeled **EventOps** and references unrelated event modules. This project follows the **FranchiseOps written requirements, franchise workflow and franchise database schema** instead. Relationships to staff, campaigns, audits and inventory are implemented as one-to-many so each outlet can have multiple records.
