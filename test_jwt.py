import jwt
from server import search_traces

SECRET = 'secret'

# 1. Valid Token for Organization '0000-000000000000' (Matches Ingested Data)
valid_payload = {'org.service.id': '0000-000000000000'}
valid_token = jwt.encode(valid_payload, SECRET, algorithm='HS256')

print('--- TEST 1: Valid Token ---')
print(search_traces('error', valid_token))

# 2. Invalid Token (Wrong Secret)
invalid_token = jwt.encode(valid_payload, 'wrong_secret', algorithm='HS256')

print('\n--- TEST 2: Invalid Token ---')
print(search_traces('error', invalid_token))

# 3. Valid Token but Wrong Org (Should return no results)
wrong_org_payload = {'org.service.id': 'different-org-id'}
wrong_org_token = jwt.encode(wrong_org_payload, SECRET, algorithm='HS256')

print('\n--- TEST 3: Wrong Org Token ---')
print(search_traces('error', wrong_org_token))
