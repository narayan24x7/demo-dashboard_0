# API reference

All API routes are public and require no credentials or tokens. Anyone who can reach the server can read, export, import and change data. The same-origin frontend uses a content security policy, frame denial and no-store response headers; these do not restrict access.

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Process liveness |
| GET | `/api/dashboard` | Analytics, actions, runs, schemas; query `start`, `end`, `outlet`, `region` |
| POST | `/api/run` | Run all agents, persist findings, queue notifications |
| POST | `/api/brief` | Network-wide default-period briefing; optional local LLM |
| POST | `/api/import` | `{dataset,csv}` → count; atomic add/update |
| GET | `/api/export?dataset=sales` | Entire source dataset as CSV; filters do not apply |
| PATCH | `/api/actions` | `{id,status,owner,due_date,notes}`; statuses open/in_progress/resolved |

Invalid inputs return 400, unknown endpoints 404, and oversized bodies 413. Maximum JSON body size is 5 MB. Requests do not dispatch external notifications.

## Example

```python
import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:8000/api/dashboard?outlet=1') as response:
    print(json.load(response)['intelligence'])
```
