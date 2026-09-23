"""Milestone 3 operational insights built from Milestones 1-3 analytics only."""

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def generate_operational_insights(performance, inventory, staff, marketing):
    """Return explainable recommendations from the four analytics modules available through Milestone 3."""
    insights = []

    def add(outlet_id, outlet, source, key, severity, title, evidence, recommendation):
        insights.append({
            "outlet_id": outlet_id,
            "outlet": outlet,
            "source": source,
            "key": key,
            "severity": severity,
            "title": title,
            "evidence": evidence,
            "recommendation": recommendation,
        })

    for row in performance:
        if not row["days"]:
            add(row["outlet_id"], row["name"], "Performance", f"sales-missing-{row['outlet_id']}", "high",
                "Sales data is missing", "No sales records exist in the selected reporting period.",
                "Validate and import daily sales before comparing outlet performance.")
        elif row["score"] is not None and row["score"] < 70:
            add(row["outlet_id"], row["name"], "Performance", f"performance-{row['outlet_id']}", "high",
                "Outlet performance needs attention",
                f"Performance score is {row['score']}/100; revenue growth is {row['growth'] if row['growth'] is not None else 'not available'}%.",
                "Review sales trend, margin and peer benchmark together; prepare a short recovery action plan.")
        elif row["growth"] is not None and row["growth"] < -10:
            add(row["outlet_id"], row["name"], "Performance", f"growth-{row['outlet_id']}", "medium",
                "Revenue trend is declining", f"Revenue changed {row['growth']}% versus the previous equal-length period.",
                "Check transaction volume, staffing coverage and local promotions before changing targets.")

    for row in inventory:
        if row["shortage"]:
            add(row["outlet_id"], row["outlet"], "Inventory", f"stock-{row['id']}", "high",
                f"{row['product']} is below its reorder point",
                f"On hand {row['quantity']}; reorder point {row['reorder_point']}; suggested replenishment {row['replenish']}.",
                "Confirm near-term demand and expiry risk, then replenish the required quantity.")
        if row["expiry_days"] <= 3 and row["quantity"] > 0:
            add(row["outlet_id"], row["outlet"], "Inventory", f"expiry-{row['id']}", "medium",
                f"{row['product']} has near-term expiry risk",
                f"Current stock {row['quantity']}; expiry is in {row['expiry_days']} day(s).",
                "Prioritize first-expiry-first-out usage and avoid unnecessary replenishment.")
        if row["waste_pct"] > 8:
            add(row["outlet_id"], row["outlet"], "Inventory", f"waste-{row['id']}", "medium",
                f"{row['product']} waste is elevated", f"Trailing waste rate is {row['waste_pct']}%.",
                "Review batch size, handling and storage conditions for the item.")

    for row in staff:
        if row["coverage_pct"] < 85:
            add(row["outlet_id"], row["outlet"], "Workforce", f"coverage-{row['id']}", "high",
                f"Shift coverage is low for {row['name']}",
                f"Worked {row['worked_hours']} of {row['scheduled_hours']} scheduled hours ({row['coverage_pct']}% coverage).",
                "Rebalance the roster and confirm availability before the next shift cycle.")
        elif row["hours_gap"] >= 4:
            add(row["outlet_id"], row["outlet"], "Workforce", f"gap-{row['id']}", "medium",
                f"Uncovered hours detected for {row['name']}", f"The current schedule has a {row['hours_gap']}-hour gap.",
                "Adjust shift allocation to reduce uncovered operating hours.")

    for row in marketing:
        if row["roi"] is not None and row["roi"] < 0:
            add(row["outlet_id"], row["outlet"], "Marketing", f"campaign-roi-{row['id']}", "high",
                f"{row['name']} has negative contribution ROI",
                f"ROAS {row['roas']}x; contribution ROI {row['roi']}%; conversions {row['conversions']}.",
                "Review audience, offer and attribution; test a smaller budget before scaling the campaign.")
        elif row["ctr"] < 1:
            add(row["outlet_id"], row["outlet"], "Marketing", f"campaign-ctr-{row['id']}", "medium",
                f"{row['name']} engagement is low", f"CTR is {row['ctr']}% from {row['impressions']} impressions.",
                "Test creative and targeting changes while holding the measurement window consistent.")

    insights.sort(key=lambda item: (SEVERITY_ORDER.get(item["severity"], 9), item["outlet"], item["source"], item["key"]))
    return insights


def outlet_attention(performance, insights):
    """Summarize recommendation counts per outlet; no cross-milestone franchise health score is invented."""
    result = []
    for outlet in performance:
        related = [item for item in insights if item["outlet_id"] == outlet["outlet_id"]]
        high = sum(item["severity"] == "high" for item in related)
        medium = sum(item["severity"] == "medium" for item in related)
        status = "Needs attention" if high else "Watch" if medium else "Stable"
        result.append({
            "outlet_id": outlet["outlet_id"],
            "name": outlet["name"],
            "region": outlet["region"],
            "high_priorities": high,
            "medium_priorities": medium,
            "total_insights": len(related),
            "status": status,
        })
    return result
