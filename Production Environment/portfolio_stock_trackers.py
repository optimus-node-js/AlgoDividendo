from pymongo import MongoClient
from datetime import datetime
import pyotp
from SmartApi.smartConnect import SmartConnect
from fastapi import HTTPException



# Function to generate the TOTP for 2FA
def generate_totp(totp_secret):
    return pyotp.TOTP(totp_secret).now()



# Function to login and fetch portfolio data
def login_and_fetch_portfolio(apiKey, client_code, password, totp_secret):
    obj = SmartConnect(api_key=apiKey)
    try:
        # Login and get session details
        data = obj.generateSession(client_code, password, generate_totp(totp_secret))
        refreshToken = data['data']['refreshToken']

        # Fetch the user's profile and name
        NameOfUser = obj.getProfile(refreshToken)['data']['name']
        user_name = ' '.join(NameOfUser.split())

        # Fetch the portfolio details dynamically (all holdings)
        portfolio = obj.allholding()['data']['holdings']  # Fetch holdings dynamically

        return obj, refreshToken, portfolio, user_name

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error during login: {e}")


# MongoDB connection string
mongo_uri = "mongodb+srv://SupremeRahul:***REDACTED***@clusternse.wpf8cel.mongodb.net/"
client = MongoClient(mongo_uri)
db = client['SmartAPI']
collection = db['Angelone Portfolio Stocks Tracker']

# Credentials for multiple users
credentials = [
    {
        "client_code": "***REDACTED***",  # This is both username and client code
        "password": "***REDACTED***",
        "apikey": "***REDACTED***",
        "totp_secret": "***REDACTED***"
    },
    # Add more users as needed with their credentials
]

# Iterate over the list of users and fetch their stock data
for credential in credentials:
    client_code = credential['client_code']
    password = credential['password']
    apiKey = credential['apikey']
    totp_secret = credential['totp_secret']

    # Login and fetch portfolio data dynamically
    obj, refreshToken, stock_data, client_name = login_and_fetch_portfolio(apiKey, client_code, password, totp_secret)
    print(stock_data)
    # Get today's date in 'dd-mm-yyyy' format
    today_date = datetime.now().strftime('%d-%m-%Y')

    # Iterate over stock data to insert or update records in MongoDB
    for stock in stock_data:
        stock_name = stock['tradingsymbol']
        new_entry = {
            "date": today_date,
            "exchange": stock['exchange'],
            "quantity": stock['quantity'],
            "realisedquantity": stock['realisedquantity'],
            "authorisedquantity": stock['authorisedquantity'],
            "product": stock['product'],
            "averageprice": stock['averageprice'],
            "symboltoken": stock['symboltoken'],
            "profitandloss": stock['profitandloss'],
            "pnlpercentage": stock['pnlpercentage']
        }

        # Check if the stock exists in the user's portfolio
        query = {"ClientCode": client_code, "PortfolioStocks.stockName": stock_name}
        existing_stock = collection.find_one(query)

        # Ensure ClientName is added on every operation
        update_data = {
            "$set": {"ClientCode": client_code, "ClientName": client_name}
        }

        if existing_stock:
            # Check if today's entry exists for the stock
            query_with_date = {"ClientCode": client_code, "PortfolioStocks.stockName": stock_name,
                               "PortfolioStocks.entries.date": today_date}
            if collection.find_one(query_with_date):
                # Update the existing entry for today's date
                update_data["$set"]["PortfolioStocks.$[stock].entries.$[entry]"] = new_entry
                collection.update_one(
                    {"ClientCode": client_code, "PortfolioStocks.stockName": stock_name,
                     "PortfolioStocks.entries.date": today_date},
                    update_data,
                    array_filters=[{"stock.stockName": stock_name}, {"entry.date": today_date}]
                )
            else:
                # Insert a new entry for today's date
                update_data["$push"] = {"PortfolioStocks.$[stock].entries": new_entry}
                collection.update_one(
                    {"ClientCode": client_code, "PortfolioStocks.stockName": stock_name},
                    update_data,
                    array_filters=[{"stock.stockName": stock_name}]
                )
        else:
            # Add new stock with today's entry
            new_stock_entry = {
                "stockName": stock_name,
                "entries": [new_entry]
            }
            update_data["$push"] = {"PortfolioStocks": new_stock_entry}
            collection.update_one(
                {"ClientCode": client_code},
                update_data,
                upsert=True
            )

print("Stock data updated successfully for all users.")
