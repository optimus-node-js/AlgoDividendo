import pyotp
from SmartApi.smartConnect import SmartConnect
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from pathlib import Path

# Replace with your actual credentials
clientcode = '***REDACTED***'
password = '***REDACTED***'
apiKey = '***REDACTED***'
totp_secret = '***REDACTED***'

app = FastAPI()

def generate_totp(totp_secret):
    return pyotp.TOTP(totp_secret).now()

def login(apiKey, clientcode, password, totp_secret):
    obj = SmartConnect(api_key=apiKey)
    try:
        data = obj.generateSession(clientcode, password, generate_totp(totp_secret))
        return obj, data['data']['refreshToken'], obj.getfeedToken()
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error during login: {e}")

obj, refreshToken, feedToken = login(apiKey, clientcode, password, totp_secret)




# Fetch LTP for a single symbol
def fetch_ltp(symbol: str, token: str):
    try:
        LTP = obj.ltpData('NSE', symbol, token)
        if LTP and 'data' in LTP and 'ltp' in LTP['data']:
            return {"symbol": symbol, "ltp": LTP['data']['ltp']}
        else:
            raise HTTPException(status_code=404, detail=f"No LTP data found for {symbol}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get LTP data for {symbol}: {e}")

# Fetch OHLC for a single symbol within a specific date range
def fetch_ohlc(symbol: str, token: str, interval: str, from_date: str, to_date: str):
    try:
        historical_params = {
            "exchange": "NSE",
            "symboltoken": token,
            "interval": interval,
            "fromdate": from_date,
            "todate": to_date
        }

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
            return {"symbol": symbol, "interval": interval, "data": ohlc_list}
        else:
            raise HTTPException(status_code=404, detail=f"No OHLC data found for {symbol}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get OHLC data for {symbol}: {e}")
    
    
# Fetch User Profile Data
def fetch_user_profile():
    try:
        profile = obj.getProfile(refreshToken)
        if profile and 'data' in profile:
            return profile['data']
        else:
            raise HTTPException(status_code=404, detail="No profile data found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile data: {e}")

# Fetch Funds Details
def fetch_funds_details():
    try:
        funds = obj.rmsLimit()
        if funds and 'data' in funds:
            return funds['data']
        else:
            raise HTTPException(status_code=404, detail="No funds data found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching funds data: {e}")
    
    
# Fetch Holding
def fetch_holding():
    print("Triggering fetch_holdings")
    try:
        holdings = obj.holding()  
        if holdings and 'data' in holdings:
            return holdings['data']
        else:
            raise HTTPException(status_code=404, detail="No holdings data found.")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching holdings data: {e}")


# Fetch All Holdings
def fetch_all_holdings():
    print("Triggering fetch_holdings")
    try:
        holdings = obj.allholding()  # Use allholding instead of getHoldings
        
        if holdings and 'data' in holdings:
            return holdings['data']
        else:
            raise HTTPException(status_code=404, detail="No holdings data found.")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching holdings data: {e}")



# Request model for dynamic stock fetching
class StockRequest(BaseModel):
    mode: str
    exchangeTokens: dict


# Fetch stock price in "FULL" mode
def fetch_full_mode_price(mode: str, exchangeTokens: dict):
    try:
        # Fetch the market data using the provided parameters
        response = obj.getMarketData(mode, exchangeTokens)
        if response and 'data' in response:
            return response['data']
        else:
            raise HTTPException(status_code=404, detail="No data found for provided tokens.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {e}")










# Function to log out the user
def logout():
    print("Triggering logout")
    try:
        response = obj.terminateSession(clientcode)
        print("Logout API Response:", response)  # Log response for debugging
        if response and response['status']:
            return {"message": "Logged out successfully"}
        else:
            raise HTTPException(status_code=500, detail="Logout failed.")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error during logout: {e}")    
    
    

# Request body models for FastAPI
class LTPRequest(BaseModel):
    symbol: str
    token: str

class OHLCRequest(BaseModel):
    symbol: str
    token: str
    interval: str
    from_date: str
    to_date: str

# Request model for dynamic stock fetching
class StockRequest(BaseModel):
    mode: str
    exchangeTokens: dict

# Home page route
@app.get("/", response_class=HTMLResponse)
async def serve_welcome_template():
    # Path to your HTML file
    html_path = Path("Templates/welcomeTemplate.html")
    
    # Read the HTML file content
    if html_path.exists():
        with open(html_path, 'r') as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return HTMLResponse(content="Template not found", status_code=404)






# FastAPI route to get LTP
@app.post("/get_price_ltp/")
async def get_ltp(data: LTPRequest):
    return fetch_ltp(data.symbol, data.token)

# FastAPI route to get OHLC
@app.post("/get_price_ohlc/")
async def get_ohlc(data: OHLCRequest):
    return fetch_ohlc(data.symbol, data.token, data.interval, data.from_date, data.to_date)


# Route to fetch stock price in full mode
@app.post("/get_price_full/")
async def get_stock_prices(request: StockRequest):
    return fetch_full_mode_price(request.mode, request.exchangeTokens)


@app.get("/get_profile/")
async def get_profile():
    return fetch_user_profile()

@app.get("/get_funds/")
async def get_funds():
    return fetch_funds_details()



# Route for fetching holdings
@app.get("/get_holding/")
async def get_holdings():
    return fetch_holding()


# Route for fetching holdings
@app.get("/get_all_holding/")
async def get_holdings():
    return fetch_all_holdings()









# FastAPI route to log out
@app.get("/logout/")
async def perform_logout():
    return logout()
