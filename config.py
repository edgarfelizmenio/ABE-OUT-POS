from requests.auth import HTTPBasicAuth

il_url = 'https://10.147.72.11'
il_channel_port = 5000

il_upstream_url = '{}:{}'.format(il_url, il_channel_port)
auth = HTTPBasicAuth('tutorial', 'pass')
headers = {'Content-Type': 'application/json'}

num_encounters = 5