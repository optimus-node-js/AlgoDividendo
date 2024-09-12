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


def generate_totp(totp_secret):
    return pyotp.TOTP(totp_secret).now()


def login(apiKey, username, password, totp_secret):
    obj = SmartConnect(api_key=apiKey)
    try:
        data = obj.generateSession(username, password, generate_totp(totp_secret))
        return obj, data['data']['refreshToken'], obj.getfeedToken()
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error during login: {e}")


obj, refreshToken, feedToken = login(apiKey, username, password, totp_secret)


def numThree(value):
    return f"{value:.3f}"


def fetch_date(day="today"):
    # Get current date and time
    now = datetime.now()

    # Yesterday's and day-before-yesterday's date and time
    yesterday = now - timedelta(days=1)
    day_before_yesterday = now - timedelta(days=2)

    # Format the time
    fixed_time_1 = "09:15"
    fixed_time_2 = "15:30"

    if day == "today":
        # Return list with yesterday's and today's date in fixed format
        return [yesterday.strftime("%Y-%m-%d ") + fixed_time_1, now.strftime("%Y-%m-%d ") + fixed_time_2]
    elif day == "yesterday":
        # Return list with day-before-yesterday and yesterday's date in fixed format
        return [day_before_yesterday.strftime("%Y-%m-%d ") + fixed_time_1,
                yesterday.strftime("%Y-%m-%d ") + fixed_time_2]


dateCorrect = fetch_date("yesterday")
previousDayDate = dateCorrect[0]
todayDayDate = dateCorrect[1]


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

        data = obj.getCandleData(historical_params)
        print(data['data'][0][4])
    except Exception as e:
        return {"interval": interval, "data": [], "error": str(e)}


data1 = obj.allholding()['data']['holdings']
TodaysGain = []
for data in data1:
    fetch_historical_ohlc(data['tradingsymbol'], data['symboltoken'], "ONE_DAY", previousDayDate, todayDayDate)
    todayGain = (data['ltp'] - data['close']) * data['quantity']
    TodaysGain.append(todayGain)
    print(f"{data['tradingsymbol']} = {numThree(todayGain)}")
    sleep(0.10)

todayOverallGain = numThree(sum(TodaysGain))
print(f"Today's Portfolio Overall Gain : {todayOverallGain}")
