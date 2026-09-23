"""Launch the real Milestone 3 server with an isolated DB and exercise core HTTP routes."""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as directory:
    env = dict(os.environ, FRANCHISEOPS_DB=str(Path(directory) / "test.db"))
    process = subprocess.Popen([sys.executable, str(root / "run.py"), "--port", "18761"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        base = "http://127.0.0.1:18761"
        for _ in range(50):
            try:
                with urllib.request.urlopen(base + "/healthz", timeout=1) as response:
                    health = json.load(response)
                    assert health["status"] == "ok"
                    assert health["scope"] == "Milestones 1-3"
                break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError("Server did not start")

        headers = {"Content-Type": "application/json"}
        for path in ["/api/dashboard", "/api/dashboard?outlet=2"]:
            with urllib.request.urlopen(urllib.request.Request(base + path, headers=headers)) as response:
                result = json.load(response)
                assert len(result["performance"]) == (1 if "?" in path else 6)
                assert "audit" not in result and "intelligence" not in result
                assert result["scope"]["agents"] == 4

        with urllib.request.urlopen(urllib.request.Request(base + "/api/run", b"{}", headers)) as response:
            run = json.load(response)
            assert run["agents"] == 4
            assert run["scope"] == "Milestones 1-3"

        for removed in ["/api/brief", "/api/actions"]:
            try:
                urllib.request.urlopen(urllib.request.Request(base + removed, b"{}", headers))
                raise AssertionError("Removed route unexpectedly exists: " + removed)
            except urllib.error.HTTPError as error:
                assert error.code == 404

        for path in ["/", "/app.js", "/style.css"]:
            with urllib.request.urlopen(base + path) as response:
                assert response.status == 200
        print("PASS Milestone 3 HTTP: health, dashboard, filters, four-agent run, removed extra routes, static assets")
    finally:
        process.terminate()
        process.communicate(timeout=10)
