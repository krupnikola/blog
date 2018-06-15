
from app1 import create_app, db, cli
from app1.models import User, Post, Message, Notification

# first - we call the application factory function that creates the app instance
app = create_app()
# second - we register the cli commands defined in cli file
# this had to be done in this way because cli commands are registered as soon as the app object is created
# and it can not work with current_app because that is a context variable available ONLY DURING A REQUEST
cli.register(app)


# ovaj dekorator odredjuje sta ce biti importovano u flask shell kada se on pokrene
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Message': Message,
            'Notification': Notification}
