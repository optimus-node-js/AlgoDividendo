import pyotp
import json
from SmartApi.smartConnect import SmartConnect

# Credentials
username = '***REDACTED***'
password = '***REDACTED***'
apiKey = '***REDACTED***'
totp_secret = '***REDACTED***'

def generate_totp(totp_secret):
    return pyotp.TOTP(totp_secret).now()

def login(apiKey, username, password, totp_secret):
    obj = SmartConnect(api_key=apiKey)
    try:
        data = obj.generateSession(username, password, generate_totp(totp_secret))
        return obj, data['data']['refreshToken'], obj.getfeedToken()
    except Exception as e:
        print(f"Error during login: {e}")
        return None, None, None

# Function to fetch OHLC data for a specific timeframe
def fetch_historical_ohlc(symbol, token, interval, from_date, to_date):
    obj, refreshToken, feedToken = login(apiKey, username, password, totp_secret)

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

        print(f"Fetching OHLC for {symbol} from {from_date} to {to_date} with interval '{interval}'")

        data = obj.getCandleData(historical_params)
        if data and 'data' in data:
            ohlc_data = data['data']
            ohlc_list = [
                {
                    "date": ohlc[0],
                    "open": ohlc[1],
                    "high": ohlc[2],
                    "low": ohlc[3],
                    "close": ohlc[4],
                }
                for ohlc in ohlc_data
            ]
            return {"interval": interval, "data": ohlc_list}
        else:
            return {"interval": interval, "data": [], "error": data}
    except Exception as e:
        return {"interval": interval, "data": [], "error": str(e)}

# New function that accepts parameters directly instead of command-line arguments
def get_ohlc_data(symbol, token, interval, from_date, to_date):
    ohlc_data = fetch_historical_ohlc(symbol, token, interval, from_date, to_date)
    return json.dumps(ohlc_data, indent=4)




ohlc_json = get_ohlc_data('CIPLA-EQ', '694', 'ONE_DAY', '2023-09-13 09:15', '2023-09-16 15:30')
print(ohlc_json)




