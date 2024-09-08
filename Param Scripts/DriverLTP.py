import pyotp
from SmartApi.smartConnect import SmartConnect

# Replace with your actual username, password, API key, and TOTP secret
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

# Function to fetch LTP for a single ticker
def fetch_ltp(symbol, token):
    obj, refreshToken, feedToken = login(apiKey, username, password, totp_secret)

    if obj is None:
        return {"error": "Failed to login, please check your API credentials."}

    try:
        LTP = obj.ltpData('NSE', symbol, token)
        if LTP and 'data' in LTP and 'ltp' in LTP['data']:
            return {"symbol": symbol, "ltp": LTP['data']['ltp']}
        else:
            return {"symbol": symbol, "ltp": None, "error": "No LTP data found."}
    except Exception as e:
        return {"symbol": symbol, "ltp": None, "error": str(e)}

# New function that accepts parameters directly instead of running inside the script
def get_ltp(symbol, token):
    ltp_data = fetch_ltp(symbol, token)
    return ltp_data

ltp_info = get_ltp('IRFC-EQ', '2029')
print(ltp_info)
