"""Explainable analytics through Milestone 3 only.

Milestone 1: Outlet Performance Agent
Milestone 2: Inventory Agent
Milestone 3: Staff Agent, Marketing Agent, Operational Insights
"""
from datetime import date, timedelta
from statistics import mean, pstdev
import json
import math

from .db import rows, now, log
from .operational_insights import generate_operational_insights, outlet_attention


def clamp(value):
    return round(max(0, min(100, value)), 1)


def safe(numerator, denominator):
    return numerator / denominator if denominator else 0


def performance(db, start, end):
    """Milestone 1 outlet performance, peer benchmarking and performance score."""
    span = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    previous = (date.fromisoformat(start) - timedelta(days=span)).isoformat()
    result = []
    for outlet in rows(db, "SELECT * FROM outlets"):
        current = rows(db, "SELECT * FROM sales WHERE outlet_id=? AND date BETWEEN ? AND ? ORDER BY date", (outlet["id"], start, end))
        prior = rows(db, "SELECT revenue FROM sales WHERE outlet_id=? AND date>=? AND date<?", (outlet["id"], previous, start))
        revenue = sum(row["revenue"] for row in current)
        cost = sum(row["cost"] for row in current)
        prior_revenue = sum(row["revenue"] for row in prior)
        result.append({
            "outlet_id": outlet["id"],
            "name": outlet["name"],
            "region": outlet["region"],
            "revenue": round(revenue, 2),
            "profit": round(revenue - cost, 2),
            "transactions": sum(row["transactions"] for row in current),
            "margin": round(safe(revenue - cost, revenue) * 100, 1),
            "growth": round((revenue / prior_revenue - 1) * 100, 1) if prior_revenue else None,
            "days": len(current),
            "coverage": round(len(current) / span * 100, 1),
        })

    for row in result:
        peers = [item for item in result if item["region"] == row["region"] and item["outlet_id"] != row["outlet_id"] and item["days"]]
        if not peers:
            peers = [item for item in result if item["outlet_id"] != row["outlet_id"] and item["days"]]
        peer_daily = mean(safe(item["revenue"], item["days"]) for item in peers) if peers else None
        row_daily = safe(row["revenue"], row["days"])
        row["peer_index"] = round(safe(row_daily, peer_daily) * 100, 1) if peer_daily else None
        row["score"] = (
            clamp(
                0.4 * min(100, row["peer_index"] if row["peer_index"] is not None else 100)
                + 0.3 * min(100, row["margin"] / 30 * 100)
                + 0.3 * min(100, 70 + (row["growth"] or 0))
            )
            if row["days"]
            else None
        )
        row["health"] = "No data" if row["score"] is None else "Healthy" if row["score"] >= 80 else "Watch" if row["score"] >= 60 else "At risk"
    return result


def inventory(db, as_of):
    """Milestone 2 inventory monitoring, forecast and replenishment recommendations."""
    result = []
    for item in rows(db, "SELECT i.*,o.name outlet FROM inventory i JOIN outlets o ON o.id=i.outlet_id"):
        from_date = (date.fromisoformat(as_of) - timedelta(days=27)).isoformat()
        history = rows(db, "SELECT used,wasted FROM movements WHERE inventory_id=? AND date<=? AND date>=? ORDER BY date", (item["id"], as_of, from_date))
        values = [row["used"] for row in history]
        demand = mean(values) if values else None
        deviation = pstdev(values) if len(values) > 1 else 0
        safety = 1.65 * deviation * math.sqrt(item["lead_days"])
        target = demand * (item["lead_days"] + 7) + safety if demand is not None else item["reorder_level"]
        trigger = max(item["reorder_level"], demand * item["lead_days"] + safety) if demand is not None else item["reorder_level"]
        shortage = item["quantity"] < trigger
        expiry_days = (date.fromisoformat(item["expiry_date"]) - date.fromisoformat(as_of)).days
        result.append(dict(
            item,
            daily_demand=round(demand, 2) if demand is not None else None,
            forecast_7d=round(demand * 7, 1) if demand is not None else None,
            safety_stock=round(safety, 1),
            reorder_point=round(trigger, 1),
            days_cover=round(safe(item["quantity"], demand), 1) if demand else None,
            replenish=max(0, math.ceil(target - item["quantity"])) if shortage else 0,
            shortage=shortage,
            waste_pct=round(safe(sum(row["wasted"] for row in history), sum(row["used"] + row["wasted"] for row in history)) * 100, 1),
            expiry_days=expiry_days,
            history_days=len(values),
        ))
    return result


