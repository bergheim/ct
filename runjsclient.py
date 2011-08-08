#!/usr/bin/env python

from functools import wraps
from collections import defaultdict
import ConfigParser, random
from flask import Flask, request, Response, session, g, redirect, url_for, \
     abort, render_template, flash, get_flashed_messages, current_app, \
     jsonify
from flaskext.wtf import Form, DateField, TextField, Required, validators, PasswordField, TextAreaField, DecimalField, HiddenField, SubmitInput

from urlparse import urlparse

config = ConfigParser.ConfigParser()
config.read(["config.ini.sample", "config.ini"])

from ct.apis import SimpleAPI


def is_safe_url(target):
    """Only redirect to URLs on the same host."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_redirect_target():
    """Returns the redirect target we want to use.  Tries the 'next'
    parameter from GET and falls back to the referrer from the request.
    """
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

class RedirectForm(Form):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        return redirect(get_redirect_target() or url_for(endpoint, **values))

class UserForm(RedirectForm):
    username = TextField(u'Brukernavn', [validators.Length(min=3, max=25)], [], u'Ditt brukernavn')
    password = PasswordField(u'Passord', [], [], u'Minimum 4 tegn')

def do_ct_login(username, password):
    server = config.get("server", "ct_url")
    ct = SimpleAPI(server)
    logged_in = ct.login(username, password)
    if logged_in:
        session['user'] = username
        session['ct'] = ct

    raise

    return logged_in

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.has_key('ct') and session['ct'].valid_session():
            g.ct = session['ct']
            return f(*args, **kwargs)
        return redirect(url_for('login', next=request.url))
    return decorated_function


app = Flask(__name__)
app.config['DEBUG'] = config.getboolean("server", "debug")
app.config['SECRET_KEY'] = config.get("server", "secret_key")

@app.route('/login', methods=['GET','POST'])
def login():
    form = UserForm()
    if request.args.has_key("next"):
        form.next_page = HiddenField(default=request.args.get("next"))

    error = ""
    if form.validate_on_submit():
        username = form.username.data.lower().strip()
        if not "bouvet\\" in username:
            username = "bouvet\\" + username
        password = form.password.data.strip()
        logged_in = do_ct_login(username, password)
        g.user = username
        if logged_in:
            return form.redirect(endpoint=url_for('index', username=username))

    return render_template('login.html', form=form, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index', _external=True), 301)

@app.route('/')
@login_required
def index():
    return render_template('jsclient-bootstrap.html')

@app.route('/api/projects')
@login_required
def get_projects():
    projects = dict([(p.id, p.name) for p in g.ct.get_projects()])
    return jsonify(projects=projects)

@app.route('/api/activities/<int:year>/<int:month>')
@login_required
def get_activities(year, month):
    activities_by_date = defaultdict(lambda: [])
    for activity in g.ct.get_activities(year, month):
        date = activity.day.strftime("%Y-%m-%d")
        activities_by_date[date].append({
            'id': activity.project_id,
            'comment': activity.comment,
            'duration': str(activity.duration),
            'day': date
        })
    return jsonify(activities=activities_by_date)

if __name__ == '__main__':
    host = config.get("server", "host")
    port = config.get("server", "port")
    app.run(host=host, port=int(port))
