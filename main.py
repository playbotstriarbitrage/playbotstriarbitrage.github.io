import http.server
import socketserver
import os
import requests
import asyncio
import json
import subprocess
import alpaca_trade_api as alpaca
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from binance.client import Client
from alpaca_trade_api import REST

# Define the URL to fetch crypto quotes from
DATA_URL = "https://data.alpaca.markets/v1beta2"

# Define the API keys and base URL
api_key = input("Enter your Alpaca API key: ")
secret_key = input("Enter your Alpaca secret key: ")
account_type = input(
  "Do you want to use a paper or live account? (paper/live): ")
base_url = "https://paper-api.alpaca.markets" if account_type.lower(
) == "paper" else "https://api.alpaca.markets"

# Define the HTTP headers
HEADERS = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": secret_key}
# Initiate Alpaca connection
api = alpaca.REST(api_key, secret_key, base_url)

# Create the Flask application object
app = Flask(__name__)
app.secret_key = 'eiWee8ep9due4deeshoa8Peichai8Ei2'

# Set the SQLAlchemy database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///admin.db'

# Initialize the SQLAlchemy extension
db = SQLAlchemy(app)

# Rest of the code...


# Define the database models
class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(50), unique=True, nullable=False)
  password = db.Column(db.String(50), nullable=False)
  api_key = db.Column(db.String(100))
  secret_key = db.Column(db.String(100))

  def __repr__(self):
    return f"User('{self.username}', '{self.api_key}', '{self.secret_key}')"


# Rest of the code...


# Define the routes
@app.route('/')
def index():
  if 'username' in session:
    return redirect('/dashboard')
  return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
  if 'username' in session:
    return redirect('/dashboard')

  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    api_key = request.form['api_key']
    secret_key = request.form['secret_key']

    user = User(username=username,
                password=password,
                api_key=api_key,
                secret_key=secret_key)
    db.session.add(user)
    db.session.commit()
    session['username'] = username
    return redirect('/dashboard')

  return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
  if 'username' in session:
    return redirect('/dashboard')

  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username, password=password).first()
    if user:
      session['username'] = username
      return redirect('/dashboard')

  return render_template('login.html')


@app.route('/dashboard')
def dashboard():
  if 'username' in session:
    return render_template('dashboard.html')
  else:
    return redirect('/login')


@app.route('/set_trading_volume', methods=['POST'])
def set_trading_volume():
  volume = request.form.get('volume')
  if volume:
    global TRADING_VOLUME
    TRADING_VOLUME = int(volume)
    return "Trading volume updated successfully"
  else:
    return "Invalid trading volume"


@app.route('/logout')
def logout():
  session.pop('username', None)
  return redirect('/')


# Rest of the code...

# Initialize spreads and prices
spreads = [0.7]
prices = {
  'SUSHI/USDT': 1000,
  'LINK/USDT': 1,
  'SOL/USDT': 0.01,
  'BTC/USDT': 0.0001,
  'AAVE/USDT': 10,
  'SOL/USDT': 0.01,
  'DOGE/USDT': 100
}

# Time between each quote & arb percent
waitTime = 5
ARB_THRESHOLD = 0.7
TRADING_VOLUME = 1000  # or whatever value you want to use

# Write the setup.sh script to file
with open('setup.sh', 'w') as f:
  f.write('#!/bin/bash\n')
  f.write('echo "Setting up the environment..."\n')
  f.write('mkdir data\n')
  f.write('echo "Done."\n')

# Call the setup.sh script
subprocess.call(['bash', 'setup.sh'])


def run():
  PORT = 8000

  Handler = http.server.SimpleHTTPRequestHandler

  with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    print(
      f"Click here to access the server: https://myproject.{os.getenv('REPL_OWNER')}.{os.getenv('REPL_SLUG')}.repl.co/"
    )
    httpd.serve_forever()


async def main():
  while True:
    task1 = loop.create_task(get_quote("SUSHI/USDT"))
    task2 = loop.create_task(get_quote("LINK/USDT"))
    task3 = loop.create_task(get_quote("SOL/USDT"))
    task4 = loop.create_task(get_quote("BTC/USDT"))
    task5 = loop.create_task(get_quote("AAVE/USDT"))
    task6 = loop.create_task(get_quote("SOL/USDT"))
    task7 = loop.create_task(get_quote("DOGE/USDT"))
    # Wait for the tasks to finish
    await asyncio.wait([task1, task2, task3, task4, task5, task6, task7])
    await check_arb()
    # Wait for the value of waitTime between each quote request
    await asyncio.sleep(waitTime)

