import os
import time
import json
import datetime
import requests
import concurrent.futures

from requests.auth import HTTPBasicAuth
from multiprocessing.pool import ThreadPool

from config import *
from crypto_config import *
import traceback

from app import celery

auth = HTTPBasicAuth('tutorial', 'pass')
headers = {'Content-Type': 'application/json'}

il_url = 'https://abe-out-il.cs300ohie.net:5000'
test_data_dir = 'test_data'
test_users_file_name = os.path.join(test_data_dir, 'users_{}_{}.json')
test_encounters_file_name = os.path.join(test_data_dir, 'encounters_{}kb.json')

results_dir = 'results'

users_file_name = 'users_{}_{}.json'
encounter_ids_file_name = 'encounter_ids.json'
encounters_file_name = 'encounters.json'

keygen_file_name = os.path.join(results_dir, 'time_key_generation_{}_{}_{}_{}_{}.txt')
save_file_name = os.path.join(results_dir, 'time_save_encounter_{}_{}_{}_{}_{}.txt')
query_file_name = os.path.join(results_dir, 'time_query_encounter_{}_{}_{}_{}_{}.txt')

if not os.path.exists(results_dir):
    os.mkdir(results_dir)

@celery.task()
def key_generation_test(num_threads, num_users, file_size, policy_size, num_attributes):
    with open(test_users_file_name.format(policy_size, num_attributes), 'r') as users_file:
        users_meta = json.load(users_file)

    transaction_times = []
    users = []
    
    def save_user_meta(user_meta):
        start = time.time()
        user_id, private_key, status_code = save_user(user_meta['attributes'])
        end = time.time()
        print(status_code)
        transaction_time = end - start
        transaction_times.append(transaction_time)
        users.append({
            'user_id': user_id,
            'private_key': private_key,
            'policy': user_meta['policy'],
            'attributes': user_meta['attributes']
        })

    pool = ThreadPool(num_users)

    test_start_date = datetime.datetime.utcnow()

    for user_meta in users_meta:
        pool.apply(save_user_meta, (user_meta,))

    pool.close()
    pool.join()
    test_end_date = datetime.datetime.utcnow()

    with open(users_file_name.format(policy_size, num_attributes), 'w') as users_file:
        print(len(users))
        json.dump(users, users_file)

    with open(keygen_file_name.format(num_threads, num_users, file_size, policy_size, num_attributes), 'w') as transaction_times_file:
        total_time = sum(transaction_times)
        num_transactions = len(transaction_times)
        avg_txn_time = total_time/float(num_transactions)
        rate = 1/avg_txn_time
        transaction_times_file.write('Key Generation Test - {} Thread, {} User, {} kb, {} attributes in policy, {} attributes in key\n'.format(
            num_threads, num_users, file_size, policy_size, num_attributes
        ))
        transaction_times_file.write('Test start: {}\n'.format(test_start_date))
        transaction_times_file.write('Test end: {}\n'.format(test_end_date))
        transaction_times_file.write('Total number of transactions: {}\n'.format(num_transactions))
        transaction_times_file.write('Total time: {}\n'.format(total_time))
        transaction_times_file.write('Average transaction time: {}\n'.format(avg_txn_time))
        transaction_times_file.write('Transactions per second: {}\n'.format(rate))
        transaction_times_file.write('\n')
        transaction_times_file.writelines(["{}\n".format(txn_time) for txn_time in transaction_times])        

