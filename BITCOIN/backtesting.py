import pandas as pd
import logging
import time

# ===========================
# Υπολογισμός Δεικτών (χρήση των συναρτήσεων σου)
# ===========================
from scalper_bitcoin import calculate_macd, calculate_rsi, calculate_bollinger_bands
from scalper_bitcoin import calculate_vwap, calculate_adx, calculate_stochastic, calculate_stochastic_rsi
from scalper_bitcoin import calculate_volume_confirmation, fallback_conditions




def load_weights(crypto_name):
    """
    Επιστρέφει τα βάρη για τους δείκτες βάσει του ονόματος του κρυπτονομίσματος.
    Args:
        crypto_name (str): Όνομα του κρυπτονομίσματος.
    Returns:
        dict: Λεξικό με τα βάρη των δεικτών.
    """
    # Παράδειγμα για BTC
    if crypto_name == "BTC":
        return {
            "macd": 0.25,
            "rsi": 0.3,
            "bollinger": 0.2,
            "vwap": 0.25
        }
    else:
        raise ValueError(f"Unknown crypto name: {crypto_name}")








# ===========================
# Backtesting Λογική
# ===========================
def backtest(df, crypto_name, buy_threshold=0.4, window=20):
    """
    Εκτέλεση backtesting μαζικά και παρουσίαση συνολικών αποτελεσμάτων.

    Args:
        df (pd.DataFrame): Ιστορικά δεδομένα με στήλες (open, high, low, close, volume).
        crypto_name (str): Όνομα του κρυπτονομίσματος για φόρτωση βαρών.
        buy_threshold (float): Κατώφλι για το σκορ αγοράς.
        window (int): Παράθυρο για τον υπολογισμό του μέσου όγκου (volume confirmation).

    Returns:
        dict: Αναφορά αποτελεσμάτων.
    """
    logging.info(f"Starting backtest for {crypto_name}. Threshold: {buy_threshold}, Volume window: {window}")
    
    # Φόρτωση βαρών για το συγκεκριμένο crypto
    weights = load_weights(crypto_name)

    signals = []
    failed_volume_confirmation = []
    fallback_success = []

    for i in range(len(df)):
        row = df.iloc[:i + 1].copy()  # Δημιουργία αντιγράφου για αποφυγή SettingWithCopyWarning

        # ===========================
        # Υπολογισμός Δεικτών
        # ===========================
        adx, atr = calculate_adx(row)
        rsi = calculate_rsi(row)
        bollinger_upper, bollinger_lower = calculate_bollinger_bands(row)
        vwap = calculate_vwap(row)

        # Υπολογισμός MACD
        short_ema = row['close'].ewm(span=12, adjust=False).mean()
        long_ema = row['close'].ewm(span=26, adjust=False).mean()
        macd = short_ema - long_ema
        signal = macd.ewm(span=9, adjust=False).mean()

        # Παίρνουμε την τελευταία τιμή για MACD και signal
        macd_last = macd.iloc[-1]
        signal_last = signal.iloc[-1]

        rsi_last = rsi.iloc[-1]
        bollinger_upper_last = bollinger_upper.iloc[-1]
        bollinger_lower_last = bollinger_lower.iloc[-1]
        current_price = row['close'].iloc[-1]
        vwap_last = vwap.iloc[-1]

        # ===========================
        # Υπολογισμός Score System
        # ===========================
        score = 0
        scores = {}

        # MACD
        if macd_last > signal_last:
            raw_score = 1 if macd_last > 0 else 0.3
        else:
            raw_score = -1
        scores['macd'] = weights['macd'] * raw_score
        score += scores['macd']

        # RSI
        if rsi_last < 25:  # Αντί για 20
            raw_score = 1.5  # Πολύ ισχυρό bullish σήμα (βαθιά υπερπουλημένη αγορά)
        elif 25 <= rsi_last < 35:  # Αντί για 30
            raw_score = 1  # Ισχυρό bullish σήμα
        elif 35 <= rsi_last < 45:  # Αντί για 40
            raw_score = 0.5  # Αδύναμο bullish σήμα
        elif 45 <= rsi_last <= 55:  # Αντί για 40-60
            raw_score = 0.1 if rsi_last < 50 else -0.1  # Ελαφρύ bullish ή bearish bias
        elif 55 < rsi_last <= 65:  # Αντί για 60-70
            raw_score = -0.5  # Αδύναμο bearish σήμα
        elif 65 < rsi_last <= 75:  # Αντί για 70-80
            raw_score = -0.3  # Ασθενές bearish σήμα
        else:  # rsi_last > 75 (αντί για 80)
            raw_score = -0.5  # Πολύ ισχυρό bearish σήμα (βαθιά υπεραγορασμένη αγορά)

        scores['rsi'] = weights['rsi'] * raw_score
        score += scores['rsi']

        # Bollinger Bands
        if current_price <= bollinger_lower_last:
            raw_score = 1.5 if current_price < bollinger_lower_last * 0.98 else 1
        elif current_price >= bollinger_upper_last:
            raw_score = -0.5 if current_price > bollinger_upper_last * 1.02 else -0.3
        else:
            raw_score = 0
        scores['bollinger'] = weights['bollinger'] * raw_score
        score += scores['bollinger']

        # VWAP
        vwap_diff = abs(current_price - vwap_last) / vwap_last
        if current_price > vwap_last:
            raw_score = 0.3 if vwap_diff > 0.05 else (0.5 if vwap_diff > 0.03 else 1)
        elif current_price < vwap_last:
            raw_score = -0.3 if vwap_diff > 0.05 else (-0.5 if vwap_diff > 0.03 else -1)
        else:
            raw_score = 0
        scores['vwap'] = weights['vwap'] * raw_score
        score += scores['vwap']

        
        # Έλεγχος Threshold
        if score >= buy_threshold:
            volume_confirmation, current_volume, avg_volume = calculate_volume_confirmation(row, window=window)
            if not volume_confirmation:
                failed_volume_confirmation.append((row.index[-1], current_price))
                if fallback_conditions(row):
                    fallback_success.append((row.index[-1], current_price))
                continue

            signals.append((row.index[-1], current_price))

    # ===========================
    # Αναφορά Αποτελεσμάτων
    # ===========================
    results = {
        'total_signals': len(signals),
        'failed_volume_confirmation': len(failed_volume_confirmation),
        'fallback_success': len(fallback_success),
        'signals': signals,
        'failed_volume_confirmation_list': failed_volume_confirmation,
        'fallback_success_list': fallback_success
    }

    # Logging Συνολικών Αποτελεσμάτων
    logging.info("Backtest completed.")
    logging.info(f"Total Positive Signals: {results['total_signals']}")
    logging.info(f"Failed Volume confirmation: {results['failed_volume_confirmation']}")
    logging.info(f"Positive Fallback Signals: {results['fallback_success']}")
    
    return results



# ===========================
# Εφαρμογή Backtesting
# ===========================
if __name__ == "__main__":
    # Φόρτωση δεδομένων
    file_path = "coin_Bitcoin.csv"  # Αρχείο με ιστορικά δεδομένα
    df = pd.read_csv(file_path)

    # Μετονομασία στηλών για συμβατότητα
    df.rename(columns={
        'High': 'high',
        'Low': 'low',
        'Open': 'open',
        'Close': 'close',
        'Volume': 'volume',
        'Date': 'date'
    }, inplace=True)

    # Μετατροπή της ημερομηνίας σε DatetimeIndex
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    # Επιλογή μόνο των απαραίτητων στηλών
    df = df[['open', 'high', 'low', 'close', 'volume']]

    # Βάρη για δείκτες
    weights = {
        "macd": 0.25,
        "rsi": 0.30,
        "bollinger": 0.25,
        "vwap": 0.20
    }

    # Εκτέλεση backtesting
    results = backtest(df, crypto_name="BTC", buy_threshold=0.4)

    # Εμφάνιση αποτελεσμάτων
    print("Total Positive Signals:", results['total_signals'])
    print("Failed Volume confirmation:", results['failed_volume_confirmation'])
    print("Positive Fallback Signals:", results['fallback_success'])
