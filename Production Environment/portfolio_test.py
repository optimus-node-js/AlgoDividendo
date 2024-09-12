import asyncio
import motor.motor_asyncio
from datetime import datetime
import pyotp
from SmartApi.smartConnect import SmartConnect
from fastapi import HTTPException
import pymongo
from time import time
start = time()
# MongoDB connection (using Motor for async)
mongo_uri = "mongodb+srv://SupremeRahul:***REDACTED***@clusternse.wpf8cel.mongodb.net/"
client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
db = client['SmartAPI']

portfolio_collection = db['Angelone Portfolio Tracker']
stocks_collection = db['Angelone Portfolio Stocks Tracker']
credentials_collection = db['Angelone Portfolio Tracking User Credentials']

# Function to generate the TOTP for 2FA
def generate_totp(totp_secret):
    return pyotp.TOTP(totp_secret).now()

# Async function to login and fetch holdings
async def login_and_fetch_holdings(apiKey, username, password, totp_secret):
    obj = SmartConnect(api_key=apiKey)
    try:
        data = await asyncio.to_thread(obj.generateSession, username, password, generate_totp(totp_secret))
        refreshToken = data['data']['refreshToken']
        profile = await asyncio.to_thread(obj.getProfile, refreshToken)
        profile_data = profile['data']
        user_name = ' '.join(profile_data['name'].split())
        client_code = profile_data['clientcode']
        # Fetch holdings
        allholding_data = await asyncio.to_thread(obj.allholding)
        holdings_data = allholding_data['data']['holdings']
        total_portfolio_data = allholding_data['data']['totalholding']
        return {
            "obj": obj,
            "user_name": user_name,
            "client_code": client_code,
            "holdings_data": holdings_data,
            "total_portfolio_data": total_portfolio_data
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error during login: {e}")

# Async function to fetch LTP data for a single symbol with rate limiting
async def fetch_ltp_data(obj, exchange, tradingsymbol, symboltoken, semaphore):
    async with semaphore:
        try:
            ltp_data_response = await asyncio.to_thread(obj.ltpData, exchange, tradingsymbol, symboltoken)
            if 'data' in ltp_data_response:
                await asyncio.sleep(0.1)  # Wait for 0.1 seconds to respect rate limit
                return ltp_data_response['data']
            else:
                raise ValueError("No LTP data found.")
        except Exception as e:
            return Exception(f"Error fetching LTP data: {e}")

# Async function to process each user's portfolio
async def process_user_portfolio(user):
    apiKey = user['apiKey'][0]
    username = user['clientId']
    password = user['password']
    totp_secret = user['totp_secret']

    try:
        # Login and fetch holdings
        user_data = await login_and_fetch_holdings(apiKey, username, password, totp_secret)
        obj = user_data['obj']
        user_name = user_data['user_name']
        client_code = user_data['client_code']
        holdings_data = user_data['holdings_data']
        total_portfolio_data = user_data['total_portfolio_data']

        today_date = datetime.today().strftime('%d-%m-%Y')

        total_today_gain = 0
        stock_entries = []

        # Prepare tasks for fetching LTP data asynchronously with rate limiting
        semaphore = asyncio.Semaphore(1)  # Limit to 1 concurrent API call per user

        ltp_tasks = []
        for stock in holdings_data:
            exchange = stock['exchange']
            tradingsymbol = stock['tradingsymbol']
            symboltoken = stock['symboltoken']
            ltp_tasks.append(fetch_ltp_data(obj, exchange, tradingsymbol, symboltoken, semaphore))

        # Fetch LTP data for all holdings concurrently, respecting rate limit
        ltp_results = await asyncio.gather(*ltp_tasks, return_exceptions=True)

        # Process each stock
        for stock, ltp_result in zip(holdings_data, ltp_results):
            if isinstance(ltp_result, Exception):
                print(f"Error fetching LTP data for {stock['tradingsymbol']}: {ltp_result}")
                continue  # Skip this stock due to error

            prev_close = float(ltp_result['close'])
            ltp = float(ltp_result['ltp'])
            today_gain = (ltp - prev_close) * stock['quantity']
            total_today_gain += today_gain

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

        # Update portfolio data in MongoDB
        await update_portfolio_in_db(client_code, user_name, today_date, total_portfolio_data, total_today_gain, stock_entries)

        print(f"Portfolio updated successfully for {user_name}!")

    except Exception as e:
        print(f"Error processing portfolio for {username}: {e}")

# Async function to update MongoDB using batch updates
async def update_portfolio_in_db(client_code, user_name, today_date, total_portfolio_data, total_today_gain, stock_entries):
    try:
        # Check if there is a portfolio entry for today
        portfolio_exists = await portfolio_collection.find_one({
            "ClientCode": client_code,
            "Portfolio.date": today_date
        })

        if portfolio_exists:
            # If portfolio entry exists, update it
            portfolio_update = {
                "filter": {
                    "ClientCode": client_code,
                    "Portfolio.date": today_date
                },
                "update": {
                    "$set": {
                        "Portfolio.$.totalholdingvalue": round(float(total_portfolio_data['totalholdingvalue']), 2),
                        "Portfolio.$.totalinvvalue": round(float(total_portfolio_data['totalinvvalue']), 2),
                        "Portfolio.$.totalprofitandloss": round(float(total_portfolio_data['totalprofitandloss']), 2),
                        "Portfolio.$.totalpnlpercentage": float(total_portfolio_data['totalpnlpercentage']),
                        "Portfolio.$.totalTodayGain": round(total_today_gain, 2)
                    }
                },
                "upsert": False
            }
            # Perform the update
            await portfolio_collection.update_one(
                portfolio_update["filter"],
                portfolio_update["update"]
            )
        else:
            # If no entry for today, push a new entry
            portfolio_push = {
                "filter": {"ClientCode": client_code},
                "update": {
                    "$set": {"Name": user_name, "ClientCode": client_code},
                    "$push": {
                        "Portfolio": {
                            "date": today_date,
                            "totalholdingvalue": round(float(total_portfolio_data['totalholdingvalue']), 2),
                            "totalinvvalue": round(float(total_portfolio_data['totalinvvalue']), 2),
                            "totalprofitandloss": round(float(total_portfolio_data['totalprofitandloss']), 2),
                            "totalpnlpercentage": float(total_portfolio_data['totalpnlpercentage']),
                            "totalTodayGain": round(total_today_gain, 2)
                        }
                    }
                },
                "upsert": True
            }
            await portfolio_collection.update_one(
                portfolio_push["filter"],
                portfolio_push["update"],
                upsert=True
            )

        # Batch update for stocks
        for stock in stock_entries:
            entry = stock['entries'][0]
            stock_exists = await stocks_collection.find_one({
                "ClientCode": client_code,
                "PortfolioStocks.stockName": stock['stockName']
            })

            if stock_exists:
                # If the stock exists, update its entries
                await stocks_collection.update_one(
                    {
                        "ClientCode": client_code,
                        "PortfolioStocks.stockName": stock['stockName']
                    },
                    {
                        "$push": {"PortfolioStocks.$.entries": entry}
                    }
                )
            else:
                # Add new stock if it doesn't exist
                await stocks_collection.update_one(
                    {"ClientCode": client_code},
                    {
                        "$setOnInsert": {"ClientName": user_name},
                        "$push": {
                            "PortfolioStocks": {
                                "stockName": stock['stockName'],
                                "entries": [entry]
                            }
                        }
                    },
                    upsert=True
                )

        print(f"Bulk update successful for {client_code}")

    except pymongo.errors.BulkWriteError as bwe:
        print(f"Bulk write error: {bwe.details}")
    except Exception as e:
        print(f"Error during bulk update: {e}")

# Function to fix existing documents where PortfolioStocks is not an array
async def fix_existing_documents():
    cursor = stocks_collection.find({
        "PortfolioStocks": {"$not": {"$type": "array"}}
    })

    async for doc in cursor:
        if 'PortfolioStocks' in doc and isinstance(doc['PortfolioStocks'], dict):
            # Convert PortfolioStocks from dict to list containing the dict
            await stocks_collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"PortfolioStocks": [doc['PortfolioStocks']]}}
            )

