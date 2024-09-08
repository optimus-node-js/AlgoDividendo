import pyotp
import argparse
import json
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

# Function that accepts parameters directly
def get_ltp(symbol, token):
    ltp_data = fetch_ltp(symbol, token)
    return json.dumps(ltp_data, indent=4)

# Command-line version using argparse
def main():
    parser = argparse.ArgumentParser(description="Fetch LTP data for a stock symbol.")
    parser.add_argument("symbol", help="Stock symbol (e.g., CIPLA-EQ)")
    parser.add_argument("token", help="Token for the stock symbol")

    args = parser.parse_args()

    # Fetch LTP data using command-line parameters
    ltp_data = fetch_ltp(args.symbol, args.token)

    # Output the LTP data in JSON format
    print(json.dumps(ltp_data, indent=4))

if __name__ == "__main__":
    main()


'''For Direct Function Call:
You can still call the get_ltp function directly:

ltp_info = get_ltp('IRFC-EQ', '2029')
print(ltp_info)

'''


'''For Command-Line Usage:
You can use the command line with argparse like this:

python DriverLTP.py IRFC-EQ 2029

'''