#!/usr/bin/env python3
import argparse
from wsgiref.simple_server import make_server
from franchiseops.db import connect, initialize
from franchiseops.seed import seed
from franchiseops.agents import run_agents
from franchiseops.server import application


def main():
    parser = argparse.ArgumentParser(description="FranchiseOps AI - Milestones 1-3")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--empty", action="store_true", help="Initialize without synthetic data")
    parser.add_argument("--run-once", action="store_true", help="Run Milestones 1-3 analytics and exit")
    args = parser.parse_args()

    db = connect()
    initialize(db)
    if not args.empty:
        seed(db)
    if db.execute("SELECT count(*) FROM outlets").fetchone()[0]:
        run_agents(db)
    db.close()
    if args.run_once:
        return

    print(f"FranchiseOps AI Milestone 3: http://{args.host}:{args.port}", flush=True)
    with make_server(args.host, args.port, application) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