@celery.task()
def save_encounter_test(num_threads, num_users, file_size, policy_size, num_attributes):
    with open(test_encounters_file_name.format(file_size), 'r') as encounters_file:
        encounters = json.load(encounters_file)
    with open(users_file_name.format(policy_size, num_attributes), 'r') as users_file:
        users = json.load(users_file)

    pool = ThreadPool(num_users)

    transaction_times = []
    encounter_ids = []

    # encounters = encounters[:20]
    def save(encounter, user):
        start = time.time()
        encounter_id, status_code = save_encounter(encounter, user['policy'], user['user_id'])
        end = time.time()
        transaction_time = end - start
        transaction_times.append(transaction_time)
        encounter_ids.append(encounter_id)

    pool = ThreadPool(num_users)

    test_start_date = datetime.datetime.utcnow()
    for encounter, user in zip(encounters, users):
        pool.apply(save, (encounter, user))

    pool.close()
    pool.join()
    test_end_date = datetime.datetime.utcnow()

    with open(encounter_ids_file_name, 'w') as encounter_ids_file:
        print(len(encounter_ids))
        json.dump(encounter_ids, encounter_ids_file)

    with open(save_file_name.format(num_threads, num_users, file_size, policy_size, num_attributes), 'w') as transaction_times_file:
        total_time = sum(transaction_times)
        num_transactions = len(transaction_times)
        avg_txn_time = total_time/float(num_transactions)
        rate = 1/avg_txn_time
        transaction_times_file.write('Save Encounter Test - {} Thread, {} User, {} kb, {} attributes in policy, {} attributes in key\n'.format(
            num_threads, num_users, file_size, policy_size, num_attributes
        ))
        transaction_times_file.write('Test start: {}\n'.format(test_start_date))
        transaction_times_file.write('Test end: {}\n'.format(test_end_date))
        transaction_times_file.write('Total number of transactions: {}\n'.format(num_transactions))
        transaction_times_file.write('Total time: {}\n'.format(total_time))
        transaction_times_file.write('Average transaction time: {}\n'.format(avg_txn_time))
        transaction_times_file.write('Transactions per second: {}\n'.format(rate))
        transaction_times_file.write('\n')
        transaction_times_file.writelines(["{}\n".format(txn_time) for txn_time in transaction_times])

@celery.task()
def query_encounter_test(num_threads, num_users, file_size, policy_size, num_attributes):
    with open(encounter_ids_file_name, 'r') as encounter_ids_file:
        encounter_ids = json.load(encounter_ids_file)
    with open(users_file_name.format(policy_size, num_attributes), 'r') as users_file:
        users = json.load(users_file)

    os.remove(encounter_ids_file_name)

    transaction_times = []
    encounters = []

    def query(encounter_id, user):
        start = time.time()
        encounter, policy, status_code = get_encounter(encounter_id, user['private_key'])
        end = time.time()
        print(status_code, encounter[''])
        transaction_time = end - start
        transaction_times.append(transaction_time)
        encounters.append(encounter)

    pool = ThreadPool(num_users)
    test_start_date = datetime.datetime.utcnow()
    for encounter_id, user in zip(encounter_ids, users):
        pool.apply(query, (encounter_id, user))

    pool.close()
    pool.join()
    test_end_date = datetime.datetime.utcnow()

    with open(encounters_file_name, 'w') as encounters_file:
        print(len(encounters))
        json.dump(encounters, encounters_file)

    with open(query_file_name.format(num_threads, num_users, file_size, policy_size, num_attributes), 'w') as transaction_times_file:
        total_time = sum(transaction_times)
        num_transactions = len(transaction_times)
        avg_txn_time = total_time/float(num_transactions)
        rate = 1/avg_txn_time
        transaction_times_file.write('Query Encounter Test - {} Thread, {} User, {} kb, {} attributes in policy, {} attributes in key\n'.format(
            num_threads, num_users, file_size, policy_size, num_attributes
        ))
        transaction_times_file.write('Test start: {}\n'.format(test_start_date))
        transaction_times_file.write('Test end: {}\n'.format(test_end_date))
        transaction_times_file.write('Total number of transactions: {}\n'.format(num_transactions))
        transaction_times_file.write('Total time: {}\n'.format(total_time))
        transaction_times_file.write('Average transaction time: {}\n'.format(avg_txn_time))
        transaction_times_file.write('Transactions per second: {}\n'.format(rate))
        transaction_times_file.write('\n')
        transaction_times_file.writelines(["{}\n".format(txn_time) for txn_time in transaction_times])
    os.remove(encounters_file_name)

def save_user(attributes):
    user_object = {
        'first_name': attributes[0],
        'last_name': attributes[1],
        'attributes': attributes[2:]
    }
    result = requests.post('{}/user'.format(il_url),
                           json=user_object,
                           headers=headers,
                           auth=auth)
    contents = result.json()
    user_id, private_key = contents['user_id'], contents['private_key']
    return (user_id, private_key, result.status_code)

