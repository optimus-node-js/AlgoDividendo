import pyotp
from SmartApi.smartConnect import SmartConnect
from fastapi import FastAPI, HTTPException
from time import sleep
from datetime import datetime, timedelta

# Replace with your actual credentials
username = '***REDACTED***'
password = '***REDACTED***'
apiKey = '***REDACTED***'
totp_secret = '***REDACTED***'

app = FastAPI()

def numThree(value):
    return f"{value:.3f}"

def generate_totp(totp_secret):
    return pyotp.TOTP(totp_secret).now()


def login(apiKey, username, password, totp_secret):
    print(f"Logging In : {username}")
    obj = SmartConnect(api_key=apiKey)
    try:
        data = obj.generateSession(username, password, generate_totp(totp_secret))
        print("Successfully Logged In!")
        return obj, data['data']['refreshToken'], obj.getfeedToken()
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error during login: {e}")

obj, refreshToken, feedToken = login(apiKey, username, password, totp_secret)


def fetchuserInfo():
    userData = obj.getProfile(refreshToken)['data']
    userName = userData['name']
    userClientCode = userData['clientcode']
    name = ' '.join(userName.split())


    return [name, userClientCode]

def fetch_historical_ohlc(symbol, token, interval, from_date, to_date):
    if obj is None:
        return {"error": "Failed to login, please check your API credentials."}

    try:
        # Fetch OHLC data using historicalData
        historical_params = {
            "exchange": "NSE",
            "symboltoken": token,
            "interval": interval,  # Time interval e.g., 'ONE_MINUTE', 'ONE_DAY', etc.
            "fromdate": from_date,  # Format: 'YYYY-MM-DD HH:MM'
            "todate": to_date  # Format: 'YYYY-MM-DD HH:MM'
        }

        # print(f"Fetching OHLC for {symbol} from {from_date} to {to_date} with interval '{interval}'")

        data = obj.getCandleData(historical_params)['data'][0][4]
        return data
    except Exception as e:
        return {"interval": interval, "data": [], "error": str(e)}

def fetch_dates():
    # Get current date and time dynamically
    now = datetime.now()

    # Check if the current time is between 12:00 AM and 9:14 AM
    if now.time() >= datetime.strptime("00:00", "%H:%M").time() and now.time() <= datetime.strptime("09:14","%H:%M").time():
        # If the time is between 12:00 AM and 9:14 AM, adjust the date
        # Subtract 3 days for "from_date" and 2 days for "to_date"
        from_date = now - timedelta(days=3)
        to_date = now - timedelta(days=2)
    else:
        # Otherwise, subtract 2 days for "from_date" and 1 day for "to_date"
        from_date = now - timedelta(days=2)
        to_date = now - timedelta(days=1)

    # Fixed times
    fixed_time_1 = "09:15"
    fixed_time_2 = "15:30"

    # Return list with from_date and to_date in fixed format
    return [from_date.strftime("%Y-%m-%d ") + fixed_time_1, to_date.strftime("%Y-%m-%d ") + fixed_time_2]

dateCorrect = fetch_dates()
previousDayDate = dateCorrect[0]
todayDayDate = dateCorrect[1]

data1 = obj.allholding()['data']['holdings']
TodaysGain = []

for data in data1:
    prevClose = fetch_historical_ohlc(data['tradingsymbol'], data['symboltoken'], "ONE_DAY", previousDayDate, todayDayDate)
    print(prevClose)
    todayGain = (data['ltp'] - prevClose) * data['quantity']
    TodaysGain.append(todayGain)
    print(f"{data['tradingsymbol']} = {numThree(todayGain)}")
    sleep(0.10)