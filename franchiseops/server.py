"""Dependency-free WSGI API for the Milestones 1-3 dashboard."""
import csv
import io
import json
import sqlite3
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs

from .db import connect, rows
from .agents import analyze, run_agents
from .imports import SCHEMAS, import_csv

STATIC = Path(__file__).parent / "static"


def application(env, start_response):
    def respond(payload, status="200 OK", ctype="application/json", extra=()):
        data = payload if isinstance(payload, bytes) else json.dumps(payload, allow_nan=False).encode()
        headers = [
            ("Content-Type", ctype),
            ("Content-Length", str(len(data))),
            ("X-Content-Type-Options", "nosniff"),
            ("Cache-Control", "no-store"),
            ("X-Frame-Options", "DENY"),
            ("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"),
            *extra,
        ]
        start_response(status, headers)
        return [data]

    path = env.get("PATH_INFO", "/")
    method = env.get("REQUEST_METHOD", "GET")
    if path == "/healthz":
        return respond({"status": "ok", "scope": "Milestones 1-3"})
    if path in ("/", "/app.js", "/style.css"):
        if method != "GET":
            return respond({"error": "Method not allowed"}, "405 Method Not Allowed")
        name = "index.html" if path == "/" else path[1:]
        ctype = {"html": "text/html; charset=utf-8", "js": "text/javascript; charset=utf-8", "css": "text/css; charset=utf-8"}[name.split(".")[-1]]
        return respond((STATIC / name).read_bytes(), ctype=ctype)

    try:
        size = int(env.get("CONTENT_LENGTH") or 0)
        if size > 5_000_000:
            return respond({"error": "Maximum request size is 5 MB"}, "413 Payload Too Large")
        body = json.loads(env["wsgi.input"].read(size)) if size else {}
        if not isinstance(body, dict):
            raise ValueError("JSON body must be an object")
        if method not in ("GET", "POST"):
            return respond({"error": "Method not allowed"}, "405 Method Not Allowed")
        query = {key: value[0] for key, value in parse_qs(env.get("QUERY_STRING", "")).items()}
        db = connect()
        try:
            if path == "/api/dashboard" and method == "GET":
                start = query.get("start")
                end = query.get("end")
                if start:
                    date.fromisoformat(start)
                if end:
                    date.fromisoformat(end)
                if start and end and start > end:
                    raise ValueError("Start date must be before end date")
                data = analyze(db, start, end)
                allowed = {
                    row["outlet_id"]
                    for row in data["performance"]
                    if (not query.get("outlet") or str(row["outlet_id"]) == query["outlet"])
                    and (not query.get("region") or row["region"] == query["region"])
                }
                for key in ("performance", "inventory", "staff", "marketing", "insights", "outlet_summary"):
                    data[key] = [row for row in data[key] if row["outlet_id"] in allowed]
                data["outlets"] = rows(db, "SELECT * FROM outlets ORDER BY name")
                data["trend"] = rows(db, "SELECT outlet_id,date,revenue FROM sales WHERE date BETWEEN ? AND ? ORDER BY date", (data["start"], data["end"]))
                data["trend"] = [row for row in data["trend"] if row["outlet_id"] in allowed]
                data["runs"] = rows(db, "SELECT * FROM runs ORDER BY id DESC LIMIT 10")
                data["activity"] = rows(db, "SELECT * FROM activity ORDER BY id DESC LIMIT 20")
                data["schemas"] = {key: list(value) for key, value in SCHEMAS.items()}
                data["data_quality"] = [
                    {"dataset": table, "rows": db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]}
                    for table in SCHEMAS
                ]
                data["scope"] = {
                    "milestone_1": ["Sales & outlet data", "Outlet benchmarking", "Performance score", "Outlet Performance Agent", "Performance dashboard"],
                    "milestone_2": ["Inventory Agent", "Inventory forecasting", "Stock monitoring", "Replenishment recommendations", "Inventory dashboard"],
                    "milestone_3": ["Data preparation & validation", "Staff Agent + workforce analytics", "Marketing Agent + marketing effectiveness", "Operational insights", "Milestone 3 dashboard", "Integration & testing"],
                    "agents": 4,
                }
                return respond(data)

            if path == "/api/run" and method == "POST":
                return respond(run_agents(db))

            if path == "/api/import" and method == "POST":
                count = import_csv(db, str(body.get("dataset", "")), str(body.get("csv", "")))
                return respond({"rows": count})

            if path == "/api/export" and method == "GET":
                dataset = query.get("dataset", "sales")
                if dataset not in SCHEMAS:
                    raise ValueError("Unknown dataset")
                records = rows(db, f"SELECT * FROM {dataset}")
                fields = list(SCHEMAS[dataset])
                buffer = io.StringIO()
                writer = csv.writer(buffer)
                writer.writerow(fields)
                for row in records:
                    writer.writerow([
                        ("'" + str(row[field])) if isinstance(row[field], str) and row[field].startswith(("=", "+", "-", "@", "\t", "\r")) else row[field]
                        for field in fields
                    ])
                return respond(buffer.getvalue().encode(), ctype="text/csv; charset=utf-8", extra=[("Content-Disposition", f'attachment; filename="{dataset}.csv"')])

            return respond({"error": "Not found"}, "404 Not Found")
        finally:
            db.close()
    except (ValueError, KeyError, TypeError, sqlite3.IntegrityError) as error:
        return respond({"error": str(error)}, "400 Bad Request")
    except Exception:
        import traceback
        traceback.print_exc()
        return respond({"error": "Internal error; check the server log"}, "500 Internal Server Error")