def get_user_info(user_id):
    result = requests.get('{}/user/{}'.format(il_url, user_id),
                          headers=headers,
                          auth=auth)
    contents = result.json()
    return contents

def save_encounter(encounter, policy, user_id):

    def validate_user():
        ta_response = requests.get('{}/user/{}'.format(il_url, user_id),
                                   headers=headers,
                                   auth=auth)      
        user_info = ta_response.json()
        return user_info

    def validate_patient_info():
        patient_id = encounter['patient_id']
        cr_response = requests.get('{}/patient/{}'.format(il_url, patient_id),
                                   headers=headers,
                                   auth=auth)
        cr_contents = cr_response.json()
        return cr_contents

    def validate_provider_info(provider_id):
        hwr_response = requests.get('{}/provider/{}'.format(il_url, provider_id),
                                    headers=headers,
                                    auth=auth)
        hwr_contents = hwr_response.json()
        return hwr_contents

    def validate_facility_info():
        location_id = encounter['location_id']
        fr_response = requests.get('{}/location/{}'.format(il_url, location_id),
                                   headers=headers,
                                   auth=auth)
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
    save_response = requests.post('{}/encounters'.format(il_url),
                                  json=payload,
                                  headers=headers,
                                  auth=auth)
    # print(save_response.status_code)
    encounter_id = save_response.json()

    return encounter_id, save_response.status_code

def get_encounter(encounter_id, secret_key):

    query_response = requests.get('{}/encounters/{}'.format(il_url, encounter_id),
                                  headers=headers,
                                  auth=auth)
    query_contents = query_response.json()
    ciphertext = query_contents['contents']
    # print(len(ciphertext), len(ciphertext) < limit)
    ciphertext_obj = bytesToObject(ciphertext.encode('utf-8'), groupObj)
    private_key = bytesToObject(secret_key.encode('utf-8'), groupObj)
    try:
        plaintext_bytes = hybrid_abe.decrypt(pk, private_key, ciphertext_obj)
        plaintext = json.loads(str(plaintext_bytes, 'utf-8'))
        encounter = plaintext['encounter']
        policy = plaintext['policy']

        def get_patient_info():
            cr_response = requests.get('{}/patient/{}'.format(il_url, encounter['patient_id']),
                                    headers=headers,
                                    auth=auth)
            patient_info = cr_response.json()
            return patient_info

        def get_provider_info(provider_id):
            hwr_response = requests.get('{}/provider/{}'.format(il_url, provider['provider_id']),
                                        headers=headers,
                                        auth=auth)
            provider_info = hwr_response.json()
            return provider_info

        def get_facility_info():
            fr_response = requests.get('{}/location/{}'.format(il_url, encounter['location_id']), 
                                    headers=headers,
                                    auth=auth)
            location_info = fr_response.json()
            return location_info

        with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
            patient_future = executor.submit(get_patient_info)
            provider_futures = []
            for provider in encounter['providers']:    
                provider_futures.append(executor.submit(get_provider_info, provider['provider_id']))
            facility_future = executor.submit(get_facility_info)
            
            patient_info = patient_future.result()

            encounter['patient_name'] = '{} {}'.format(patient_info['given_name'], patient_info['family_name'])
            encounter['gender'] = patient_info['gender']
            encounter['city'] = patient_info['city']
            encounter['province'] = patient_info['province']
            encounter['country'] = patient_info['country']

            for i in range(len(encounter['providers'])):
                provider_info = provider_futures[i].result()
                provider = encounter['providers'][i]
                provider['attributes'] = provider_info['attributes']
                provider['identifier'] = provider_info['identifier']
                provider['name'] = provider_info['name']
            
            facility_info = facility_future.result()
            encounter['location_name'] = facility_info['name']

    except Exception as e:
        # print('failed to get encounter!')
        traceback.print_exc()
        encounter = ciphertext
        policy = None

    return encounter, policy, query_response.status_code