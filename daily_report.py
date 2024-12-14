import json
from datetime import datetime
import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Cc, Content, Attachment
from sendgrid import SendGridAPIClient
from base64 import b64encode
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Συνάρτηση για να φορτώσει τα κλειδιά από το αρχείο JSON
def load_keys(json_path="/opt/python/scalping-bot/api_keys.json"):
    try:
        with open(json_path, "r") as file:
            keys = json.load(file)
            SENDGRID_API_KEY = keys.get("SENDGRID_API_KEY")

            if not SENDGRID_API_KEY:
                raise ValueError("sendgrid key is missing in the JSON file.")

            return SENDGRID_API_KEY
    except FileNotFoundError:
        raise FileNotFoundError(f"The specified JSON file '{json_path}' was not found.")
    except json.JSONDecodeError:
        raise ValueError(f"The JSON file '{json_path}' is not properly formatted.")

# Φόρτωση των κλειδιών
SENDGRID_API_KEY = load_keys()

# Λίστα με τα paths των αρχείων state.json για κάθε bot
bot_files = [
    '/opt/python/scalping-bot/AVAX/state.json', 
    '/opt/python/scalping-bot/SOLANA/state.json', 
    '/opt/python/scalping-bot/LITECOIN/state.json', 
    '/opt/python/scalping-bot/ETHEREUM/state.json', 
    '/opt/python/scalping-bot/BITCOIN/state.json', 
    '/opt/python/scalping-bot/XRP/state.json',
    '/opt/python/scalping-bot/CARDANO/state.json',
    '/opt/python/scalping-bot/POLKADOT/state.json',
    '/opt/python/scalping-bot/DOGECOIN/state.json', # Νέο bot    
    '/opt/python/scalping-bot/POLYGON/state.json',   # Νέο bot
    '/opt/python/scalping-bot/STELLAR/state.json', # Νέο bot
]

# Λίστα με τα ονόματα των bots
bot_names = ['AVAX', 'SOLANA', 'LITECOIN', 'ETHEREUM', 'BITCOIN', 'XRP', 'CARDANO', 'POLKADOT', 'DOGECOIN', 'POLYGON', 'STELLAR']

