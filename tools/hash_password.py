"""Print a password hash for ADMIN_PASSWORD or VIEWER_PASSWORD."""
import getpass,secrets,hashlib
password=getpass.getpass('Password (12+ characters): ')
if len(password)<12: raise SystemExit('Use at least 12 characters')
salt=secrets.token_bytes(16)
print('pbkdf2$'+salt.hex()+'$'+hashlib.pbkdf2_hmac('sha256',password.encode(),salt,260000).hex())
