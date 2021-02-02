import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

port = 465  # For SSL
password = 'noreplytwitter4menpasswordissimple'
message_subject = "Password Reset: Twitter 4 men support"
sender_email = "noreply.twitter4men@gmail.com"

# Content
MIME_content = 'This is a random string message'

class Mailer():
    def __init__(self, to):
        self.message = MIMEMultipart()
        self.message["Subject"] = message_subject
        self.message["From"] = sender_email
        self.message["To"] = to
        self.MIME_message = """<h1>Hey, emailing works!</h1><p>This is a paragraph</p>"""
    
    def send(self):
        # Turn these into plain/html MIMEText objects
        the_message = MIMEText(self.MIME_message, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        self.message.attach(the_message)

        self.code = random.randint(100000, 999999)
        
        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, self.to, self.message.as_string()
            )
        
        return self.code