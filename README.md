# FranchiseOps AI — Full Dashboard

A complete non-Streamlit dashboard with a responsive HTML/CSS/JavaScript frontend and separate Python analytics agents. Uses the requested palette: #FFFFFF, #102A43, #0878B8, #16B8F3, #CCEEFF, #2B2B2B, #52687A, #B2D4E5.

## Start locally

Requires Python 3.10 or newer. Open a terminal inside this folder:

```sh
python -m venv .venv
```

Windows:

```sh
.venv\Scripts\activate
```

macOS / Linux:

```sh
source .venv/bin/activate
```

Then:

```sh
python -m pip install -r requirements.txt
python server.py
```

Open **http://localhost:8000**. Included saved outputs are ready to browse immediately. No Node, API key, login, or Streamlit is required. Use **Run this agent** on individual agent pages or **Run all agents** on Overview. Runs happen in the backend and report completion or failure; required upstream dependencies run first. Rerun all after source data changes to refresh downstream results.

You can also run modules directly:

```sh
python pipeline.py all
python pipeline.py inventory
python pipeline.py operations
```

## Included modules

| Milestone | Module ID | Purpose |
|---|---|---|
| 1 | data | Source validation, cleaning and deduplication |
| 1 | benchmark | Outlet KPI comparison and ranking |
| 1 | score | Seven-driver performance score |
| 1 | performance | Outlet insights and recommended actions |
| 2 | forecast | Three-month lagged demand estimate |
| 2 | inventory | Stock monitoring and replenishment |
| 3 | staff | Staff health and retention |
| 3 | workforce | Attendance, productivity and scheduling |
| 3 | marketing | Spend efficiency and marketing agent |
| 3 | campaigns | Campaign ROI and effectiveness |
| 3 | operations | Recent operational risk and actions |
| 3 | health | Cross-functional outlet health |

Every view has region/outlet filtering, appropriate period filtering, charts, a searchable/sortable/paginated table, outlet detail inspection, and filtered CSV download. Full-period aggregates do not respond to the month filter; it is hidden on those pages and the period scope is labelled.

## Source data and branch reconciliation

The supplied 19 ZIPs were inventoried. `SOURCE_MANIFEST.json` records their hashes. The integrated non-UI Python modules from the m3-dashboard branch provide corrected common interfaces. Enhanced staff and marketing modules come from their dedicated m3 feature branches; operational risk uses the operational-insights branch. No former Streamlit app is included.

- Main source: 750 outlets, 40 months, 30,000 cleaned outlet-month records.
- Inventory workbook includes 120 duplicate test records; applicable loaders remove them.
- The 96-row, 8-outlet demonstration data was excluded to avoid mixing populations.
- Missing numeric values are imputed with column medians following the sales preparation notebook.
- Sales preparation reads `engine/data/raw/FranchiseOps_AI_Milestone2_Inventory_Dataset.xlsx`.
- Workforce/campaign analysis reads `engine/data/raw/FranchiseOps_AI_Milestone2_Milestone3_Combined_Dataset.xlsx`.
- Staff retains its branch's monthly and trend CSV outputs in `engine/staff_agent/`.
- Operational issue-label generation was repaired to report issue names, not boolean text.
- The supplied forecasting formula uses `shift(1).rolling(3)`. Although its original column is named `Demand_Forecast_Next_Month_Units`, it is a lagged historical estimate, not a true future-period prediction. The interface labels it accordingly; initial unavailable estimates remain null. Inventory uses the separate forecast values supplied in its workbook.
- Algorithms are deterministic, explainable rules and analytics. They do not call an LLM.

## Structure

- `dist/` — browser frontend and exported per-agent JSON results
- `engine/` — agent modules, original workbooks, processed CSVs and source tests
- `pipeline.py` — module registry, dependencies, execution and JSON export
- `server.py` — local HTTP server and asynchronous agent-run API
- `tests/` — dashboard integration checks

The run API is intentionally local, bound to 127.0.0.1 by default, rejects cross-origin requests, and runs only allowlisted agent IDs. For a public production deployment, put this service behind your deployment platform's access control and TLS; the bundled server is intended for local project demonstration.

## Hosted preview vs. full application

The hosted site serves saved results and all browsing/filtering/export interactions. It cannot execute Python. Run controls are disabled there and the interface explicitly says “Saved results · preview.” The downloaded local app runs all Python agents.

For a Python-capable host, install `requirements.txt`, set `HOST=0.0.0.0` and the host-provided `PORT`, and start `python server.py`. Add production access controls before exposing mutable agent endpoints. Static hosts can serve `dist/` but cannot run agents.

## Verification

```sh
python -m pip install pytest
python -m pytest tests engine/tests -q
```

The final verification suite contains 18 tests. Data integration checks verify outlet coverage, duplicates, output schemas, finite scores, source revenue totals and operational labels. Original module tests check forecasts, inventory decisions and Milestone 3 formulas.

The frontend passed JavaScript syntax checks and rendering-logic checks for all 13 views. A full browser visual check was not available in this environment.
