from pymongo import MongoClient
from datetime import datetime
import pyotp
from SmartApi.smartConnect import SmartConnect
from fastapi import HTTPException

# MongoDB connection string
mongo_uri = "mongodb+srv://SupremeRahul:***REDACTED***@clusternse.wpf8cel.mongodb.net/"
client = MongoClient(mongo_uri)

# Database and collection
db = client['SmartAPI']
portfolio_collection = db['Angelone Portfolio Tracker']

# Example credentials array for multiple users
credentials = [
    {
        "username": "***REDACTED***",  # This is both username and client code
        "password": "***REDACTED***",
        "apikey": "***REDACTED***",
        "totp_secret": "***REDACTED***"
    },
    # Add more users as needed with their credentials
]


# Function to generate the TOTP for 2FA
def generate_totp(totp_secret):
    return pyotp.TOTP(totp_secret).now()


# Function to login and fetch portfolio data
def login_and_fetch_portfolio(apiKey, username, password, totp_secret):
    obj = SmartConnect(api_key=apiKey)
    try:
        # Login and get session details
        data = obj.generateSession(username, password, generate_totp(totp_secret))
        refreshToken = data['data']['refreshToken']

        # Fetch the user's profile and name
        NameOfUser = obj.getProfile(refreshToken)['data']['name']
        user_name = ' '.join(NameOfUser.split())
        # Fetch the portfolio details
        portfolio = obj.allholding()['data']['totalholding']  # Pre-calculated portfolio data from API

        return obj, refreshToken, portfolio, user_name

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error during login: {e}")


# Function to update or insert the portfolio in MongoDB
def update_portfolio_data(username, portfolio_data, user_name):
    today_date = datetime.today().strftime('%d-%m-%Y')

    # Check if the user exists in the collection
    user_portfolio = portfolio_collection.find_one({"ClientCode": username})

    if user_portfolio:
        # User exists, now check if today's date is already in the portfolio
        for entry in user_portfolio['Portfolio']:
            if entry['date'] == today_date:
                # Update the existing entry for today
                portfolio_collection.update_one(
                    {"ClientCode": username, "Portfolio.date": today_date},
                    {
                        "$set": {
                            "Portfolio.$.totalholdingvalue": portfolio_data['totalholdingvalue'],
                            "Portfolio.$.totalinvvalue": portfolio_data['totalinvvalue'],
                            "Portfolio.$.totalprofitandloss": portfolio_data['totalprofitandloss'],
                            "Portfolio.$.totalpnlpercentage": portfolio_data['totalpnlpercentage']
                        }
                    }
                )
                print(f"Updated portfolio for {user_name} on {today_date}.")
                return
        # If today's date is not found, append a new entry
        portfolio_collection.update_one(
            {"ClientCode": username},
            {
                "$push": {
                    "Portfolio": {
                        "date": today_date,
                        "totalholdingvalue": portfolio_data['totalholdingvalue'],
                        "totalinvvalue": portfolio_data['totalinvvalue'],
                        "totalprofitandloss": portfolio_data['totalprofitandloss'],
                        "totalpnlpercentage": portfolio_data['totalpnlpercentage']
                    }
                }
            }
        )
        print(f"Added new portfolio entry for {user_name} on {today_date}.")
    else:
        # User does not exist, create a new document for the user
        new_portfolio_doc = {
            "Name": user_name,
            "ClientCode": username,
            "Portfolio": [
                {
                    "date": today_date,
                    "totalholdingvalue": portfolio_data['totalholdingvalue'],
                    "totalinvvalue": portfolio_data['totalinvvalue'],
                    "totalprofitandloss": portfolio_data['totalprofitandloss'],
                    "totalpnlpercentage": portfolio_data['totalpnlpercentage']
                }
            ]
        }
        portfolio_collection.insert_one(new_portfolio_doc)
        print(f"Created new portfolio for {user_name} and added entry for {today_date}.")


# Example loop to handle multiple users' portfolios
for credential in credentials:
    obj, refreshToken, portfolio_data, user_name = login_and_fetch_portfolio(
        apiKey=credential["apikey"],
        username=credential["username"],
        password=credential["password"],
        totp_secret=credential["totp_secret"]
    )

    if portfolio_data:
        update_portfolio_data(
            username=credential["username"],  # Using username as client code
            portfolio_data=portfolio_data,
            user_name=user_name
        )
