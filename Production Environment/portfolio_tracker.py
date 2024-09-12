import time
from pymongo import MongoClient, UpdateOne
from datetime import datetime, timedelta
import pyotp
from SmartApi.smartConnect import SmartConnect
from fastapi import HTTPException
import concurrent.futures
# MongoDB connection
mongo_uri = "mongodb+srv://SupremeRahul:***REDACTED***@clusternse.wpf8cel.mongodb.net/"
client = MongoClient(mongo_uri)
db = client['SmartAPI']

portfolio_collection = db['Angelone Portfolio Tracker']
stocks_collection = db['Angelone Portfolio Stocks Tracker']
credentials_collection = db['Angelone Portfolio Tracking User Credentials']

# Function to generate the TOTP for 2FA
def generate_totp(totp_secret):
    return pyotp.TOTP(totp_secret).now()


# Login and fetch portfolio data
def login_and_fetch_portfolio(apiKey, username, password, totp_secret):
    obj = SmartConnect(api_key=apiKey)
    try:
        print("Logging in and fetching portfolio data...")
        data = obj.generateSession(username, password, generate_totp(totp_secret))
        refreshToken = data['data']['refreshToken']
        NameOfUser = obj.getProfile(refreshToken)['data']['name']
        client_code = obj.getProfile(refreshToken)['data']['clientcode']
        user_name = ' '.join(NameOfUser.split())
        print(f"Successfully logged in as {user_name} with client code {client_code}")
        return obj, refreshToken, user_name, client_code
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error during login: {e}")


# Fetch dates function
def fetch_dates():
    print("Fetching dates for historical OHLC data...")
    now = datetime.now()
    if now.time() >= datetime.strptime("00:00", "%H:%M").time() and now.time() <= datetime.strptime("09:14",
                                                                                                    "%H:%M").time():
        from_date = now - timedelta(days=3)
        to_date = now - timedelta(days=2)
    else:
        from_date = now - timedelta(days=2)
        to_date = now - timedelta(days=1)

    fixed_time_1 = "09:15"
    fixed_time_2 = "15:30"
    print(f"From date: {from_date.strftime('%Y-%m-%d')} To date: {to_date.strftime('%Y-%m-%d')}")
    return [from_date.strftime("%Y-%m-%d ") + fixed_time_1, to_date.strftime("%Y-%m-%d ") + fixed_time_2]


# Fetch historical OHLC data with rate limiting and detailed logging
def fetch_historical_ohlc(obj, symbol, token, from_date, to_date):
    try:
        print(f"Fetching OHLC data for {symbol}...")
        time.sleep(0.5)  # Slowing down the request to reduce rate-limit issues
        historical_params = {
            "exchange": "NSE",
            "symboltoken": token,
            "interval": "ONE_DAY",
            "fromdate": from_date,
            "todate": to_date
        }
        response = obj.getCandleData(historical_params)
        if 'data' in response and len(response['data']) > 0:
            print(f"Previous close for {symbol}: {response['data'][0][4]}")
            return response['data'][0][4]  # Return the closing price
        else:
            raise ValueError(f"No historical data found for {symbol}")
    except Exception as e:
        print(f"Error fetching OHLC data for {symbol}: {e}")
        return {"error": str(e)}


# Backoff mechanism for handling API rate-limit errors
def fetch_with_backoff(api_call, retries=5, backoff_factor=1):
    for i in range(retries):
        try:
            return api_call()
        except Exception as e:
            if "Access denied because of exceeding access rate" in str(e):
                wait_time = backoff_factor * (2 ** i)  # Exponential backoff
                print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("Failed after maximum retries")


# Update portfolio data with detailed logging and handling rate limit issues

