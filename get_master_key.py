import requests
import json
import os

from config import *
from crypto_config import *

retries = 100

while retries > 0:
    response = requests.get('{}/masterkey'.format(ta_url), auth=auth)
    if response.status_code == 200:
        master_key = response.json()
        with open(master_key_file_name, "w") as master_key_file:
            json.dump(master_key, master_key_file)
        break
    else:
        retries -= 1
else:
    print("Master key file not found!")
