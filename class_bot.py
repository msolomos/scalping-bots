import logging
import requests
import json
import time
import pushover


class ScalpingBot:
    def __init__(self, config):
        """
        Αρχικοποίηση του bot με βάση τις ρυθμίσεις που περνιούνται ως config.
        """
        # Βασικές ρυθμίσεις από το config
        self.crypto_symbol = config["CRYPTO_SYMBOL"]
        self.crypto_name = config["CRYPTO_NAME"]
        self.crypto_currency = config["CRYPTO_CURRENCY"]
        self.scalp_target = config["SCALP_TARGET"]
        self.trade_amount = config["TRADE_AMOUNT"]

        # Ρυθμίσεις τεχνικών δεικτών
        self.short_ma_period = config["short_ma_period"]
        self.long_ma_period = config["long_ma_period"]
        self.rsi_threshold = config["RSI_THRESHOLD"]

        # Ρυθμίσεις cooldown
        self.cooldown_file = config["cooldown_file"]

        # Ενεργοποίηση αρχικών μεταβλητών
        self.daily_profit = 0
        self.current_trades = 0
        self.active_trade = None
        self.highest_price = 0
        self.trailing_profit_active = False

        # Ρυθμίσεις API
        self.public_base_url = "https://api.exchange.coinbase.com"

        # Αρχικοποίηση logger
        logging.basicConfig(level=logging.INFO)

        logging.info(f"Bot initialized for {self.crypto_name}")

    def get_crypto_price(self, retries=3, delay=5):
        """
        Λαμβάνει την τρέχουσα τιμή του κρυπτονομίσματος από το Coinbase API.
        """
        request_path = f"/products/{self.crypto_symbol}/ticker"

        for attempt in range(retries):
            try:
                response = requests.get(f"{self.public_base_url}{request_path}")
                if response.status_code != 200:
                    logging.error(f"Failed to fetch {self.crypto_name} price. Status: {response.status_code}")
                    time.sleep(delay)
                    continue

                data = response.json()
                if "price" not in data:
                    logging.error(f"'price' key missing in API response.")
                    time.sleep(delay)
                    continue

                price = float(data["price"])
                logging.info(f"Fetched {self.crypto_name} price: {price} {self.crypto_currency}")
                return price

            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching {self.crypto_name} price: {e}")
                time.sleep(delay)

        logging.error(f"Failed to fetch {self.crypto_name} price after {retries} attempts.")
        return None




    def save_cooldown_state(self, custom_duration=None):
        """
        Αποθηκεύει το cooldown state με διάρκεια (προεπιλογή: 3600 δευτερόλεπτα).
        """
        duration = custom_duration or 3600
        cooldown_data = {"timestamp": time.time(), "duration": duration}

        with open(self.cooldown_file, "w") as file:
            json.dump(cooldown_data, file)

        logging.info(f"Cooldown state saved with duration {duration} seconds.")

    def check_cooldown(self):
        """
        Ελέγχει αν το cooldown έχει λήξει.
        """
        try:
            with open(self.cooldown_file, "r") as file:
                cooldown_data = json.load(file)

            elapsed_time = time.time() - cooldown_data["timestamp"]
            remaining_time = cooldown_data["duration"] - elapsed_time

            if remaining_time > 0:
                logging.info(f"Cooldown active. Remaining time: {remaining_time:.2f} seconds.")
                return False, remaining_time

            return True, 0

        except FileNotFoundError:
            logging.info("No cooldown file found. Cooldown is over.")
            return True, 0




        
    def calculate_ma(self, prices, period):
        """
        Υπολογίζει τον κινητό μέσο όρο (Moving Average).
        """
        if len(prices) < period:
            logging.warning(f"Not enough data to calculate MA for period {period}.")
            return None
        ma = sum(prices[-period:]) / period
        logging.info(f"Calculated MA for period {period}: {ma}")
        return ma

    def calculate_rsi(self, prices, period=14):
        """
        Υπολογίζει τον RSI (Relative Strength Index).
        """
        if len(prices) < period:
            logging.warning(f"Not enough data to calculate RSI for period {period}.")
            return None

        gains = []
        losses = []

        for i in range(1, len(prices)):
            diff = prices[i] - prices[i - 1]
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))

        average_gain = sum(gains[-period:]) / period
        average_loss = sum(losses[-period:]) / period

        if average_loss == 0:
            return 100

        rs = average_gain / average_loss
        rsi = 100 - (100 / (1 + rs))
        logging.info(f"Calculated RSI: {rsi}")
        return rsi
        
        
    # Ειδοποίηση μέσω Pushover
    def send_push_notification(self, message):
        try:
            po = pushover.Client(user_key=PUSHOVER_USER, api_token=PUSHOVER_TOKEN)
            po.send_message(message, title="Scalping Alert")
            #logging.info("Push notification sent via Pushover")
        except Exception as e:
            logging.error(f"Error sending Push notification: {e}")

    def sendgrid_email(self, subject, content):
        """
        Στέλνει email μέσω SendGrid.
        """
        try:
            SENDGRID_API_KEY = "your_sendgrid_api_key"
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            email = Mail(
                from_email="your_email@example.com",
                to_emails="recipient_email@example.com",
                subject=subject,
                plain_text_content=content
            )
            response = sg.send(email)
            if response.status_code in [200, 202]:
                logging.info("Email sent successfully.")
            else:
                logging.error(f"Failed to send email. Status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Error sending email: {e}")
        



    def execute_scalping_trade(self):
        """
        Υλοποιεί τη στρατηγική scalping.
        """
        logging.info("Executing scalping trade...")
        price = self.get_crypto_price()
        if price is None:
            logging.error("Price fetch failed. Exiting scalping trade.")
            return

        # Placeholder logic for trading
        ma_short = self.calculate_ma([price] * self.short_ma_period, self.short_ma_period)  # Example usage
        ma_long = self.calculate_ma([price] * self.long_ma_period, self.long_ma_period)  # Example usage

        if ma_short and ma_long and ma_short > ma_long:
            logging.info(f"Scalping signal detected. Short MA ({ma_short}) > Long MA ({ma_long}).")
            self.send_push_notification("Scalping signal detected!")
            # Execute trade logic here
        else:
            logging.info(f"No scalping signal. Short MA: {ma_short}, Long MA: {ma_long}")




    def run(self):
        """
        Κύρια εκτέλεση του bot.
        """
        is_cooldown_over, remaining_time = self.check_cooldown()
        if not is_cooldown_over:
            logging.info(f"Cooldown active. Waiting for {remaining_time:.2f} seconds.")
            return

        logging.info("Starting scalping trade logic.")
        self.execute_scalping_trade()

        



if __name__ == "__main__":
    config = {
        "CRYPTO_SYMBOL": "LTC-EUR",
        "CRYPTO_NAME": "LTC",
        "CRYPTO_CURRENCY": "EUR",
        "SCALP_TARGET": 1.02,
        "TRADE_AMOUNT": 20,
        "short_ma_period": 5,
        "long_ma_period": 20,
        "RSI_THRESHOLD": 30,
        "cooldown_file": "/path/to/cooldown_state.json"
    }

    bot = ScalpingBot(config)
    bot.run()

