from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from datetime import datetime
from app1 import app, db
from flask_login import login_user, current_user, logout_user, login_required
from app1.forms import LoginForm, RegistrationForm, EditProfileForm
from app1.models import User


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        # no need to put .add() before commit because the user is already in the database, we are just submitting the changes
        db.session.commit()


@app.route('/')
@app.route('/index')
# login decorator is set to protect the index page from a non-logged in users, feature of flask_login
@login_required
def index():
    posts = [
        {
            'author': {'username': 'John'},
            'body': "Beautiful day in Portland!"
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # first, checks if the user is logged in already
    # if yes, redirects away from the login form to /index
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("invalid username or password")
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        # save the querystring part of the URL for later redirection, feature of flask.redirect
        next_page = request.args.get('next')
        # security measure, if netloc part of the next_page querystring is not empty, never redirect to it
        # if someone inserts http://something as a querystring it is a problem
        # # in other words, if next = absolute URL, do not redirect to it
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # first, checks if the user is logged in already
    # if yes, redirects away from the login form to /index
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        # these are flask-sqlalchemy sessions, practically database transactions
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user")
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
# when there is a dynamic component in URL, that dynamic piece is being sent as an argument to
# view function
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'},
    ]
    return render_template('user.html', user=user, posts=posts)


@app.route('/edit_profile', methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username= form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('user', username = current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)
