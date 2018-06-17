from app1 import db, login
from flask import current_app
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import jwt
from time import time
from app1.search import add_to_index, remove_from_index, query_index
import json
import redis
import rq


# bunch of functions that interact between SQLAlchemy and elastic
class SearchableMixin(object):
    @classmethod
    # this function wraps the query_search to replace the list of IDs with actual objects
    # and return them in the same order as the elastic found them - this is very important since elastic is
    # giving the results based on the closest match!
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        # important to see that function is returning ordered QUERY OBJECT, not the queries themselves,
        # and to get the queries we need to add .all() or .first() etc
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    # here we are catching changes in the current session before they are committed
    def before_commit(cls, session):
        session._changes = {
            'add': [obj for obj in session.new if isinstance(obj, cls)],
            'update': [obj for obj in session.dirty if isinstance(obj, cls)],
            'delete': [obj for obj in session.deleted if isinstance(obj, cls)]
        }

    @classmethod
    # adding the changes to elastic database after the changes were committed
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    # method called to add existing entries to the index, to index the existing posts
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


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
    # because there are two foreign keys in Messages table pointing to User table, we need to specify
    # which foreign key we want to use with every relationship
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)
    notifications = db.relationship('Notification', backref='user',
                                    lazy='dynamic')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')

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
                          current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    # verifies the received token
    # made it as a static method because user is unknown in this moment so this method can not be called on 
    # a user object
    @staticmethod
    def verify_reset_password_token(token):
        try:
            # we are taking the id of the user from the dictionary under the key ['reset_password']
            # that is returned from token if the token iz validated
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            # returning none just not to break the app if the user is unknown
            return None
        # getting the user object back as a return value based on user.ID
        return User.query.get(id)

    # with this we get the number of new messages by filtering them out by comparing last_seen times
    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(Message.timestamp > last_read_time).count()

    # helper method that will generate new notification for the user
    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        #
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n


    # helper for creating the tasks for the particular user
    def launch_task(self, name, description, *args, **kwargs):
        # app1.main.tasks is a module where all task functions are stored and 'name' attribute is the name of the function inside module
        rq_job = current_app.task_queue.enqueue('app1.main.tasks.' + name, self.id,
                                                *args, **kwargs)
        # task object for the database, important is that id is passed to the database here! DB is not generating the id field
        # (look at the Task model)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        db.session.add(task)
        return task

    # returns all tasks for the user that are not finished (complete = False)
    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
        complete=False).first()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(SearchableMixin, db.Model):
    # this item is ignored by SQLAlchemy but tells us what field we want to index to elastic
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


# event listeners related to elastic, added to listen for changes in the post table and trigger
# the changes in elastic database to automatically index the new posts
db.event.listen(db.session, 'before_commit', Post.before_commit)
db.event.listen(db.session, 'after_commit', Post.after_commit)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # we assign a name for every notification, making this model flexible for different types of notifications
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # was not used python datetime module, unix timestamp was used because of JavaScript compatibility because
    # this entries will be used with javascript
    timestamp = db.Column(db.Float, index=True, default=time)
    # this will be a JSON string
    payload_json = db.Column(db.Text)

    def get_data(self):
        # this helper function takes JSON and decodes it to a Py data structure
        return json.loads(str(self.payload_json))


# model for Redis task queuing, tasks are stored in the db
class Task(db.Model):
    # id is not an integer because we are taking the id from redis, since redis id is already creating unique id for every task
    # we just put it in the database
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    # helper method that represents the task
    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    # wrapper that gets the job instance and then gets the progress attribute from the job metadata
    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100