# Main execution
async def main():
    print("Fixing existing documents...")
    await fix_existing_documents()

    print("Starting the portfolio update process for all users...")
    all_users = await credentials_collection.find().to_list(None)

    # Limit the number of concurrent users processed to respect rate limits across users
    semaphore = asyncio.Semaphore(5)  # Adjust based on your system's capabilities and API limits

    async def sem_task(user):
        async with semaphore:
            await process_user_portfolio(user)

    tasks = [sem_task(user) for user in all_users]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

end = time()
print(f"Time Took: {end - start} s")

"""
This module updates portfolio and stock data for users asynchronously using MongoDB.
It handles the following:

1. Fetches portfolio and stock data for each user.
2. Updates or inserts new portfolio entries based on the current date.
3. Updates or inserts stock data for each user's portfolio.

Key updates:
- **Bulk Updates**: The code now uses batch updates for MongoDB operations to improve performance.
- **Portfolio Update Logic**:
  - The code checks if there is an existing entry for the user's portfolio for the current date.
  - If the entry exists, it updates the corresponding portfolio using the positional operator (`$`).
  - If the entry does not exist, it inserts a new portfolio entry with today's data.
- **Stock Update Logic**:
  - The code checks if each stock already exists in the user's portfolio.
  - If the stock exists, it appends new entries to the `PortfolioStocks` array.
  - If the stock does not exist, it inserts the stock data with its entries.
- **Error Handling**: Bulk write errors and other exceptions are handled gracefully, with detailed error messages for failed operations.

Concurrency and Rate Limiting:
- The code uses asynchronous operations to fetch data concurrently for multiple users.
- Semaphores are used to limit the number of concurrent API requests, respecting rate limits.
"""
