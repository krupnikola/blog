from flask_mail import Message
from app1 import mail
from flask import current_app
# package to allow asynchronous tasking in the app 
# to put the email sending task in the separate background thread
from threading import Thread



def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


# wrapper function for Message function to add custom attributes
def send_email(subject, sender, recipients, text_body, html_body, attachments=None, sync=None):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)

    if sync:
        mail.send(msg)

    else:

        Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
