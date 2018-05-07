# USAGE:
# docker exec abeoutpos_abe-out-pos_1 python3 key_generation_test.py <policy_size> <num_attributes> <num_txns>_encounters.json
import sys
import os
import time
import json
import requests
import datetime
import warnings
import random
import concurrent.futures

import logging

from functools import reduce

from config import *
from crypto_config import *

with open(master_key_file_name) as master_key_file:
    master_key = json.load(master_key_file)

pk = bytesToObject(master_key['pk'].encode('utf-8'), groupObj)
mk = bytesToObject(master_key['mk'].encode('utf-8'), groupObj)

def save_encounter(encounter, policy, user_id):

    def validate_user():
        ta_response = requests.get('{}/user/{}'.format(il_upstream_url, user_id),
                                   headers=headers,
                                   auth=auth,
                                   verify=False)      
        user_info = ta_response.json()
        return user_info

    def validate_patient_info():
        patient_id = encounter['patient_id']
        cr_response = requests.get('{}/patient/{}'.format(il_upstream_url, patient_id),
                                   headers=headers,
                                   auth=auth,
                                   verify=False)
        cr_contents = cr_response.json()
        return cr_contents

    def validate_provider_info(provider_id):
        hwr_response = requests.get('{}/provider/{}'.format(il_upstream_url, provider_id),
                                    headers=headers,
                                    auth=auth,
                                   verify=False)
        hwr_contents = hwr_response.json()
        return hwr_contents

    def validate_facility_info():
        location_id = encounter['location_id']
        fr_response = requests.get('{}/location/{}'.format(il_upstream_url, location_id),
                                   headers=headers,
                                   auth=auth,
                                   verify=False)
        fr_contents = fr_response.json()
        return fr_contents

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.submit(validate_user)
        executor.submit(validate_patient_info)
        for provider in encounter['providers']:
            executor.submit(validate_provider_info, provider['provider_id'])
        executor.submit(validate_facility_info)

    plaintext = json.dumps({
        'encounter': encounter,
        'policy': policy
    })

    # encrypt
    ciphertext = hybrid_abe.encrypt(pk, plaintext, policy)
    ciphertext = objectToBytes(ciphertext, groupObj)
    ciphertext = str(ciphertext, 'utf-8')

    payload = {
        'patient_id': encounter['patient_id'],
        'contents': ciphertext
    }

    # print(len(payload['contents']), len(payload['contents']) < limit)
    save_response = requests.post('{}/encounters'.format(il_upstream_url),
                                  json=payload,
                                  headers=headers,
                                  auth=auth,
                                  verify=False)
    # print(save_response.status_code)
    encounter_id = save_response.json()

    return encounter_id, save_response.status_code

test_data_dir = 'input'
output_data_dir = 'data'

policy_size = int(sys.argv[1])
num_attributes = int(sys.argv[2])
input_filename = sys.argv[3]

num_txns_str = input_filename.split("_")[0]

users_file_name = 'users_{}_{}_{}.json'.format(policy_size, num_attributes, num_txns_str)
encounter_ids_file_name = '{}_encounter_ids_{}_{}.json'.format(num_txns_str, policy_size, num_attributes)
transaction_summary_file_name = '{}_{}_{}_save_transaction_summary.txt'.format(policy_size, num_attributes, num_txns_str)

users_file_path = os.path.join(test_data_dir, users_file_name)
input_path = os.path.join(test_data_dir, input_filename)
encounter_ids_path = os.path.join(test_data_dir, encounter_ids_file_name)

transaction_summary_path = os.path.join(output_data_dir, transaction_summary_file_name)

with open(users_file_path) as users_file:
    users = json.load(users_file)

with open(input_path) as input_file:
    encounters = json.load(input_file)

transaction_times_success = []
transaction_times = []
status_codes = []
encounter_ids = []
error_count = 0

def save(encounter, user, retry=False):
    global error_count
    start = time.time()
    encounter_id, status_code = save_encounter(encounter, user['policy'], user['user_id'])
    end = time.time()
    print(status_code) 
    transaction_time = end - start
    if status_code == 201:
        transaction_times_success.append(transaction_time)
        encounter_ids.append({
            'user': user,
            'encounter_id': encounter_id
        })
    else:
        error_count += 1
    if not retry:
        status_codes.append(status_code)        
        transaction_times.append(transaction_time)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    eupair = list(zip(encounters, users))
    test_start_date = datetime.datetime.utcnow()
    for encounter, user in eupair:
        save(encounter, user)
    while error_count > 0:
        retries = error_count
        error_count = 0
        while retries > 0:
            encounter, user = random.choice(eupair)
            save(encounter, user, True)
            retries -= 1
    test_end_date = datetime.datetime.utcnow()

with open(encounter_ids_path, "w") as encounter_ids_file:
    print("number of encounters: {}".format(len(encounter_ids)))
    json.dump(encounter_ids, encounter_ids_file)

with open(transaction_summary_path, "w") as transaction_summary_file:
    total_time = sum(transaction_times)
    num_transactions = len(transaction_times)
    avg_txn_time = total_time/float(num_transactions)
    rate = 1/avg_txn_time

    total_time_success = sum(transaction_times_success)
    avg_txn_time_success = total_time_success/float(num_transactions)
    rate_success = 1/avg_txn_time_success

    successful_transactions = reduce(lambda a,b: a + b, map(lambda x: 1 if x == 201 else 0, status_codes))
    transaction_summary_file.write('Test start: {}\n'.format(test_start_date))
    transaction_summary_file.write('Test end: {}\n'.format(test_end_date))
    transaction_summary_file.write('Total number of transactions: {}\n'.format(num_transactions))
    transaction_summary_file.write('Total time: {}\n'.format(total_time))
    transaction_summary_file.write('Average transaction time: {}\n'.format(avg_txn_time))
    transaction_summary_file.write('Average transaction time (success): {}\n'.format(avg_txn_time_success))
    transaction_summary_file.write('Transactions per second: {}\n'.format(rate))
    transaction_summary_file.write('Transactions per second (success): {}\n'.format(rate_success))
    transaction_summary_file.write('Successful transactions: {}\n'.format(successful_transactions))
    transaction_summary_file.write('\n')
    transaction_summary_file.writelines(["{}, {}\n".format(status_code, txn_time) for txn_time, status_code in zip(transaction_times, status_codes)])
    transaction_summary_file.write('\n')
    transaction_summary_file.writelines(["{}, {}\n".format(201, txn_time) for txn_time in transaction_times_success])