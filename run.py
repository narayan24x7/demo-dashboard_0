#!/usr/bin/env python3
import argparse, os
from wsgiref.simple_server import make_server
from franchiseops.db import connect, initialize
from franchiseops.seed import seed
from franchiseops.agents import run_agents
from franchiseops.notifications import dispatch
from franchiseops.server import application

def main():
    parser=argparse.ArgumentParser(description='FranchiseOps AI')
    parser.add_argument('--host',default='127.0.0.1'); parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--empty',action='store_true',help='Initialize without synthetic data')
    parser.add_argument('--run-once',action='store_true',help='Run agents and exit')
    parser.add_argument('--dispatch',action='store_true',help='Opt in to sending configured notifications')
    args=parser.parse_args()
    if args.host not in ('127.0.0.1','localhost') and (len(os.getenv('ADMIN_PASSWORD',''))<12 or os.getenv('ADMIN_PASSWORD')=='demo-change-me'):
        parser.error('Set ADMIN_PASSWORD to a strong password of at least 12 characters before exposing the server')
    db=connect(); initialize(db)
    if not args.empty: seed(db)
    if db.execute('SELECT count(*) FROM outlets').fetchone()[0]: run_agents(db)
    if args.dispatch: dispatch(db)
    db.close()
    if args.run_once: return
    print(f'FranchiseOps AI: http://{args.host}:{args.port}',flush=True)
    if not os.getenv('ADMIN_PASSWORD'): print('Local demo login: admin / demo-change-me',flush=True)
    with make_server(args.host,args.port,application) as httpd: httpd.serve_forever()

if __name__=='__main__': main()
