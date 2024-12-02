from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Replace with your SendGrid API key
SENDGRID_API_KEY = "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"

message = Mail(
    from_email='info@f2d.gr',
    to_emails='msolomos2@gmail.com',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>'
)

try:
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(f"Error: {e}")
