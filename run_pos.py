import requests
import json
import os
import time
import random
import base64

from requests.auth import HTTPBasicAuth

from models import *

auth = HTTPBasicAuth('tutorial', 'pass')
headers = {'Content-Type': 'application/json'}

encounters_file = 'encounters.json'

# with open('image.jpg', "rb") as image_file:
#     image = image_file.read()

# import base64
# image = str(base64.b64encode(image), 'utf-8')
# print(image)
# print(type(image))
# print(len(image))

# load encounters file and get the desired number of encounters
filesize = os.path.getsize(encounters_file)
with open(encounters_file, 'r') as encounters_file:
    encounters = json.load(encounters_file)
    average_encounter_size = filesize / len(encounters)
    encounters = encounters[:num_encounters]

print('Average encounter size:', average_encounter_size)

run = 0
run_times = []
for run in range(1):
    with open(os.path.join('policies', 
                        'length_{}'.format(policy_length), 
                        '{} attributes in key'.format(key_size),
                        'run 0.json')) as test_input_file:
        test_input = json.load(test_input_file)

    users = []
    start = time.time()
    for i in range(len(test_input)):
        user_id, private_key = save_user(test_input[i]['attributes'])
        user = {
            'user_id': user_id,
            'private_key': private_key,
            'policy': test_input[i]['policy']
        }
        users.append(user)
    end = time.time()
    total_key_generation_time = end - start
    print('Total key generation time:', total_key_generation_time, '\tAverage:', total_key_generation_time/len(test_input))

    encounter_ids = []
    # for i in range(5):
    start = time.time()
    for i in range(len(encounters)):
        user = users[i % len(test_input)]
        user_id = user['user_id']
        policy = user['policy']

        # encounters[i]['image'] = image

        encounter_id = save_encounter(encounters[i], user['policy'], user_id)
        encounter_ids.append(encounter_id)
    end = time.time()

    total_save_time = end - start
    print('Save encounter total time:', total_save_time, "\tAverage:", total_save_time/len(encounters))

    start = time.time()
    fetched_encounters = []
    policies = []
    for i in range(len(encounter_ids)):
        user = users[i % len(test_input)]
        secret_key = user['private_key']
        encounter, policy = get_encounter(encounter_ids[i], secret_key)
        fetched_encounters.append(encounter)
        policies.append(policy)
    end = time.time()

    total_query_time = end - start
    print('Query encounter total time:', total_query_time, "\tAverage:", total_query_time/len(fetched_encounters))