# API reference

All requests and responses use JSON unless noted. Authenticate with `Authorization: Bearer <token>`. Viewer accounts can read and export; mutations require an administrator. Same-origin frontend, no wildcard CORS, CSP, frame denial and no-store response headers are used.

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Unauthenticated process liveness |
| POST | `/api/login` | `{username,password}` → `{token,role,username,demo}` |
| POST | `/api/logout` | Invalidate token |
| GET | `/api/dashboard` | Analytics, actions, runs, schemas; query `start`, `end`, `outlet`, `region` |
| POST | `/api/run` | Run all agents, persist findings, queue notifications |
| POST | `/api/brief` | Network-wide default-period briefing; optional local LLM |
| POST | `/api/import` | `{dataset,csv}` → count; atomic add/update |
| GET | `/api/export?dataset=sales` | Entire source dataset as CSV; filters do not apply |
| PATCH | `/api/actions` | `{id,status,owner,due_date,notes}`; statuses open/in_progress/resolved |

Invalid inputs return 400, missing sessions 401, unauthorized role 403, unknown endpoints 404, oversized bodies 413, repeated login failures 429. Maximum body size: 5 MB. Requests do not dispatch external notifications.

## Example

```python
import json, urllib.request
base = 'http://127.0.0.1:8000'
request = urllib.request.Request(base+'/api/login',
    json.dumps({'username':'admin','password':'demo-change-me'}).encode(),
    {'Content-Type':'application/json'})
with urllib.request.urlopen(request) as r:
    token = json.load(r)['token']
request = urllib.request.Request(base+'/api/dashboard?outlet=1',
    headers={'Authorization':'Bearer '+token})
with urllib.request.urlopen(request) as r:
    print(json.load(r)['intelligence'])
```
