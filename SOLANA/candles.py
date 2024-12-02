import requests
import json
import logging
from cryptography.hazmat.primitives import serialization
import time
import jwt
import secrets

CRYPTO_SYMBOL = "SOL-EUR"
GRANULARITY = "ONE_MINUTE"



# Your Coinbase API details (you need to define these)
key_name = "organizations/a935a9c0-1188-4df6-b289-3bc9c82328d8/apiKeys/cad2e31e-0159-4731-97d6-a43373845768"
key_secret = "-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIElQWMXqYUmD9J9ajFEUxYBqCxkDsLXfAgoKY87BynQaoAoGCCqGSM49\nAwEHoUQDQgAEe/nIxWZ27+bnVyIljVripEhfi5B59QgVcWNDqfiGn3PAvGGPqqK/\nGS95NnY0jDImKumL3AF4fcXOh+MaAebSaw==\n-----END EC PRIVATE KEY-----\n"





logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
    ],
)

def build_jwt(uri):
    # logging.debug(f"Building JWT token for URI: {uri}")
    private_key_bytes = key_secret.encode("utf-8")
    private_key = serialization.load_pem_private_key(private_key_bytes, password=None)

    # JWT payload
    jwt_payload = {
        "sub": key_name,
        "iss": "cdp",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,  # Expire in 120 seconds
        "uri": uri,
    }

    # Generate JWT token using ES256
    jwt_token = jwt.encode(
        jwt_payload,
        private_key,
        algorithm="ES256",
        headers={"kid": key_name, "nonce": secrets.token_hex()},
    )
    # logging.debug(f"JWT token generated successfully: {jwt_token}")
    return jwt_token


import requests
import json
import logging

def fetch_candles():
    """
    Ανακτά τα ιστορικά δεδομένα candles από το Coinbase API για το συγκεκριμένο κρυπτονόμισμα και τη χρονική περίοδο.
    
    Χρησιμοποιεί τις στατικές μεταβλητές:
    - CRYPTO_SYMBOL: Το σύμβολο του κρυπτονομίσματος (π.χ. "BTC-USD").
    - GRANULARITY: Το χρονικό διάστημα των candles (π.χ. "ONE_MINUTE", "FIVE_MINUTE").
    
    :return: Λίστα με τα ιστορικά candles ή ένα λεξικό με error message.
    """
    request_host = "api.coinbase.com"
    candles_path = f"/api/v3/brokerage/products/{CRYPTO_SYMBOL}/candles"
    url = f"https://{request_host}{candles_path}"
    
    # Δημιουργία του σωστού URI για το JWT token
    uri = f"GET {request_host}{candles_path}"
    jwt_token = build_jwt(uri)  # Δημιουργία νέου JWT token

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }

    # Παράμετροι για το granularity
    params = {
        "granularity": GRANULARITY
    }

    try:
        response = requests.get(url, headers=headers, params=params)

        # Έλεγχος της απόκρισης
        if response.status_code == 200:
            candles_data = response.json()

            # Logging των δεδομένων και εμφάνιση στο τερματικό
            logging.info(f"Fetched candles data: {candles_data}")
            print(f"Fetched candles data: {json.dumps(candles_data, indent=2)}")
            return candles_data
        else:
            logging.error(f"Failed to fetch candles. Status: {response.status_code}, Data: {response.text}")
            print(f"Failed to fetch candles. Status: {response.status_code}, Data: {response.text}")
            return {
                "error": response.status_code,
                "message": response.text
            }

    except Exception as e:
        logging.error(f"Error fetching candles data: {e}")
        print(f"Error fetching candles data: {e}")
        return {
            "error": "exception",
            "message": str(e)
        }



# Main loop (updated to load state)
def run_bot():
    logging.info("Fetching Candles...")
    fetch_candles()



if __name__ == "__main__":
    fetch_candles()