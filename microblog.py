
from app1 import app, db, cli
from app1.models import User, Post



# ovaj dekorator odredjuje sta ce biti importovano u flask shell kada se on pokrene
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}
