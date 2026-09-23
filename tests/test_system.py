import io
import json
import os
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

from franchiseops.db import connect, initialize
from franchiseops.seed import seed
from franchiseops.agents import analyze, run_agents
from franchiseops.imports import import_csv, SCHEMAS
from franchiseops.server import application


class FranchiseOpsMilestone3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test.db"
        self.old = os.environ.get("FRANCHISEOPS_DB")
        os.environ["FRANCHISEOPS_DB"] = str(self.path)
        self.db = connect()
        initialize(self.db)
        seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
        if self.old is None:
            os.environ.pop("FRANCHISEOPS_DB", None)
        else:
            os.environ["FRANCHISEOPS_DB"] = self.old

    def request(self, path, method="GET", payload=None, query=""):
        body = json.dumps(payload or {}).encode()
        status = []
        env = {
            "PATH_INFO": path,
            "REQUEST_METHOD": method,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
            "QUERY_STRING": query,
            "REMOTE_ADDR": "test",
        }
        result = b"".join(application(env, lambda value, headers: status.append(value)))
        return int(status[0].split()[0]), result

    def test_seed_is_idempotent(self):
        seed(self.db)
        self.assertEqual(self.db.execute("SELECT count(*) FROM sales").fetchone()[0], 540)
        self.assertEqual(self.db.execute("SELECT count(*) FROM staff").fetchone()[0], 30)
        self.assertEqual(self.db.execute("SELECT count(*) FROM campaigns").fetchone()[0], 12)

    def test_scope_contains_only_milestones_1_to_3_outputs(self):
        data = analyze(self.db)
        self.assertEqual(set(data) - {"start", "end", "snapshot_date"}, {"performance", "inventory", "staff", "marketing", "insights", "outlet_summary"})
        self.assertNotIn("audit", data)
        self.assertNotIn("intelligence", data)

    def test_database_has_no_post_milestone3_tables(self):
        tables = {row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertNotIn("audits", tables)
        self.assertNotIn("alerts", tables)
        self.assertNotIn("notifications", tables)

    def test_inventory_forecast_and_replenishment(self):
        row = next(x for x in analyze(self.db)["inventory"] if x["outlet_id"] == 2 and x["product"] == "Rice (kg)")
        self.assertGreater(row["replenish"], 0)
        self.assertEqual(row["history_days"], 28)
        self.assertAlmostEqual(row["forecast_7d"], row["daily_demand"] * 7, delta=.1)

    def test_staff_workforce_metrics(self):
        row = next(x for x in analyze(self.db)["staff"] if x["outlet_id"] == 5)
        self.assertEqual(row["coverage_pct"], 72.5)
        self.assertEqual(row["hours_gap"], 11)
        self.assertEqual(row["status"], "Under-covered")

    def test_marketing_effectiveness_uses_margin(self):
        campaign = next(x for x in analyze(self.db)["marketing"] if x["outlet_id"] == 2)
        self.assertEqual(campaign["roi"], -28)
        self.assertEqual(campaign["roas"], 1.8)
        self.assertEqual(campaign["effectiveness"], "Weak")

    def test_operational_insights_use_only_m1_to_m3_sources(self):
        insights = analyze(self.db)["insights"]
        self.assertGreater(len(insights), 0)
        self.assertTrue({x["source"] for x in insights}.issubset({"Performance", "Inventory", "Workforce", "Marketing"}))
        self.assertTrue(any(x["source"] == "Workforce" for x in insights))
        self.assertTrue(any(x["source"] == "Marketing" for x in insights))

    def test_no_composite_franchise_intelligence_score(self):
        data = analyze(self.db)
        for row in data["outlet_summary"]:
            self.assertNotIn("score", row)
            self.assertNotIn("risk", row)
            self.assertIn(row["status"], {"Stable", "Watch", "Needs attention"})

    def test_zero_spend_and_no_inventory_history(self):
        self.db.execute("UPDATE campaigns SET spend=0")
        self.db.execute("DELETE FROM movements")
        self.db.commit()
        data = analyze(self.db)
        self.assertIsNone(data["marketing"][0]["roi"])
        self.assertIsNone(data["inventory"][0]["daily_demand"])
        json.dumps(data, allow_nan=False)

    def test_run_agents_reports_four_agents_and_m3_scope(self):
        result = run_agents(self.db)
        self.assertEqual(result["agents"], 4)
        self.assertEqual(result["scope"], "Milestones 1-3")
        self.assertEqual(result["agents_run"], ["Performance", "Inventory", "Staff", "Marketing"])
        self.assertGreaterEqual(result["operational_insights"], 1)

    def test_csv_transaction_rollback(self):
        old = self.db.execute("SELECT revenue FROM sales WHERE outlet_id=1 ORDER BY date DESC").fetchone()[0]
        content = f"outlet_id,date,revenue,transactions,cost\n1,{date.today()},123,1,20\n999,{date.today()},100,1,20\n"
        with self.assertRaises(sqlite3.IntegrityError):
            import_csv(self.db, "sales", content)
        self.assertEqual(old, self.db.execute("SELECT revenue FROM sales WHERE outlet_id=1 ORDER BY date DESC").fetchone()[0])

    def test_bad_numbers_rejected(self):
        for value in ["nan", "inf", "-1"]:
            with self.assertRaises(ValueError):
                import_csv(self.db, "sales", f"outlet_id,date,revenue,transactions,cost\n1,2026-01-01,{value},1,20\n")

    def test_upsert_sales(self):
        content = f"outlet_id,date,revenue,transactions,cost\n1,{date.today()},123,1,20\n"
        import_csv(self.db, "sales", content)
        import_csv(self.db, "sales", content)
        self.assertEqual(self.db.execute("SELECT count(*) FROM sales").fetchone()[0], 540)
        self.assertEqual(self.db.execute("SELECT revenue FROM sales WHERE outlet_id=1 AND date=?", (str(date.today()),)).fetchone()[0], 123)

    def test_import_schemas_exclude_audits(self):
        self.assertEqual(set(SCHEMAS), {"franchises", "outlets", "sales", "inventory", "movements", "staff", "campaigns"})

    def test_dashboard_filters_and_scope(self):
        code, body = self.request("/api/dashboard", query="outlet=2")
        self.assertEqual(code, 200)
        data = json.loads(body)
        self.assertEqual(len(data["performance"]), 1)
        self.assertTrue(all(x["outlet_id"] == 2 for x in data["inventory"]))
        self.assertTrue(all(x["outlet_id"] == 2 for x in data["insights"]))
        self.assertEqual(data["scope"]["agents"], 4)

    def test_removed_extra_routes(self):
        self.assertEqual(self.request("/api/brief", "POST")[0], 404)
        self.assertEqual(self.request("/api/actions", "POST")[0], 404)
        self.assertEqual(self.request("/api/login", "POST")[0], 404)
        self.assertEqual(self.request("/api/logout", "POST")[0], 404)

    def test_public_run_and_import(self):
        self.assertEqual(self.request("/api/run", "POST")[0], 200)
        sample = f"outlet_id,date,revenue,transactions,cost\n1,{date.today()},123,1,20\n"
        code, body = self.request("/api/import", "POST", {"dataset": "sales", "csv": sample})
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["rows"], 1)

    def test_export_formula_escape(self):
        self.db.execute("UPDATE staff SET name='=1+1' WHERE id=1")
        self.db.commit()
        code, body = self.request("/api/export", query="dataset=staff")
        self.assertEqual(code, 200)
        self.assertIn("'=1+1", body.decode())

    def test_invalid_dates_and_unknown_routes(self):
        self.assertEqual(self.request("/api/dashboard", query="start=bad")[0], 400)
        self.assertEqual(self.request("/api/missing")[0], 404)


if __name__ == "__main__":
    unittest.main()
