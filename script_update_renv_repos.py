### CREATE MODULE
# 1. Create Git repository
# 2. Create Preliminary index.yml
# Insert Quantargo repository to renv file

import json

lockfile = {}
with open('renv.lock') as jsonfile:
  lockfile = json.load(jsonfile)
  lockfile['R']['Repositories'].insert(0, {'Name': 'QUANTARGO', 'URL': 'https://repository.quantargo.com/ubuntu-20.04/r-4.0.5'})

with open('renv.lock', 'w') as outfile:
  json.dump(lockfile, outfile)
