from login import *
import csv
from alice_blue import *

access_token = AliceBlue.login_and_get_access_token(username=username, 
	password=password,twoFA=twoFA, api_secret=api_secret, redirect_url=redirect_url, app_id=app_id)

print(access_token)

with open('access_token.txt', 'w') as wr1:
	wr = csv.writer(wr1)
	wr.writerow([access_token])