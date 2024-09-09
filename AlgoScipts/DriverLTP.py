import pyotp
from SmartApi.smartConnect import SmartConnect
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from pathlib import Path

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
print(obj.allholding()['data']['holdings'])
# holdings = obj.holding()['data']
# summing = []
# for i in holdings:
#     print(summing.append(i['profitandloss']))
#
# print(summing)
# print(sum(summing))

# data = {
#     "datatype":"PercPriceGainers",
#     "expirytype":"NEAR"
# }
# print(obj.gainersLosers(data))



#
# param = { "mode": "FULL", "exchangeTokens": { "NSE": ["3045","881"], "NFO": ["58662"]} }
# print(obj.getMarketData(param['mode'], param['exchangeTokens']))

