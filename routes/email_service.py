import smtplib
from email.mime.text import MIMEText

def send_email(sender,
               password,
               receiver,
               subject,
               body):

    message = MIMEText(body)

    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receiver

    with smtplib.SMTP("smtp.gmail.com", 587) as server:

        server.starttls()

        server.login(sender, password)

        server.send_message(message)