import requests

async def get_quote(symbol: str):
    '''
    Get quote data from Alpaca API
    '''

    try:
        # Make the request
        quote = requests.get(
            'https://api.alpaca.markets/v2/assets?asset_class=crypto',
            headers=HEADERS)
        
        # Check if the request was successful (status code 200)
        if quote.status_code == 200:
            data = quote.json()
            prices = {item['symbol']: item['price'] for item in data}
            return prices.get(symbol)
        else:
            print("Undesirable response from Alpaca! {}".format(quote.json()))
            return None

    except Exception as e:
        print("There was an issue getting trade quote from Alpaca: {0}".format(e))
        return None

async def check_arb():
  '''
    Check to see if a profitable arbitrage opportunity exists
    '''

  # set minimum profit threshold to avoid losses
  MIN_PROFIT = 0.7

  SUSHI = prices['SUSHI/USDT']
  LINK = prices['LINK/USDT']
  SOL = prices['SOL/USDT']
  BTC = prices['BTC/USDT']
  AAVE = prices['AAVE/USDT']
  SOL = prices['SOL/USDT']
  DOGE = prices['DOGE/USDT']
  DIV1 = SUSHI / LINK
  DIV2 = SUSHI / SOL
  DIV3 = SUSHI / BTC
  DIV4 = SUSHI / AAVE
  DIV5 = SUSHI / SOL
  DIV6 = SUSHI / DOGE
  SPREAD1 = abs(DIV1 - DIV2)
  SPREAD2 = abs(DIV1 - DIV3)
  SPREAD3 = abs(DIV1 - DIV4)
  SPREAD4 = abs(DIV1 - DIV5)
  SPREAD5 = abs(DIV1 - DIV6)
  BUY_SUSHI = 1000 / SUSHI
  BUY_LINK = 1000 / LINK
  BUY_SOL = 1000 / SOL
  BUY_BTC = 1000 / BTC
  BUY_AAVE = 1000 / AAVE
  BUY_SOL = 1000 / SOL
  BUY_DOGE = 1000 / DOGE
  SELL_LINK = BUY_SUSHI / DIV1
  SELL_SOL = BUY_SUSHI / DIV2
  SELL_BTC = BUY_SUSHI / DIV3
  SELL_AAVE = BUY_SUSHI / DIV4
  SELL_SOL = BUY_SUSHI / DIV5
  SELL_DOGE = BUY_SUSHI / DIV6

  if SPREAD1 > ARB_THRESHOLD:
    if DIV1 > DIV2:
      profit = (BUY_SUSHI - (BUY_LINK * DIV2)) * TRADING_VOLUME
      if profit > MIN_PROFIT:
        print(
          "Buy LINK with SUSHI on exchange A and sell LINK for SUSHI on exchange B"
        )
        print("Profit: ", profit)
    else:
      profit = ((BUY_LINK * DIV1) - BUY_SUSHI) * TRADING_VOLUME
      if profit > MIN_PROFIT:
        print(
          "Buy LINK with SUSHI on exchange B and sell LINK for SUSHI on exchange A"
        )
        print("Profit: ", profit)

  if SPREAD2 > ARB_THRESHOLD:
    if DIV1 > DIV3:
      profit = (BUY_SUSHI - (BUY_BTC * DIV3)) * TRADING_VOLUME
      if profit > MIN_PROFIT:
        print(
          "Buy BTC with SUSHI on exchange A and sell BTC for SUSHI on exchange B"
        )
        print("Profit: ", profit)
    else:
      profit = ((BUY_BTC * DIV1) - BUY_SUSHI) * TRADING_VOLUME
      if profit > MIN_PROFIT:
        print(
          "Buy BTC with SUSHI on exchange B and sell BTC for SUSHI on exchange A"
        )
        print("Profit: ", profit)

  if SPREAD3 > ARB_THRESHOLD:
    if DIV1 > DIV4:
      profit = (BUY_SUSHI - (BUY_AAVE * DIV4)) * TRADING_VOLUME
      if profit > MIN_PROFIT:
        print(
          "Buy AAVE with SUSHI on exchange A and sell AAVE for SUSHI on exchange B"
        )
        print("Profit: ", profit)
    else:
      profit = ((BUY_AAVE * DIV1) - BUY_SUSHI) * TRADING_VOLUME
      if profit > MIN_PROFIT:
        print(
          "Buy AAVE with SUSHI on exchange B and sell BTC for AAVE on exchange A"
        )
        print("Profit: ", profit)

    if SPREAD4 > ARB_THRESHOLD:
      if DIV1 > DIV5:
        profit = (BUY_SUSHI - (BUY_SOL * DIV5)) * TRADING_VOLUME
        if profit > MIN_PROFIT:
          print(
            "Buy SOL with SUSHI on exchange A and sell SOL for SUSHI on exchange B"
          )
          print("Profit: ", profit)
      else:
        profit = ((BUY_SOL * DIV1) - BUY_SUSHI) * TRADING_VOLUME
        if profit > MIN_PROFIT:
          print(
            "Buy SOL with SUSHI on exchange B and sell SOL for SUSHI on exchange A"
          )
          print("Profit: ", profit)

    if SPREAD5 > ARB_THRESHOLD:
      if DIV1 > DIV6:
        profit = (BUY_SUSHI - (BUY_DOGE * DIV6)) * TRADING_VOLUME
        if profit > MIN_PROFIT:
          print(
            "Buy DOGE with SUSHI on exchange A and sell DOGE for SUSHI on exchange B"
          )
          print("Profit: ", profit)
      else:
        profit = ((BUY_DOGE * DIV1) - BUY_SUSHI) * TRADING_VOLUME
        if profit > MIN_PROFIT:
          print(
            "Buy DOGE with SUSHI on exchange B and sell DOGE for SUSHI on exchange A"
          )
          print("Profit: ", profit)


