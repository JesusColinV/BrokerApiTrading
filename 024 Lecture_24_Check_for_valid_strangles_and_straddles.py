from login import *
from alice_blue import *
import datetime
from pprint import pprint
from time import sleep
import csv

alice = None
socket_opened = False
entry_time = datetime.time(9,30)


symbol = 'NIFTY'
fut_expiry_date = datetime.date(2021,6,24)
expire_on = '21JUN'


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


def open_positions():
	global alice, array_strike_p, array_symbol, array_buy_or_sell, array_quantity, datecalc, ltp
	h2 = alice.get_netwise_positions()
	# pprint(h2)

	# We will store the details of the open positions in various arrays
	array_strike_p = [] #eg. 14300
	array_symbol = [] #eg. PE or CE
	array_buy_or_sell = [] # eg. 'SELL' or 'BUY'
	array_quantity = [] # eg. 75 or -75
	array_trading_symbol = [] #eg. ['NIFTY21JUN15500CE']

	if h2['data']['positions'] == []:
		print('No Open Positions right now\n')

	else: ## if h2 is no empty
		for x in h2['data']['positions']:
			if x['trading_symbol'][0:5] == symbol and x['trading_symbol'][5:10] == expire_on:
				if x['net_quantity'] !=0:
					y = x['strike_price']

					z = int(round(float(y)))  # convert this to integer

					a = x['trading_symbol'][-2:]

					n = x['net_quantity']
					if n< 0:
						position = 'SELL'
					elif n > 0:
						position = 'BUY'
					else:
						print('some error')

					t = x['trading_symbol']

					array_strike_p.append(z)
					array_symbol.append(a)
					array_buy_or_sell.append(position)
					array_quantity.append(n)
					array_trading_symbol.append(t)

	print('quantity:', array_quantity)
	print('Full Symbol:', array_trading_symbol)

def check_for_valid_strangle_or_straddle():
	global order_placed, valid_contracts

	sell_counter = 0
	place = []

	for x in range(len(array_buy_or_sell)):
		if array_buy_or_sell[x] == 'SELL':
			sell_counter = sell_counter + 1
			place.append(x)

	if sell_counter == 2:
		if (array_symbol[place[0]] == 'PE' and array_symbol[place[1]] == 'CE' or array_symbol[place[0]] == 'CE' and array_symbol[place[1]] == 'PE'):
			print('Valid Strangle or Straddle found')
			valid_contracts = 'Found'

			if array_symbol[place[0]] == 'PE' and array_symbol[place[1]] == 'CE':
				ce_strike = array_strike_p[place[1]]
				pe_strike = array_strike_p[place[0]]

			elif array_symbol[place[0]] == 'CE' and array_symbol[place[1]] == 'PE':
				ce_strike = array_strike_p[place[0]]
				pe_strike = array_strike_p[place[1]]

		else:
			print('2 sell contracts found but No Straddle or Strangle found')
			valid_contracts = "Not_Found"


	elif sell_counter == 0:
		print(f"{sell_counter} no of Sell Contracts found")
		valid_contracts = "Not_Found"

	else:
		print(f"{sell_counter} no of Sell Contracts found. .Do something about it, then restart the program")
		valid_contracts = "Error_Contracts"


	if valid_contracts == 'Found':
		order_placed = True
	elif valid_contracts == "Not_Found":
		order_placed = False
	elif valid_contracts == "Error_Contracts":
		order_placed = False
		print("Clear the old orders... unable to execute")


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

	script = alice.get_instrument_for_fno(symbol = symbol, expiry_date = fut_expiry_date, 
		is_fut = True, strike = None, is_CE = False)

	open_positions()
	check_for_valid_strangle_or_straddle()

	print("Status of order_placed = ", order_placed)



if (__name__ == '__main__'):
	main()