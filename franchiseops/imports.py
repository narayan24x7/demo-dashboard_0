"""Milestone 3 data preparation and validation contracts."""
import csv
import io
import math
from datetime import date
from .db import log

SCHEMAS = {
    "franchises": {"id": int, "name": str, "region": str, "owner": str},
    "outlets": {"id": int, "franchise_id": int, "name": str, "region": str, "status": str},
    "sales": {"outlet_id": int, "date": str, "revenue": float, "transactions": int, "cost": float},
    "inventory": {"id": int, "outlet_id": int, "product": str, "quantity": float, "reorder_level": float, "lead_days": int, "unit_cost": float, "expiry_date": str},
    "movements": {"inventory_id": int, "date": str, "used": float, "wasted": float},
    "staff": {"id": int, "outlet_id": int, "name": str, "role": str, "scheduled_hours": float, "worked_hours": float, "orders": int, "shift": str},
    "campaigns": {"id": int, "outlet_id": int, "name": str, "spend": float, "attributed_revenue": float, "gross_margin": float, "impressions": int, "clicks": int, "conversions": int, "status": str},
}
KEYS = {"sales": ["outlet_id", "date"], "movements": ["inventory_id", "date"]}


def import_csv(db, table, content):
    if table not in SCHEMAS:
        raise ValueError("Unknown dataset")
    reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
    schema = SCHEMAS[table]
    if set(reader.fieldnames or []) != set(schema):
        raise ValueError("CSV headers must match: " + ",".join(schema))
    records = []
    for index, row in enumerate(reader, 2):
        if index > 10001:
            raise ValueError("Maximum 10,000 rows per import")
        try:
            if None in row:
                raise ValueError("Too many columns")
            record = {key: kind(row[key].strip()) for key, kind in schema.items()}
            for key, value in record.items():
                if isinstance(value, (int, float)) and (not math.isfinite(value) or value < 0):
                    raise ValueError(f"{key} must be finite and non-negative")
                if isinstance(value, str) and (not value or len(value) > 1000):
                    raise ValueError(f"{key} is empty or too long")
                if key == "date" or key.endswith("_date"):
                    date.fromisoformat(value)
                if key == "id" or key.endswith("_id"):
                    if value < 1:
                        raise ValueError(f"{key} must be positive")
            if table == "campaigns" and not (record["conversions"] <= record["clicks"] <= record["impressions"]):
                raise ValueError("Require conversions <= clicks <= impressions")
            records.append(record)
        except (ValueError, TypeError, AttributeError) as error:
            raise ValueError(f"Row {index}: {error}") from error
    if not records:
        raise ValueError("CSV contains no data")
    keys = KEYS.get(table, ["id"])
    columns = list(schema)
    updates = [key for key in columns if key not in keys]
    query = (
        f"INSERT INTO {table} ({','.join(columns)}) VALUES({','.join('?' for _ in columns)}) "
        f"ON CONFLICT({','.join(keys)}) DO UPDATE SET " + ",".join(f"{key}=excluded.{key}" for key in updates)
    )
    with db:
        db.executemany(query, [[record[key] for key in columns] for record in records])
        log(db, "data.import", f"{table}: {len(records)} rows")
    return len(records)
