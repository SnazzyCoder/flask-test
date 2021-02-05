from email import message
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template_string, Flask
from pathlib import Path
import random

port = 465  # For SSL
password = 'noreplytwitter4menpasswordissimple'
message_subject = "Password Reset: Twitter 4 men support"
sender_email = "noreply.twitter4men@gmail.com"

# Content
MIME_content = 'This is a random string message'

def send_mail(to):
    message = MIMEMultipart()
    message["Subject"] = message_subject
    message["From"] = sender_email
    message["To"] = to
    
    app = Flask(__name__)
    code = random.randint(100000, 999999)
    htmlmessage = """
        <div class="wrapper" style="text-align: center;">
            <h4>Hey, you've requested for a password reset.</h4>
            <p>
                <h2>{{code}}</h2>is your code.
            </p>
            <p>
                If this was not you, simply ignore this message.
            </p>
        </div>
    """
    
    with app.app_context():
        MIME_message = str(render_template_string(htmlmessage, code=code))

    # Turn these into plain/html MIMEText objects
    the_message = MIMEText(MIME_message, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(the_message)
    
    
    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, to, message.as_string()
        )
        
    return code