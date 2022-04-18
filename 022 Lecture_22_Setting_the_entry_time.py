from login import *
from alice_blue import *
import datetime
from pprint import pprint
from time import sleep
import csv

alice = None
socket_opened = False
entry_time = datetime.time(9,30)


def event_handler_quote_update(message):
	global ltp
	ltp = message['ltp']
	print('\nLTP = ', ltp)

def open_callback():
	global socket_opened
	socket_opened = True

def open_socket_now():
	global socket_opened
	socket_opened = False
	alice.start_websocket(subscribe_callback = event_handler_quote_update,
							socket_open_callback = open_callback,
							run_in_background = True)
	sleep(2)
	while (socket_opened == False):
		pass



def main():
	global alice, socket_opened, script

	if alice == None:
		access_token = open('access_token.txt', 'r').read().strip()
		alice = AliceBlue(username = username, password = password, 
			access_token = access_token, master_contracts_to_download = ['NSE', 'NFO'])
		print('....... login Success ..\n')

	if socket_opened == False:
		open_socket_now()

	while datetime.datetime.now().time() <= entry_time:
		print('waiting for right time')
		sleep(10)


if (__name__ == '__main__'):
	main()