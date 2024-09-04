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
        print("Failed to login, please check your API credentials.")
        return

    try:
        LTP = obj.ltpData('NSE', symbol, token)
        if LTP and 'data' in LTP and 'ltp' in LTP['data']:
            print(f"LTP of {symbol}: {LTP['data']['ltp']}")
        else:
            print(f"No LTP data found for {symbol}")
    except Exception as e:
        print(f"Failed to get LTP data for {symbol}: {e}")


# Replace 'RELIANCE-EQ' and '2885' with a valid symbol and token
fetch_ltp('IRFC-EQ', '2029')
