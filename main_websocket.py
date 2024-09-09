import websocket
import json
import pyotp
from SmartApi.smartConnect import SmartConnect
import threading
import time
import logging

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your actual credentials
username = '***REDACTED***'
password = '***REDACTED***'
apiKey = '***REDACTED***'
totp_secret = '***REDACTED***'
feed_token = None
client_code = username
jwt_token = None
retry_attempts = 3  # Number of retry attempts if token is invalid

# Function to generate TOTP using pyotp
def generate_totp(totp_secret):
    return pyotp.TOTP(totp_secret).now()

# Function to login using credentials and fetch feed token
def login(apiKey, username, password, totp_secret):
    obj = SmartConnect(api_key=apiKey)
    try:
        logger.info("Logging in...")
        data = obj.generateSession(username, password, generate_totp(totp_secret))
        logger.info(f"Session Data: {data}")
        global feed_token, jwt_token
        feed_token = obj.getfeedToken()
        jwt_token = data['data']['jwtToken']
        logger.info(f"Generated feed token: {feed_token}")
        return obj, data['data']['refreshToken'], feed_token
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return None, None, None

# WebSocket class for handling real-time LTP data
class SmartWebSocketV2:
    def __init__(self, jwt_token, api_key, client_code, feed_token):
        self.jwt_token = jwt_token
        self.api_key = api_key
        self.client_code = client_code
        self.feed_token = feed_token
        self.ws = None

    def on_open(self, ws):
        logger.info("WebSocket connection opened")
        # Subscribing to stock feed for 'IRFC-EQ' using token '2029'
        token_list = [
            {
                "exchangeType": 1,  # NSE Exchange
                "tokens": ["2029"]  # IRFC-EQ stock token
            }
        ]
        correlation_id = "abc123"  # Unique ID for this session
        mode = 1  # Mode to request live data
        self.subscribe(correlation_id, mode, token_list)

    def on_message(self, ws, message):
        logger.info(f"Received WebSocket message: {message}")

    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket closed with code: {close_status_code}, message: {close_msg}")

    def subscribe(self, correlation_id, mode, token_list):
        # Constructing subscription message
        subscribe_message = {
            "action": 1,  # Subscribe
            "token": self.feed_token,
            "client_code": self.client_code,
            "correlation_id": correlation_id,
            "mode": mode,
            "token_list": token_list
        }
        logger.info(f"Sending subscription message: {subscribe_message}")
        self.ws.send(json.dumps(subscribe_message))

    def connect(self):
        websocket_url = "wss://smartapisocket.angelone.in/smart-stream"
        headers = {
            'Authorization': f'Bearer {self.jwt_token}',  # Send JWT token in headers
            'x-api-key': self.api_key,  # API Key header
            'x-feed-token': self.feed_token  # Feed token in headers
        }

        self.ws = websocket.WebSocketApp(
            websocket_url,
            header=[f'{key}: {value}' for key, value in headers.items()],
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        # Keeping the connection alive with ping_interval
        wst = threading.Thread(target=self.ws.run_forever, kwargs={"ping_interval": 30})  # Ping every 30 seconds
        wst.daemon = True
        wst.start()

    def close(self):
        if self.ws:
            self.ws.close()

# Retry function for login and WebSocket connection
def retry_connection(apiKey, username, password, totp_secret, max_attempts):
    attempt = 0
    while attempt < max_attempts:
        obj, refreshToken, feedToken = login(apiKey, username, password, totp_secret)
        if obj and feedToken:
            # Initialize WebSocket connection for real-time data
            ws_client = SmartWebSocketV2(jwt_token, apiKey, client_code, feedToken)
            ws_client.connect()
            try:
                while True:
                    time.sleep(1)  # Keep the script running to listen for WebSocket data
            except KeyboardInterrupt:
                ws_client.close()
                break
        else:
            attempt += 1
            logger.info(f"Login failed, retrying... Attempt {attempt}/{max_attempts}")
            time.sleep(5)  # Wait before retrying

    if attempt == max_attempts:
        logger.error("Failed to connect after multiple attempts. Please check your credentials.")

# Main function to start the WebSocket connection with retry logic
if __name__ == "__main__":
    retry_connection(apiKey, username, password, totp_secret, retry_attempts)
