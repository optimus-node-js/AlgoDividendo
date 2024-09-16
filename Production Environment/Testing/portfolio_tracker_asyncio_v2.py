import asyncio
import motor.motor_asyncio
from datetime import datetime, timedelta
import pyotp
from SmartApi.smartConnect import SmartConnect
from concurrent.futures import ProcessPoolExecutor
from time import time
import random

# MongoDB connection (using Motor for async)
mongo_uri = "mongodb+srv://SupremeRahul:***REDACTED***@clusternse.wpf8cel.mongodb.net/"
client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
db = client['SmartAPI']

portfolio_collection = db['PortfolioHolding_test']
stocks_collection = db['StockHolding_test']
credentials_collection = db['Angelone Portfolio Tracking User Credentials']

# Simulated list of NSE trading holidays
TRADING_HOLIDAYS = ["2024-03-29", "2024-08-15", "2024-10-02"]

def is_trading_holiday(date):
    return date.strftime("%Y-%m-%d") in TRADING_HOLIDAYS

def find_previous_working_day(date):
    while date.weekday() in [5, 6] or is_trading_holiday(date):  # Saturday=5, Sunday=6
        date -= timedelta(days=1)
    return date

def fetch_dates():
    now = datetime.now()
    day_of_week = now.weekday()
    fixed_time_1 = "09:15"
    fixed_time_2 = "15:30"

    if is_trading_holiday(now) or day_of_week in [5, 6]:
        previous_day = find_previous_working_day(now - timedelta(days=1))
        from_date = find_previous_working_day(previous_day - timedelta(days=1))
        to_date = previous_day
    else:
        if day_of_week == 0 and now.time() < datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=5)
            to_date = now - timedelta(days=4)
        elif day_of_week == 0 and now.time() >= datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=4)
            to_date = now - timedelta(days=3)
        elif day_of_week == 1 and now.time() < datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=4)
            to_date = now - timedelta(days=3)
        else:
            from_date = now - timedelta(days=2)
            to_date = now - timedelta(days=1)

    from_date_str = from_date.strftime("%Y-%m-%d ") + fixed_time_1
    to_date_str = to_date.strftime("%Y-%m-%d ") + fixed_time_2
    return from_date_str, to_date_str

# Function to generate the TOTP for 2FA
def generate_totp(totp_secret):
    return pyotp.TOTP(totp_secret).now()

# Function to login and fetch holdings, used in ProcessPoolExecutor
def process_user_portfolio_sync(user):
    # Each process starts its own event loop to run async code
    asyncio.run(process_user_portfolio(user))


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
        return obj, user_name, client_code
    except Exception as e:
        print(f"Error during login for user {username}: {e}")
        return None, None, None

# Async function to fetch holdings
async def fetch_holdings(obj):
    try:
        allholding_data = await asyncio.to_thread(obj.allholding)
        holdings_data = allholding_data['data']['holdings']
        total_portfolio_data = allholding_data['data']['totalholding']
        await asyncio.sleep(1)  # API rate limit: 1 hit per second for holdings
        return holdings_data, total_portfolio_data
    except Exception as e:
        print(f"Error fetching holdings: {e}")
        return None, None

# Async function to fetch OHLC data
async def fetch_ohlc_data(obj, exchange, symboltoken, semaphore):
    async with semaphore:
        try:
            from_date, to_date = fetch_dates()
            historical_params = {
                'exchange': exchange,
                'symboltoken': symboltoken,
                'interval': 'ONE_DAY',
                'fromdate': from_date,
                'todate': to_date
            }
            await asyncio.sleep(0.1)  # API rate limit: 10 hits per second for OHLC
            historical_data_response = await asyncio.to_thread(obj.getCandleData, historical_params)
            if 'data' in historical_data_response and historical_data_response['data']:
                last_data_point = historical_data_response['data'][-1]
                ohlc_data = {
                    'close': float(last_data_point[4])  # Closing price
                }
                return ohlc_data
            else:
                raise ValueError("No historical data found.")
        except Exception as e:
            print(f"Error fetching OHLC data: {e}")
            return None

