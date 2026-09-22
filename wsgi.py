"""Deployment entry point; fail closed if demo credentials are still configured."""
import os
if len(os.getenv('ADMIN_PASSWORD',''))<12 or os.getenv('ADMIN_PASSWORD')=='demo-change-me':
    raise RuntimeError('Set a strong ADMIN_PASSWORD with at least 12 characters for deployment')
from franchiseops.server import application
