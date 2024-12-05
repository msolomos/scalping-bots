import pandas as pd
import matplotlib.pyplot as plt
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment
from base64 import b64encode
from datetime import datetime

# Στατική διαδρομή αρχείου CSV
FILE_PATH = "/opt/python/scalping-bot/SOLANA/crypto_scores.csv"
SENDGRID_API_KEY = "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"

# Δηλώσεις για αποστολέα και παραλήπτη
EMAIL_SENDER = "info@f2d.gr"  # Διεύθυνση αποστολέα
EMAIL_RECIPIENT = "info@f2d.gr"  # Διεύθυνση παραλήπτη

def process_and_email_csv_with_sendgrid():
    try:
        # Ανάγνωση αρχείου CSV
        if not os.path.exists(FILE_PATH):
            raise FileNotFoundError("csv file not found.")
        
        df = pd.read_csv(FILE_PATH)
        
        # Φιλτράρισμα για το SOLANA
        df_solana = df[df['bot_name'].str.contains("SOL", case=False)]
        
        if df_solana.empty:
            print("no data found for solana.")
            return
        
        # Μετατροπή score σε αριθμητική μορφή
        df_solana['score'] = pd.to_numeric(df_solana['score'], errors='coerce')
        
        # Αφαίρεση NaN τιμών από score
        df_solana = df_solana.dropna(subset=['score'])

        # Μετατροπή timestamp σε datetime
        df_solana['timestamp'] = pd.to_datetime(df_solana['timestamp'], format="%d/%m/%Y %H:%M:%S")
        
        # Δημιουργία γραφήματος
        plt.figure(figsize=(12, 6))
        plt.plot(df_solana['timestamp'], df_solana['current_price'], label="Τιμή Solana")
        
        # Φιλτράρισμα εγγραφών με score > 0.1
        df_high_score = df_solana[df_solana['score'] > 0.1]

        # Επαλήθευση εγγραφών με score > 0.1
        print(f"records with score > 0.1: {len(df_high_score)}")
        print(df_high_score[['timestamp', 'current_price', 'score']])
        
        # Προσθήκη στο γράφημα
        plt.scatter(
            df_high_score['timestamp'], 
            df_high_score['current_price'], 
            color="red", 
            label="Σκορ > 0.1",
            zorder=5
        )
        
        # Προσαρμογές γραφήματος
        plt.xlabel("Ώρα")
        plt.ylabel("Τιμή (USD)")
        plt.title("Διακύμανση Τιμής Solana με Σκορ > 0.1")
        plt.legend()
        plt.grid(True)

        # Ρυθμίσεις για τα Labels στον άξονα Χ (μόνο ώρες)
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%H:%M"))
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.HourLocator(interval=1))
        plt.xticks(rotation=45)
        
        # Αποθήκευση γραφήματος
        image_path = "solana_price_chart.png"
        plt.savefig(image_path, bbox_inches="tight")
        plt.close()
        
        # Αποστολή email μέσω SendGrid
        send_email_with_chart(image_path, "Ημερήσιο Γράφημα Solana")
        
        # Διαγραφή αρχείου εικόνας
        os.remove(file_path)
        os.remove(image_path)
        print("files were deleted successfully.")
    
    except Exception as e:
        print(f"Σφάλμα: {e}")

def send_email_with_chart(image_path, subject):
    try:
        # Φόρτωση εικόνας και κωδικοποίηση σε Base64
        with open(image_path, 'rb') as img_file:
            encoded_image = b64encode(img_file.read()).decode()
        
        # Δημιουργία περιεχομένου email
        html_content = """
        Δείτε το ημερήσιο γράφημα Solana που επισυνάπτεται.
        """
        
        # Δημιουργία email μέσω SendGrid
        message = Mail(
            from_email=EMAIL_SENDER,
            to_emails=EMAIL_RECIPIENT,
            subject=subject,
            html_content=html_content
        )
        
        # Επισύναψη εικόνας
        attachment = Attachment()
        attachment.file_content = encoded_image
        attachment.file_type = "image/png"
        attachment.file_name = os.path.basename(image_path)
        attachment.disposition = "attachment"
        message.attachment = attachment
        
        # Αποστολή μέσω SendGrid API
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        print("Email sent successfully!")
    
    except Exception as e:
        print(f"Error sending email: {e}")

# Παράδειγμα εκτέλεσης
process_and_email_csv_with_sendgrid()
