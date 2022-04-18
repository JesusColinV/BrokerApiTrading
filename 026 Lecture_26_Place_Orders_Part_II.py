from login import *
from alice_blue import *
import datetime
from pprint import pprint
from time import sleep
import csv

alice = None
socket_opened = False
entry_time = datetime.time(0,30)


symbol = 'NIFTY'
fut_expiry_date = datetime.date(2021, 6, 24)
expire_on = '21JUN'
strike_range = 0

livefeed = LiveFeedType.MARKET_DATA
no_of_lots = 1
product_type = ProductType.Intraday
datecalc = datetime.date(2021, 6 , 24)


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


def get_prices():
	global ltp, ce_strike, pe_strike, alice, script

	try:
		alice.subscribe(script, livefeed)
		sleep(1)
		curr_ltp = int(ltp)
		alice.unsubscribe(script, livefeed)

		# First 3 digits
		a = int(str(curr_ltp)[0:3])
		c = curr_ltp%100

		if c <= 25:
			m = 0
		elif (c > 25 and c <= 50) or (c > 50 and c < 75):
			m = 50
		elif c >= 75:
			m = 100
		else:
			print('some error in selecting strike prices')

		ce_strike, pe_strike = (a*100 + m)+ strike_range, (a*100 + m)- strike_range
		print('ce_strike = ', ce_strike, 'pe_strike =', pe_strike)

	except Exception as e:
		print(f"some error occurred in getting ltp or getting strike prices::: -> {e}")


def place_strangle_or_straddle():
	global ce_strike, pe_strike

	print('placing two orders: Sell CE and Sell PE')

	get_ce_curr_price_spread(ce_strike)
	get_pe_curr_price_spread(pe_strike)

def get_ce_curr_price_spread(ce_strike):
	global alice, ltp, datecalc

	n_call = alice.get_instrument_for_fno(symbol = symbol, expiry_date = datecalc, is_fut = False, strike = ce_strike, is_CE = True)

	alice.subscribe(n_call, livefeed)
	sleep(1)

	Sell_ce_option(n_call)

	alice.unsubscribe(n_call, livefeed)


def get_pe_curr_price_spread(pe_strike):
	global alice, ltp, datecalc

	n_put = alice.get_instrument_for_fno(symbol = symbol, expiry_date = datecalc, is_fut = False, strike = pe_strike, is_CE = False)

	alice.subscribe(n_put, livefeed)
	sleep(1)

	Sell_pe_option(n_put)

	alice.unsubscribe(n_put, livefeed)

def Sell_ce_option(n_call):
	quantity = no_of_lots*int(n_call[5])

	order = alice.place_order(transaction_type = TransactionType.Sell,
								instrument = n_call,
								quantity = quantity,
								order_type = OrderType.Market,
								product_type = product_type,
								price = 0.0,
								trigger_price = None,
								stop_loss = None,
								square_off = None,
								trailing_sl = None,
								is_amo = False)

	try:
		if order['status'] == 'success':
			print(f"\nCE Sell order at {ce_strike} placed {no_of_lots} lots at price = {ltp}")
	except Exception as e:
		print("Sell CE Order placing status failed =>", e)


def Sell_pe_option(n_put):
	quantity = no_of_lots*int(n_put[5])

	order = alice.place_order(transaction_type = TransactionType.Sell,
								instrument = n_put,
								quantity = quantity,
								order_type = OrderType.Market,
								product_type = product_type,
								price = 0.0,
								trigger_price = None,
								stop_loss = None,
								square_off = None,
								trailing_sl = None,
								is_amo = False)

	try:
		if order['status'] == 'success':
			print(f"\nPE Sell order at {pe_strike} placed {no_of_lots} lots at price = {ltp}")
	except Exception as e:
		print("Sell PE Order placing status failed =>", e)


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


	while True:

		if (datetime.datetime.now().second % 10 == 0):
			if order_placed == False:

				get_prices()

				try:
					place_strangle_or_straddle()
					sleep(10)

					open_positions()
					check_for_valid_strangle_or_straddle()

					print("status of order_placed after creating = ", order_placed)

					## If order has been placed but not executed... Then we pause the code
					while valid_contracts != "Found":
						print("Order Placed but not executed.. Rectify and run again")
						sleep(30)


				except Exception as e:
					print('error in placing order => ', e)
					print('\nNow orders Not placed.. Error\n')




if (__name__ == '__main__'):
	main()