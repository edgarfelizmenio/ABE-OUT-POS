import json
import zlib

import concurrent.futures
import requests

from config import *
from crypto_config import *
import traceback

limit = (1 << 32) - 1

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
    return (user_id, private_key)

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

    # print('save_encounter:', len(encounter['image']))

    plaintext = json.dumps({
        'encounter': encounter,
        'policy': policy
    })

    # encrypt
    plaintext = zlib.compress(plaintext.encode('utf-8'), 9)
    ciphertext = hybrid_abe.encrypt(pk, plaintext, policy)
    ciphertext = objectToBytes(ciphertext, groupObj)
    ciphertext = str(ciphertext, 'utf-8')

    payload = {
        'patient_id': encounter['patient_id'],
        'contents': ciphertext
    }



    print(len(payload['contents']), len(payload['contents']) < limit)
    save_response = requests.post('{}/encounters'.format(il_url), 
                             json=payload, 
                             headers=headers, 
                             auth=auth)
    encounter_id = save_response.json()

    return encounter_id

def get_encounter(encounter_id, secret_key):

    query_response = requests.get('{}/encounters/{}'.format(il_url, encounter_id),
                                  headers=headers,
                                  auth=auth)
    query_contents = query_response.json()
    ciphertext = query_contents['contents']
    print(len(ciphertext), len(ciphertext) < limit)
    ciphertext_obj = bytesToObject(ciphertext.encode('utf-8'), groupObj)
    private_key = bytesToObject(secret_key.encode('utf-8'), groupObj)
    try:
        plaintext_bytes = hybrid_abe.decrypt(pk, private_key, ciphertext_obj)
        plaintext_bytes = zlib.decompress(plaintext_bytes)
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
        print('failed to get encounter!')
        traceback.print_exc()
        encounter = ciphertext
        policy = None

    return encounter, policy