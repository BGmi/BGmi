import json
import os
import glob
with open('/var/lib/transmission-daemon/info/settings.json', 'r') as f:
    config = json.load(f)

with open('/var/lib/transmission-daemon/info/settings.json', 'w') as f:
    config['rpc-authentication-required'] = False
    json.dump(config, f)

HOME = os.environ.get('HOME')
if not glob.glob(os.path.join(HOME, '.config/transmission-daemon')):
    os.makedirs(os.path.join(HOME, '.config/transmission-daemon'))
with open(os.path.join(HOME, '.config/transmission-daemon/settings.json'), 'w') as f:
    json.dump(config, f)