# Update portfolio data with detailed logging and handling rate limit issues
def update_portfolio_data(obj, user_name, client_code):
    today_date = datetime.today().strftime('%d-%m-%Y')
    previous_day, today = fetch_dates()

    def fetch_holdings():
        return obj.allholding()

    # Fetch holdings data with backoff
    try:
        print(f"Fetching user holdings for {user_name}...")
        allholding_data = fetch_with_backoff(fetch_holdings)
        holdings_data = allholding_data['data']['holdings']
        total_portfolio_data = allholding_data['data']['totalholding']
        print(f"Holdings fetched: {len(holdings_data)} stocks")
    except Exception as e:
        print(f"Error fetching holdings data for {user_name}: {e}")
        return

    total_today_gain = 0
    stock_entries = []

    # Iterate through user's holdings
    for stock in holdings_data:
        print(f"Processing stock: {stock['tradingsymbol']}")
        prev_close = fetch_historical_ohlc(obj, stock['tradingsymbol'], stock['symboltoken'], previous_day, today)

        if isinstance(prev_close, dict) and 'error' in prev_close:
            print(f"Skipping stock {stock['tradingsymbol']} due to OHLC fetch error")
            continue

        today_gain = (stock['ltp'] - prev_close) * stock['quantity']
        total_today_gain += today_gain

        print(f"Today's gain for {stock['tradingsymbol']}: {today_gain}")

        stock_entries.append({
            "stockName": stock['tradingsymbol'],
            "entries": [{
                "date": today_date,
                "exchange": stock['exchange'],
                "quantity": stock['quantity'],
                "realisedquantity": stock['realisedquantity'],
                "authorisedquantity": stock['authorisedquantity'],
                "product": stock['product'],
                "averageprice": stock['averageprice'],
                "symboltoken": stock['symboltoken'],
                "profitandloss": stock['profitandloss'],
                "pnlpercentage": stock['pnlpercentage'],
                "todayGain": round(today_gain, 2)
            }]
        })

        # Sleep to respect rate limit in each iteration
        time.sleep(0.5)

    print(f"Total portfolio gain today for {user_name}: {total_today_gain}")

    # Check if the portfolio entry already exists for today before inserting
    portfolio_exists = portfolio_collection.find_one({
        "ClientCode": client_code,
        "Portfolio.date": today_date
    })

    if not portfolio_exists:
        # Use pre-calculated total values from the API response
        portfolio_collection.update_one(
            {"ClientCode": client_code},
            {
                "$set": {"ClientCode": client_code, "Name": user_name},
                "$push": {
                    "Portfolio": {
                        "date": today_date,
                        "totalholdingvalue": round(total_portfolio_data['totalholdingvalue'], 2),
                        "totalinvvalue": round(total_portfolio_data['totalinvvalue'], 2),
                        "totalprofitandloss": round(total_portfolio_data['totalprofitandloss'], 2),
                        "totalpnlpercentage": total_portfolio_data['totalpnlpercentage'],
                        "totalTodayGain": round(total_today_gain, 2)
                    }
                }
            },
            upsert=True
        )
    else:
        print(f"Portfolio data for {today_date} already exists for {user_name}, skipping insertion.")

    # Check and update PortfolioStocks, including adding the client name
    bulk_updates = []
    for stock in stock_entries:
        for entry in stock['entries']:
            stock_exists = stocks_collection.find_one({
                "ClientCode": client_code,
                "PortfolioStocks.stockName": stock['stockName']
            })

            if stock_exists:
                # Update the stock if it exists by pushing the entry
                bulk_updates.append(UpdateOne(
                    {"ClientCode": client_code, "PortfolioStocks.stockName": stock['stockName']},
                    {
                        "$push": {"PortfolioStocks.$.entries": entry}
                    }
                ))
            else:
                # Insert new stock if it doesn't exist, adding the client name here
                bulk_updates.append(UpdateOne(
                    {"ClientCode": client_code},
                    {
                        "$setOnInsert": {"ClientName": user_name},  # Add the client name when inserting
                        "$push": {
                            "PortfolioStocks": {
                                "stockName": stock['stockName'],
                                "entries": [entry]
                            }
                        }
                    },
                    upsert=True
                ))

    # Execute bulk write for stock updates
    if bulk_updates:
        stocks_collection.bulk_write(bulk_updates)
    else:
        print(f"No new stock entries to update for {user_name}")

    return "Portfolio updated successfully!"


# Function to handle each user's portfolio update in a separate thread
def process_user_portfolio(user):
    apiKey = user['apiKey'][0]  # Use only the first API key
    username = user['clientId']
    password = user['password']
    totp_secret = user['totp_secret']

    try:
        # Login and fetch data for each user
        obj, refreshToken, user_name, client_code = login_and_fetch_portfolio(apiKey, username, password, totp_secret)
        result = update_portfolio_data(obj, user_name, client_code)
        print(result)
    except Exception as e:
        print(f"Error processing portfolio for {user['clientName']}: {e}")
# Main execution for iterating through all users in the credentials collection
if __name__ == "__main__":
    try:
        print("Starting the portfolio update process for all users...")

        # Fetch all user credentials
        all_users = credentials_collection.find()

        # Use ThreadPoolExecutor for multi-threading
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_user_portfolio, user) for user in all_users]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()  # Ensure any raised exceptions are caught
                except Exception as e:
                    print(f"Error: {e}")

    except Exception as e:
        print(f"An error occurred while iterating through users: {e}")