def staff(db):
    """Milestone 3 enhanced staff/workforce analytics."""
    result = []
    for row in rows(db, "SELECT s.*,o.name outlet FROM staff s JOIN outlets o ON o.id=s.outlet_id"):
        coverage = min(100, safe(row["worked_hours"], row["scheduled_hours"]) * 100)
        result.append(dict(
            row,
            attendance=round(coverage, 1),
            coverage_pct=round(coverage, 1),
            orders_per_hour=round(safe(row["orders"], row["worked_hours"]), 2),
            hours_gap=round(max(0, row["scheduled_hours"] - row["worked_hours"]), 1),
            status="Covered" if coverage >= 95 else "Watch" if coverage >= 85 else "Under-covered",
        ))
    return result


def marketing(db):
    """Milestone 3 enhanced marketing effectiveness analytics."""
    result = []
    for row in rows(db, "SELECT c.*,o.name outlet FROM campaigns c JOIN outlets o ON o.id=c.outlet_id"):
        contribution = row["attributed_revenue"] * row["gross_margin"] - row["spend"]
        roi = round(contribution / row["spend"] * 100, 1) if row["spend"] else None
        result.append(dict(
            row,
            roas=round(safe(row["attributed_revenue"], row["spend"]), 2) if row["spend"] else None,
            roi=roi,
            ctr=round(safe(row["clicks"], row["impressions"]) * 100, 2),
            conversion=round(safe(row["conversions"], row["clicks"]) * 100, 2),
            cost_per_conversion=round(safe(row["spend"], row["conversions"]), 2) if row["conversions"] else None,
            contribution=round(contribution, 2),
            effectiveness="No spend" if not row["spend"] else "Strong" if roi is not None and roi >= 20 else "Watch" if roi is not None and roi >= 0 else "Weak",
        ))
    return result


def analyze(db, start=None, end=None):
    end = end or date.today().isoformat()
    start = start or (date.fromisoformat(end) - timedelta(days=29)).isoformat()
    performance_rows = performance(db, start, end)
    inventory_rows = inventory(db, date.today().isoformat())
    staff_rows = staff(db)
    marketing_rows = marketing(db)
    insights = generate_operational_insights(performance_rows, inventory_rows, staff_rows, marketing_rows)
    return {
        "performance": performance_rows,
        "inventory": inventory_rows,
        "staff": staff_rows,
        "marketing": marketing_rows,
        "insights": insights,
        "outlet_summary": outlet_attention(performance_rows, insights),
        "start": start,
        "end": end,
        "snapshot_date": date.today().isoformat(),
    }


def run_agents(db):
    """Run all analytics agents available through Milestone 3 and log the integration result."""
    timestamp = now()
    cursor = db.execute("INSERT INTO runs(started_at,status) VALUES(?,?)", (timestamp, "running"))
    run_id = cursor.lastrowid
    data = analyze(db)
    summary = {
        "agents": 4,
        "agents_run": ["Performance", "Inventory", "Staff", "Marketing"],
        "operational_insights": len(data["insights"]),
        "outlets": len(data["performance"]),
        "scope": "Milestones 1-3",
        "engine": "rules-and-statistics",
    }
    db.execute("UPDATE runs SET status=?,finished_at=?,summary=? WHERE id=?", ("completed", now(), json.dumps(summary), run_id))
    log(db, "milestone3.run", json.dumps(summary))
    db.commit()
    return {"id": run_id, **summary}
