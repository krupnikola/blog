# this are the functions that run in the worker process

import json
import sys
import time
from flask import render_template
from rq import get_current_job
from app1 import create_app, db
from app1.models import User, Post, Task
from app1.email import send_email

# app and the context must be created and pushed manually to be available for this process
app = create_app()
app.app_context().push()


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        # progress is taken from the metadata
        job.meta['progress'] = progress
        job.save_meta()
        # task is taken from the db based on id created by redis for every id ( that same id is the id in the database)
        task = Task.query.get(job.get_id())
        # her we introduce new type of the notification, progress notification
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()


def export_posts(user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = user.posts.count()
        for post in user.posts.order_by(Post.timestamp.asc()):
            data.append({'body': post.body,
                         'timestamp': post.timestamp.isoformat() + 'Z'})
            time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_posts)

        send_email('[Microblog] Your blog posts',
                sender=app.config['ADMINS'][0], recipients=[user.email],
                text_body=render_template('email/export_posts.txt', user=user),
                html_body=render_template('email/export_posts.html',
                                          user=user),
                # this is how flask-mail is expecting attachment to be served as an attribute, 3-piece tuple
                attachments=[('posts.json', 'application/json',
                              json.dumps({'posts': data}, indent=4))],
                sync=True)
    except:
        _set_task_progress(100)
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())