# Function for placing orders


def post_Alpaca_order(symbol, qty, side):
  '''
  Post an order to Alpaca
  '''
  try:
    order = requests.post('{0}/v2/orders'.format(base_url),
                          headers=HEADERS,
                          json={
                            'symbol': symbol,
                            'qty': qty,
                            'side': side,
                            'type': 'market',
                            'time_in_force': 'gtc',
                          })
    return order
  except Exception as e:
    print("There was an issue posting order to Alpaca: {0}".format(e))
    return False


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()


# Define the routes
@app.route('/')
def index():
  return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']

    # Check if the username and password are valid
    user = User.query.filter_by(username=username, password=password).first()
    if user:
      session['user_id'] = user.id
      return redirect('/dashboard')
    else:
      return render_template('login.html',
                             error='Invalid username or password')
  else:
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']

    # Create a new user
    if create_user(username, password):
      return redirect('/login')
    else:
      return render_template('register.html', error='Username already taken')
  else:
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
  # Check if the user is logged in
  if 'user_id' in session:
    return render_template('dashboard.html')
  else:
    return redirect('/login')


alpaca_client = alpaca.REST(alpaca_api_key, alpaca_secret_key, alpaca_base_url)

# Rest of

# Split the remaining profit and distribute to Alpaca users
alpaca_users = User.query.all()  # Retrieve all users from the database
num_users = len(alpaca_users)
if num_users > 0:
  remaining_profit = profit * 0.7  # 70% of the profit goes to Alpaca users
  individual_profit = remaining_profit / num_users
  individual_profit = round(individual_profit, 2)  # Round to 2 decimal places

  for user in alpaca_users:
    # Perform profit split for each user
    user_api_key = user.api_key
    user_secret_key = user.secret_key
    user_base_url = 'https://api.alpaca.markets'  # Use paper trading API for testing
    user_alpaca_client = alpaca.REST(user_api_key, user_secret_key,
                                     user_base_url)
    user_alpaca_client.submit_order(symbol=base_symbol,
                                    qty=individual_profit,
                                    side='buy',
                                    type='market',
                                    time_in_force='gtc')

# ...


def send_to_internal_wallet(amount):
  binance_api_key = 'your_binance_api_key'
  binance_secret_key = 'your_binance_secret_key'
  binance_client = Client(binance_api_key, binance_secret_key)

  internal_wallet_address = 'TLGcdTwtdoPgUt4iwvrFb2obipbXcvWAxM'  # Replace with the admin's internal wallet address
  usdt_symbol = 'USDT'

  # Generate a unique memo for the transaction
  memo = 'Profit distribution'

  # Create the withdrawal request to send funds to the admin's internal wallet
  binance_client.withdraw(asset=usdt_symbol,
                          address=internal_wallet_address,
                          amount=amount,
                          name='',
                          network='',
                          addressTag='',
                          transactionFeeFlag=False,
                          withdrawOrderId='',
                          timestamp=None,
                          recvWindow=None,
                          transactionType='INTERNAL_TRANSFER',
                          memo=memo)
