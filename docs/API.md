# API reference — Milestones 1–3

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Liveness plus scope marker |
| GET | `/api/dashboard` | M1–M3 analytics; optional `start`, `end`, `outlet`, `region` filters |
| POST | `/api/run` | Run the four analytics agents through M3 and generate operational insights |
| POST | `/api/import` | Validate and atomically upsert a supported CSV dataset |
| GET | `/api/export?dataset=sales` | Export a supported source dataset as CSV |

`/api/dashboard` returns these analytics collections: `performance`, `inventory`, `staff`, `marketing`, `insights`, and `outlet_summary`, plus trend data, source schemas, data-quality counts and run history.

Supported import/export datasets are `franchises`, `outlets`, `sales`, `inventory`, `movements`, `staff`, and `campaigns`.

Example:

```python
import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:8000/api/dashboard?outlet=1') as response:
    result = json.load(response)
    print(result['insights'])
```
