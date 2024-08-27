import os
import json
import pyotp
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from tabulate import tabulate
from pymongo import MongoClient
from SmartApi.smartConnect import SmartConnect

# MongoDB connection setup
mongo_client = MongoClient("mongodb+srv://SupremeRahul:***REDACTED***@clusternse.wpf8cel.mongodb.net/")
db = mongo_client['AlgoTrading']
collection = db['BSE']

# AngelOne API credentials
username = '***REDACTED***'
password = '***REDACTED***'
api_key = '***REDACTED***'
totp_key = '***REDACTED***'  # TOTP key for 2FA

# Generate TOTP
totp = pyotp.TOTP(totp_key).now()

# Authenticate with Angel One API
smart_connect = SmartConnect(api_key=api_key)
data = smart_connect.generateSession(username, password, totp)

if data['status']:
    refresh_token = data['data']['refreshToken']
    access_token = data['data']['jwtToken']
else:
    raise Exception(f"Login failed: {data['message']}")


# Function to fetch dividend data
def fetch_dividend_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr')

    data = []
    for row in rows:
        columns = row.find_all('td')
        if len(columns) >= 8:
            company_name = columns[0].get_text(strip=True).replace('$', '')
            stock_symbol = columns[1].get_text(strip=True) + '-EQ'
            stock_code = columns[2].get_text(strip=True)
            ex_dividend_date = columns[3].get_text(strip=True)
            record_date = columns[4].get_text(strip=True)
            dividend_type = columns[5].get_text(strip=True)
            dividend_amount = columns[6].get_text(strip=True)
            cmp = columns[7].get_text(strip=True)

            data.append(
                [company_name, stock_symbol, stock_code, ex_dividend_date, record_date, dividend_type, dividend_amount,
                 cmp])

    return data


# Fetch dividend data
url = 'https://www.chittorgarh.com/report/stock-dividend/135/'
dividend_data = fetch_dividend_data(url)

# Prompt user for investment amount
investment_amount = float(input("Enter your investment amount: "))

# Prepare data for display
IssuerCompany, share_symbols, StockCode, Ex_DividendDate, RecordDate, DividendType, DividendAmount, CMP = zip(
    *dividend_data)

Qty = []
PotentialDividend = []
InvestAmount = []
DividendStatus = []

current_date = datetime.now().date()

for i in range(len(CMP)):
    current_price = float(CMP[i])
    qty = investment_amount // current_price

    try:
        potential_dividend = qty * float(DividendAmount[i])
    except ValueError:
        potential_dividend = 'N/A'

    invest_amount = qty * current_price

    # Determine dividend status
    ex_date = datetime.strptime(Ex_DividendDate[i], '%b %d, %Y').date()
    if current_date >= ex_date:
        status = 'Missed'
    else:
        status = 'Active'

    Qty.append(qty)
    PotentialDividend.append(f"{potential_dividend:.2f}" if potential_dividend != 'N/A' else potential_dividend)
    InvestAmount.append(f"{invest_amount:.2f}")
    DividendStatus.append(status)

# Fetch LTP data from Angel One API and update the table
ltp_prices = []

for symbol in share_symbols:
    print(f"Symbol: {symbol}")

    document = collection.find_one({"symbol": symbol})
    if document:
        token = document['Security Code']
        print(f"Token: {token}")
        try:
            ltp_data = smart_connect.ltpData('NSE', symbol, token)
            ltp_prices.append(ltp_data['data']['ltp'])
        except Exception as e:
            ltp_prices.append('N/A')
            print(f"Error fetching LTP for {symbol}: {e}")
    else:
        ltp_prices.append('N/A')
        print(f"Error: Token for {symbol} not found in the database.")

# Create a table using tabulate
table_data = list(
    zip(IssuerCompany, share_symbols, Ex_DividendDate, DividendStatus, DividendAmount, CMP, Qty, PotentialDividend,
        InvestAmount, ltp_prices))
headers = ["Company Name", "Stock Symbol", "Ex-Date", "Dividend Status", "Dividend Amount", "Current Price", "Qty",
           "Potential Dividend", "Invest Amount", "LTP Price"]

print(tabulate(table_data, headers=headers, tablefmt="pretty"))
