#!/usr/bin/env python

import calendar
import datetime
from functools import wraps
from collections import defaultdict
import ConfigParser, random
from flask import Flask, request, Response, session, g, redirect, url_for, \
    abort, render_template, flash, get_flashed_messages, current_app, \
    jsonify
from flaskext.wtf import Form, DateField, TextField, Required, \
    validators, PasswordField, TextAreaField, DecimalField, HiddenField, \
    SubmitInput

from decimal import Decimal
from urlparse import urlparse

config = ConfigParser.ConfigParser()
config.read(["config.ini.sample", "config.ini"])

from ct.apis import SimpleAPI
from ct.activity import Activity

def ct_format_date(year, month, day):
    return "%s-%02d-%02d" % (year, month, day)
    
def ct_get_month(year, month):
    ndays = calendar.monthrange(year, month)[1]
    days = xrange(1, ndays + 1)
    keys = [ct_format_date(year, month, day) for day in days]
    activities_by_date = dict(map(lambda x: (x, []), keys))
    for activity in g.ct.get_activities(year, month):
        if activity.duration <= 0:
            continue

        date = activity.day.strftime("%Y-%m-%d")
        activities_by_date[date].append({
            'id': activity.project_id,
            'comment': activity.comment,
            'duration': str(activity.duration),
            'day': date
        })
    return activities_by_date

def ct_get_day(year, month, day):
    all_activities = ct_get_month(year, month)
    date = ct_format_date(year, month, day)
    return { date: all_activities[date] }

def is_safe_url(target):
    """Only redirect to URLs on the same host."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


class UserForm(Form):
    username = TextField(u'Brukernavn', [validators.Length(min=3, max=25)], [], u'Ditt brukernavn')
    password = PasswordField(u'Passord', [validators.Length(min=4)], [], u'Minimum 4 tegn')
    next_page = HiddenField()

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        
        if not self.next_page.data:
            self.next_page.data = request.args.get('next') or request.referrer

    def validate_next_page(self, field):
        if field.data and not is_safe_url(field.data):
            field.data = None
            
    def validate_username(self, field):
        username = field.data.lower().strip()
        if not "bouvet\\" in username:
            username = "bouvet\\" + username
        field.data = username

    def validate_password(self, field):
        field.data = field.data.strip()


def do_ct_login(username, password):
    server = config.get("server", "ct_url")
    ct = SimpleAPI(server)
    logged_in = ct.login(username, password)
    if logged_in:
        session['user'] = username
        session['ct'] = ct

    return logged_in

def is_logged_in():
    return session.has_key('ct') and session['ct'].valid_session()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if is_logged_in():
            g.ct = session['ct']
            return f(*args, **kwargs)
        return redirect(url_for('login', next=request.url))
    return decorated_function


app = Flask(__name__)
app.config['DEBUG'] = config.getboolean("server", "debug")
app.config['SECRET_KEY'] = config.get("server", "secret_key")

@app.route('/login', methods=['GET','POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))

    error = ""
    form = UserForm()
    if form.validate_on_submit():
        logged_in = do_ct_login(form.username.data, form.password.data)
        if logged_in:
            next_page = form.next_page.data or url_for('index')
            return redirect(next_page)
        else:
            error = "Username and password did not match."

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
def get_activities_by_month(year, month):
    return jsonify(activities=ct_get_month(year, month))

@app.route('/api/activities/<int:year>/<int:month>/<int:day>', methods=["GET"])
@login_required
def get_activities_by_day(year, month, day):
    return jsonify(activities=ct_get_day(year, month, day))

@app.route('/api/activities/<int:year>/<int:month>/<int:day>', methods=["PUT", "POST"])
@login_required
def set_activities_by_day(year, month, day):
    _, current_activities = ct_get_day(year, month, day).popitem()
    to_add = request.json['activities']
    to_delete = [x for x in current_activities if not x in to_add]

    for data in to_add:
        activity = activity_from_dict(data)
        g.ct.report_activity(activity)

    for data in to_delete:
        activity = activity_from_dict(data)
        g.ct.delete_activity(activity)
    return get_activities_by_day(year, month, day)

def activity_from_dict(data):
        year, month, day = [int(x) for x in data['day'].split("-")]
        date = datetime.date(year, month, day)
        duration = Decimal(data['duration'])
        return Activity(date, data['id'], data['duration'], data['comment'])

if __name__ == '__main__':
    host = config.get("server", "host")
    port = config.get("server", "port")
    app.run(host=host, port=int(port))
