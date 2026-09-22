"""Optional background agent cycle. Run separately from the web process."""
import argparse,time,logging
from franchiseops.db import connect,initialize
from franchiseops.agents import run_agents
from franchiseops.notifications import dispatch
parser=argparse.ArgumentParser();parser.add_argument('--interval',type=int,default=300);parser.add_argument('--dispatch',action='store_true');args=parser.parse_args()
if args.interval<30: parser.error('Minimum interval is 30 seconds')
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
try:
    while True:
        db=connect()
        try:
            initialize(db);logging.info('Agent run: %s',run_agents(db))
            if args.dispatch: dispatch(db)
        except Exception: logging.exception('Cycle failed; will retry next interval')
        finally: db.close()
        time.sleep(args.interval)
except KeyboardInterrupt: logging.info('Worker stopped')