# Async function to update MongoDB
async def update_portfolio_in_db(client_code, user_name, today_date, total_portfolio_data, total_today_gain, stock_entries):
    # Check if a portfolio exists for this client on the given date
    result = await portfolio_collection.update_one(
        {
            "ClientCode": client_code,
            "Portfolio.date": today_date  # We search by date to see if it exists
        },
        {
            "$set": {
                "Portfolio.$.totalholdingvalue": round(float(total_portfolio_data['totalholdingvalue']), 2),
                "Portfolio.$.totalinvvalue": round(float(total_portfolio_data['totalinvvalue']), 2),
                "Portfolio.$.totalprofitandloss": round(float(total_portfolio_data['totalprofitandloss']), 2),
                "Portfolio.$.totalpnlpercentage": float(total_portfolio_data['totalpnlpercentage']),
                "Portfolio.$.totalTodayGain": round(total_today_gain, 2)
            }
        }
    )

    if result.matched_count == 0:
        # No entry for today; push a new portfolio entry
        await portfolio_collection.update_one(
            {"ClientCode": client_code},
            {
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
            upsert=True
        )

    # Insert or update individual stock entries
    for stock in stock_entries:
        entry = stock['entries'][0]

        # First, check if a stock exists for this client
        document = await stocks_collection.find_one({"ClientCode": client_code})

        if document is None:
            # If no document exists, insert a new document for the client and their stocks
            await stocks_collection.insert_one({
                "ClientCode": client_code,
                "ClientName": user_name,
                "PortfolioStocks": [
                    {
                        "stockName": stock['stockName'],
                        "entries": [entry]
                    }
                ]
            })
        else:
            # Document exists, check if the stock already exists
            stock_exists = False
            for stock_data in document.get("PortfolioStocks", []):
                if stock_data["stockName"] == stock['stockName']:
                    stock_exists = True

                    # Now, check if today's date entry exists within this stock's entries
                    date_exists = any(e['date'] == today_date for e in stock_data['entries'])
                    if date_exists:
                        # Update the existing entry for today's date
                        await stocks_collection.update_one(
                            {
                                "ClientCode": client_code,
                                "PortfolioStocks.stockName": stock['stockName'],
                                "PortfolioStocks.entries.date": today_date
                            },
                            {
                                "$set": {
                                    "PortfolioStocks.$[stockItem].entries.$[entryItem]": entry
                                }
                            },
                            array_filters=[
                                {"stockItem.stockName": stock['stockName']},
                                {"entryItem.date": today_date}
                            ]
                        )
                    else:
                        # If the date does not exist, push a new entry for today
                        await stocks_collection.update_one(
                            {
                                "ClientCode": client_code,
                                "PortfolioStocks.stockName": stock['stockName']
                            },
                            {
                                "$push": {
                                    "PortfolioStocks.$.entries": entry
                                }
                            }
                        )
                    break

            if not stock_exists:
                # If the stock doesn't exist, push a new stock and its entries
                await stocks_collection.update_one(
                    {"ClientCode": client_code},
                    {
                        "$push": {
                            "PortfolioStocks": {
                                "stockName": stock['stockName'],
                                "entries": [entry]
                            }
                        }
                    }
                )

# Async function to process each user's portfolio
async def process_user_portfolio(user, ohlc_semaphore):
    apiKey = user['apiKey'][0]
    username = user['clientId']
    password = user['password']
    totp_secret = user['totp_secret']

    obj, user_name, client_code = await login_and_fetch_holdings(apiKey, username, password, totp_secret)
    if obj is None:
        return

    holdings_data, total_portfolio_data = await fetch_holdings(obj)
    if holdings_data is None:
        return

    today_date = datetime.today().strftime('%d-%m-%Y')
    total_today_gain = 0
    stock_entries = []

    # Fetch all OHLC data concurrently
    ohlc_tasks = [
        fetch_ohlc_data(obj, stock['exchange'], stock['symboltoken'], ohlc_semaphore) for stock in holdings_data
    ]
    ohlc_results = await asyncio.gather(*ohlc_tasks)

    for stock, ohlc_data in zip(holdings_data, ohlc_results):
        if ohlc_data is not None:
            prev_close = ohlc_data['close']
            ltp = float(stock['ltp'])
            today_gain = (ltp - prev_close) * stock['quantity']
            total_today_gain += today_gain

            entry = {
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
            }

            stock_entries.append({
                "stockName": stock['tradingsymbol'],
                "entries": [entry]
            })
            print(f"Processed {stock['tradingsymbol']}: Prev Close={prev_close}, LTP={ltp}, Today Gain={today_gain}")
        else:
            print(f"Skipped {stock['tradingsymbol']} due to OHLC data fetch issue")

    await update_portfolio_in_db(client_code, user_name, today_date, total_portfolio_data, total_today_gain, stock_entries)
    print(f"Portfolio updated successfully for {user_name}!")

# Main execution
async def main():
    print("Starting the portfolio update process for all users...")
    all_users = await credentials_collection.find().to_list(None)

    ohlc_semaphore = asyncio.Semaphore(10)  # 10 OHLC hits per second

    async def process_user(user):
        await process_user_portfolio(user, ohlc_semaphore)

    await asyncio.gather(*[process_user(user) for user in all_users])

if __name__ == "__main__":
    start_time = time()
    asyncio.run(main())
    end_time = time()
    print(f"Total execution time: {end_time - start_time} seconds")