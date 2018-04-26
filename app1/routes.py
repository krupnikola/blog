from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from app1 import app, db
from flask_login import login_user, current_user, logout_user, login_required
from app1.forms import LoginForm, RegistrationForm
from app1.models import User



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


@app.route('/register', methods = ['GET', 'POST'])
def register():
    # first, checks if the user is logged in already
    # if yes, redirects away from the login form to /index
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user")
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

