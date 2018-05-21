from app1 import db, login, app
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import jwt
from time import time

# not a model class table since we'll not use it directly but through SQLAlchemy
# to get the foreign keys
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # for the given follower user, this attribute will give the list of users that this user is following
    follows = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')


    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.follows.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.follows.remove(user)

    def is_following(self, user):
        return self.follows.filter(followers.c.followed_id == user.id).count() > 0

    # list of posts that user is following
    def followed_posts(self):
        # posts table and followers table are joined to display only posts from followed users
        followed = Post.query.join(
            followers, followers.c.followed_id == Post.user_id).filter(
                followers.c.follower_id == self.id)
        # posts from users that user is following are combined with user-own posts and displayed together - SQL UNION statement
        return followed.union(self.posts).order_by(Post.timestamp.desc())

    # generates token for password reset when called for a particular user
    # we define the fields in the token in form of a dictionary
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in},
            # adds .decode at the end because token encoder returns byte string and
            # we want normal string to work with 
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    # verifies the received token
    # made it as a static method because user is unknown in this moment so this method can not be called on 
    # a user object
    @staticmethod
    def verify_reset_password_token(token):
        try:
            # we are taking the id of the user from the dictionary under the key ['reset_password']
            # that is returned from token if the token iz validated
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            # returning none just not to break the app if the user is unknown
            return None
        # getting the user object back as a return value based on user.ID
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post {}>'.format(self.body)