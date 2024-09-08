import pyotp
import argparse
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
        print("Failed to login, please check your API credentials.")
        return

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


def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Fetch historical OHLC data for a stock symbol.")
    parser.add_argument("symbol", help="Stock symbol (e.g., CIPLA-EQ)")
    parser.add_argument("token", help="Token for the stock symbol")
    parser.add_argument("interval", help="Time interval (e.g., ONE_MINUTE, ONE_DAY)")
    parser.add_argument("from_date", help="Start date (format: YYYY-MM-DD HH:MM)")
    parser.add_argument("to_date", help="End date (format: YYYY-MM-DD HH:MM)")

    args = parser.parse_args()

    # Fetch OHLC data for the specific interval
    ohlc_data = fetch_historical_ohlc(args.symbol, args.token, args.interval, args.from_date, args.to_date)

    # Output the OHLC data in JSON format
    print(json.dumps(ohlc_data, indent=4))


if __name__ == "__main__":
    main()