# Συνάρτηση για ανάγνωση των δεδομένων από το state.json κάθε bot
def analyze_bot_data(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r') as f:
        data = json.load(f)
    daily_profit = data.get('daily_profit', 0) or 0
    total_profit = data.get('total_profit', 0) or 0
    current_trades = data.get('current_trades', 0) or 0
    active_trade = data.get('active_trade', 0) or 0
    trade_amount = data.get('trade_amount', 0) or 0
    total_active_trade_value = active_trade * trade_amount
    
    # Διαχείριση δεύτερης θέσης
    second_trade_price = data.get('second_trade_price', 0)
    second_trade_amount = data.get('second_trade_amount', 0)
    average_trade_price = data.get('average_trade_price', 0)
    second_position_open = second_trade_price > 0 and second_trade_amount > 0
    second_trade_value = second_trade_price * second_trade_amount if second_position_open else 0

    return {
        'daily_profit': daily_profit,
        'total_profit': total_profit,
        'current_trades': current_trades,
        'active_trade': active_trade,
        'trade_amount': trade_amount,
        'total_active_trade_value': total_active_trade_value,
        'second_trade_price': second_trade_price,
        'second_trade_amount': second_trade_amount,
        'average_trade_price': average_trade_price,
        'second_trade_value': second_trade_value,
        'second_position_open': second_position_open
    }

# Ανάλυση δεδομένων για κάθε bot και αποθήκευση αποτελεσμάτων για ταξινόμηση
bot_data = []
for i, bot_file in enumerate(bot_files):
    result = analyze_bot_data(bot_file)
    if result:
        result['name'] = bot_names[i]  # Προσθήκη του ονόματος του bot στο dictionary
        bot_data.append(result)

# Ταξινόμηση των bots με βάση την ανοικτή θέση (total_active_trade_value) από το μεγαλύτερο στο μικρότερο
bot_data = sorted(bot_data, key=lambda x: x['total_active_trade_value'], reverse=True)


# Δημιουργία HTML περιεχομένου με απλό πίνακα χωρίς εξωτερικό CSS ή Bootstrap
current_date = datetime.now().strftime('%d-%m-%Y')
table_rows = ''.join([
    f"""
    <tr style="{'background-color: #ffcccc;' if bot['second_position_open'] else ''}">
        <td>{bot['name']}</td>
        <td>{bot['current_trades']}</td>
        <td>{bot['trade_amount']:.2f}</td>
        <td>{bot['active_trade']:.2f} EUR</td>
        <td>{bot['total_active_trade_value']:.2f} EUR</td>
        <td>{bot['second_trade_price']:.2f} EUR</td>
        <td>{bot['second_trade_value']:.2f} EUR</td>        
        <td>{bot['average_trade_price']:.2f} EUR</td>        
        <td>{bot['daily_profit']:.2f} EUR</td>
        <td>{bot['total_profit']:.2f} EUR</td>
    </tr>
    """ for bot in bot_data
])

report_html = f"""
<html>
<body>
    <h2>Ημερήσια Αναφορά {current_date}</h2>
    <p><strong>Ημερήσιο Κέρδος:</strong> {sum(bot['daily_profit'] for bot in bot_data):.2f} EUR</p>
    <p><strong>Συνολικό Κέρδος:</strong> {sum(bot['total_profit'] for bot in bot_data):.2f} EUR</p>
    <p><strong>Ημερήσιος Αριθμός Συναλλαγών:</strong> {sum(bot['current_trades'] for bot in bot_data)}</p>
    <p><strong>Συνολικό Άνοιγμα:</strong> {sum(bot['total_active_trade_value'] for bot in bot_data):.2f} EUR</p>
    <h3>Λεπτομέρειες ανά bot:</h3>
    <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 80%; border: 1px solid #eeeeee;">
        <thead>
            <tr style="background-color: #d3d3d3; color: #000;">
                <th>Bot Name</th>
                <th>Συναλλαγές</th>
                <th>Τεμάχια</th>
                <th>Τιμή Αγοράς</th>
                <th>Συνολικό Άνοιγμα</th>
                <th>Δεύτερη Τιμή Αγοράς</th>
                <th>Αξία Δεύτερης Θέσης</th>                
                <th>Μέσος Ορος DCA</th>
                <th>Κέρδος Ημέρας</th>
                <th>Συνολικό Κέρδος</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    <p><i>Τα bots με ανοιχτή δεύτερη θέση επισημαίνονται με κόκκινο φόντο.</i></p>
</body>
</html>
"""

# Εκτύπωση της αναφοράς για έλεγχο
#print(report_html)

# Δημιουργία φακέλου REPORTS αν δεν υπάρχει
reports_dir = "/opt/python/scalping-bot/REPORTS"
if not os.path.exists(reports_dir):
    os.makedirs(reports_dir)

# Αποθήκευση αναφοράς σε αρχείο μέσα στον φάκελο REPORTS με utf-8 κωδικοποίηση
report_filename = os.path.join(reports_dir, f"daily_report_{current_date}.txt")
with open(report_filename, "w", encoding="utf-8") as report_file:
    report_file.write(report_html)

# Συνάρτηση για αποστολή email μέσω SendGrid
def send_email_report(api_key, sender_email, recipient_email, cc_email, subject, report_text, report_html):
    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    
    # Δημιουργία email
    from_email = Email(sender_email)
    to_email = To(recipient_email)
    cc_email = Cc(cc_email) if cc_email else None  # Προσθήκη CC αν οριστεί
    content = Content("text/html", report_html)

    # Δημιουργία του μηνύματος
    mail = Mail(from_email=from_email, to_emails=to_email, subject=subject, html_content=content)

    # Προσθήκη CC αν υπάρχει
    if cc_email:
        mail.add_cc(cc_email)    
    
    # # Προσθήκη του συνημμένου αρχείου κειμένου
    # with open(report_filename, 'rb') as f:
        # data = f.read()
        # encoded = b64encode(data).decode()

    # attachment = Attachment()
    # attachment.file_content = encoded
    # attachment.file_type = "text/plain"
    # attachment.file_name = report_filename
    # attachment.disposition = "attachment"
    # mail.add_attachment(attachment)

    try:
        response = sg.send(mail)
        print(f"Email στάλθηκε! Κωδικός: {response.status_code}")
    except Exception as e:
        print(f"Σφάλμα κατά την αποστολή του email: {e}")

# Κλήση της συνάρτησης με τα δεδομένα του report
api_key = SENDGRID_API_KEY
sender_email = "info@f2d.gr"
recipient_email = "info@f2d.gr"
cc_email = ""
subject = f"Scalping bots - Ημερήσια Αναφορά {current_date}"

# Κλήση της συνάρτησης αποστολής email
send_email_report(api_key, sender_email, recipient_email, cc_email, subject, report_html, report_html)
