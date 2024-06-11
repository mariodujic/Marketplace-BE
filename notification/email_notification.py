import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

smtp_host = None
smtp_user = None
smtp_password = None
smtp_sender_email = None
admin_emails = None


def initialize_email_notification_env_variables():
    global smtp_host, smtp_user, smtp_password, smtp_sender_email, admin_emails
    smtp_host = os.getenv('SMTP_HOST')
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_sender_email = os.getenv('SMTP_SENDER_EMAIL')
    admin_emails = os.getenv('ADMIN_EMAILS')


def send_order_confirmation_email_to_customer(recipient_email: str, order_id: str, first_name: str):
    if not all([smtp_host, smtp_user, smtp_password, smtp_sender_email]):
        print("One or more required SMTP config environment variables are missing.")
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
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_sender_email, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    finally:
        if server:
            server.quit()


def send_order_confirmation_email_to_admin(
        customer_email: str,
        order_id: str,
        first_name: str,
        last_name: str,
        payment_id: str,
        shipping_address: str
):
    if not all([smtp_host, smtp_user, smtp_password, smtp_sender_email]):
        print("One or more required SMTP config environment variables are missing.")
        return False

    admin_emails_list = admin_emails.split(',')

    msg = MIMEMultipart()
    msg['From'] = smtp_sender_email
    msg['To'] = ', '.join(admin_emails_list)
    msg['Subject'] = f'Narudžba broj {order_id} zaprimljena'
    body = f"""
    <html>
    <body>
        <p>Poštovani admin,</p>
        <p>Zaprimljena je nova narudžba pod brojem <strong>{order_id}</strong>.</p>
        <p>Ime i prezime: <strong>{first_name} {last_name}</strong>.</p>
        <p>Email: <strong>{customer_email}</strong>.</p>
        <p>ID plaćanja: <strong>{payment_id}</strong>.</p>
        <p>Adresa slanja: <strong>{shipping_address}</strong>.</p>
        <p>Srdačan pozdrav!</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    server = None
    try:
        server = smtplib.SMTP(smtp_host, 587)
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_sender_email, admin_emails_list, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    finally:
        if server:
            server.quit()


def send_password_reset_email(recipient_email: str, reset_link: str) -> bool:
    if not all([smtp_host, smtp_user, smtp_password, smtp_sender_email]):
        print("One or more required SMTP config environment variables are missing.")
        return False

    subject = "Zahtjev za resetiranje lozinke"
    body = f"""
       <html>
       <body>
           <p>Poštovani,</p>
           <p>Zatražili ste resetiranje lozinke. Kliknite na donji link kako biste resetirali svoju lozinku:</p>
           <p><a href="{reset_link}">Resetiraj lozinku</a></p>
           <p>Ako niste zatražili ovu radnju, ignorirajte ovaj email.</p>
           <p>S poštovanjem,</p>
           <p>Vaš shop</p>
       </body>
       </html>
       """

    msg = MIMEMultipart()
    msg['From'] = smtp_sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    server = None
    try:
        server = smtplib.SMTP(smtp_host, 587)
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_sender_email, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    finally:
        if server:
            server.quit()
