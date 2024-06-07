import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_order_confirmation_email(recipient_email: str, order_id: str, first_name: str):
    smtp_host = os.getenv('SMTP_HOST')
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_sender_email = os.getenv('SMTP_SENDER_EMAIL')

    if not all([smtp_host, smtp_user, smtp_password, smtp_sender_email]):
        print("One or more required environment variables are missing.")
        return False

    msg = MIMEMultipart()
    msg['From'] = smtp_sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Narudžba zaprimljena"
    body = f"""
    <html>
    <body>
        <p>Poštovani {first_name},</p>
        <p>Vaša narudžba s brojem <strong>{order_id}</strong> je zaprimljena.</p>
        <p>Hvala vam na povjerenju!</p>
        <p>Srdačan pozdrav!</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    server = None
    try:
        server = smtplib.SMTP(smtp_host, 587)
        server.starttls()
        server.login(smtp_user, smtp_password)

        server.sendmail(smtp_sender_email, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    finally:
        if server:
            server.quit()
