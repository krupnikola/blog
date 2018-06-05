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
def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # because current_app is a context aware variable which belongs to a current app instance as a proxy object
    # it keeps the context only within the same thread, so in this case we need to pass the application object
    # in order for mail functionality to work in a separate thread

    # that is achieved through special method
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
