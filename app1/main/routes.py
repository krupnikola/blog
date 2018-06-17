from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from app1 import db
from app1.main.forms import EditProfileForm, PostForm, SearchForm, MessageForm
from app1.models import User, Post, Message, Notification
from app1.translate import translate
from app1.main import bp


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        # no need to put .add() before committing the new timestamp
        # because the user is already in the database, we are just submitting the changes
        db.session.commit()
        # the search form should be available on every page the user is viewing,
        # so we store it in the g object so it is available during full application context
        g.search_form = SearchForm()
    # during every request, locale is set for a particular request
    # and now it can be included in base template into moment package
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
# login decorator is set to protect the index page from a non-logged in users, feature of flask_login
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    # requested page number is saved to a variable, taken from the query string with the 'request' package from flask
    # has to be converted to integer because the return value would be a string natively
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    # making links for next and previous page for navigation
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    # the return of the paginate is pagination object, not a list as it is with .all(), so to access list of items,
    # we need to add .items to the pagination object = posts
    return render_template('main/index.html', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    # we'll use index template to display all the posts, but without the form that is present
    # on /index page - this is accomplished by adding {% if form %} condition in the index.html
    # to check if the form exists in the route definition and if it is being passed to the template
    return render_template('main/index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
# when there is a dynamic component in URL, that dynamic piece is being sent as an argument to
# view function
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('main/user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('main/edit_profile.html', title=_('Edit Profile'),
                           form=form)


# route for the user that a logged in user wants to start following
@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('main.user', username=username))


# this is a translate route with only the POST method
# it uses the translate function defined in translate.py
# ATTENTION - data is pulled from request in a different way then when we have flask form and we are making POST request
# now we have a data already on the page, so we need to take it from the query string
@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    # inside, "translate" function defined inside translate.py is called
    # the POST request in this route does not originate from wtf form as in other cases so we access fields in
    # the request directly from the request object and not through WTF FORM
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@bp.route('/search', methods=['GET'])
@login_required
def search():
    # since the form is submitted with GET method, we can not use Flask-WTF validate_on_submit() since
    # it only supports POST method, so we use only validate() and
    # if the user submitted empty search form he is redirected to the page with all posts
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('main/search.html', title=_('Search'), posts=posts,
                         next_url=next_url, prev_url=prev_url)


# route for popup when mouse hover over username
@bp.route('/user/<username>/popup', methods=['GET'])
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('main/user_popup.html', user=user)


# route for sending messages
@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    # load recipient user from the database
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(msg)
        # as arguments, we pass the name of the notification and number of new messages
        user.add_notification('unread_message_count', user.new_messages())
        # because add_notification alters the Notification table, this changes must be commited
        db.session.commit()
        flash(_('Your message has been sent'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('main/send_message.html', title=_('Send Message'), form=form, recipient=recipient)


# route for reading private messages by user
@bp.route('/messages', methods=['GET'])
def messages():
    # first we update the last read time in the db for the current user
    current_user.last_message_read_time = datetime.utcnow()
    # reset also the notification about unread messages to zero since the user is reading them in the moment
    current_user.add_notification("unread_message_count", 0)
    # commit the change to the last seen time in the database
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(Message.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) if messages.has_prev else None
    # the return of the paginate is pagination object, not a list as it is with .all(), so to access list of items,
    # we need to add .items to the pagination object = messages
    return render_template('main/messages.html', messages=messages.items, next_url=next_url, prev_url=prev_url)


# route for client to retrieve notifications for the logged in user via Ajax call
@bp.route('/notifications')
@login_required
def notifications():
    # variable that holds the last time client requested the notifications, default is 0.0 (float number)
    since = request.args.get('since', 0.0, type=float)
    # this variable will hold all the notifications pulled from the database since the last 'since' moment
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    # we make the return value a JSON list of notifications because that is easier for the client (JS) to handle
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


# route for exporting blogs of the currently logged on user
@bp.route('/export_posts')
@login_required
def export_posts():
    # if user is already running an export...
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        # launch the export through launch_task helper method
        current_user.launch_task('export_posts', _('Exporting posts...'))
        # session must be commited since this helper function modifies the database
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))