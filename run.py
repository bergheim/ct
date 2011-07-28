#!/usr/bin/env python

import calendar
import datetime
import time
import operator
import pprint
from collections import defaultdict
from functools import wraps

from flask import Flask, request, Response, session, g, redirect, url_for, \
     abort, render_template, flash, get_flashed_messages, current_app
from flaskext.wtf import Form, DateField, TextField, Required, validators, PasswordField, TextAreaField, DecimalField, HiddenField
import ConfigParser, random
#from flaskext.login import LoginManager, UserMixin, \
#    login_required, login_user, logout_user
from beaker.middleware import SessionMiddleware
from ct.apis import RangeAPI

pp = pprint.PrettyPrinter(indent=4)

from urlparse import urlparse


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
        return redirect(get_redirect_target(endpoint, **values))

def debug():
    assert current_app.debug == False, "Debug:"

class MethodRewriteMiddleware(object):
    """Middleware for HTTP method rewriting.

    Snippet: http://flask.pocoo.org/snippets/38/
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if 'METHOD_OVERRIDE' in environ.get('QUERY_STRING', ''):
            args = url_decode(environ['QUERY_STRING'])
            method = args.get('__METHOD_OVERRIDE__')
            if method:
                method = method.encode('ascii', 'replace')
                environ['REQUEST_METHOD'] = method
        return self.app(environ, start_response)


config = ConfigParser.ConfigParser()
config.read(["config.ini.sample", "config.ini"])

session_opts = {
#    'session.type': 'ext:memcached',
#    'session.url': '127.0.0.1:11211',
    'session.data_dir': './cache',
}

app = Flask(__name__)
app.config['DEBUG'] = config.get("server", "debug")
app.config['SECRET_KEY'] = config.get("server", "secret_key")

#app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)
app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)

#login_manager = LoginManager()
#login_manager.setup_app(app)
#login_manager.login_view = "login"

def generate_calendar_month(date):
    c = calendar.Calendar()
    year = date.year
    month = date.month
    days = []
    for day in c.itermonthdays2(year, month):
        days.append(day)

    weeknumbers = []
    for day in c.monthdays2calendar(year, month):
        weekday,_ = day[0]

        if weekday == 0:
            weekday = 1

        tweek = datetime.date(year, month, weekday).isocalendar()
        weeknumbers.append((tweek[0], tweek[1]))


    cal = {}
    weeknumber = weeknumbers.pop(0)
    cal[weeknumber] = []
    for day, weekday in days:
        cal[weeknumber].append([day, weekday])

        if day > 0 and weekday == 6 and len(weeknumbers) > 0:
            weeknumber = weeknumbers.pop(0)
            cal[weeknumber] = []

    return cal


#class User(UserMixin):
class User():
    def __init__(self, id):
        self.id = id
        #if "user" in session:
        #    self.name = session['user']
        #else:
        self.username = self.name = str(id)

        self.password = self.name + "_secret"

    def __repr__(self):
        return "%s: %s" % (self.id, self.username)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        bsession = request.environ['beaker.session']
        if not valid_user() or not bsession.has_key('ct') or not bsession['ct'].valid_session():
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

class UserForm(RedirectForm):
    username = TextField(u'Brukernavn', [validators.Length(min=3, max=25)], [], u'Ditt brukernavn')
    password = PasswordField(u'Passord', [], [], u'Minimum 4 tegn')

class ActivityForm(Form):
    hours = DecimalField()
    notes = TextAreaField()

    #todo: this should be one generic method
    #def validate_existing_hours(form, field):
    #    if field.data != fresh lookup:
    #        raise ValidationError("Edited since you opened it")

    #def __init__(self, id=0):
    #    if id:
    #        # fetch record
    #        _existing_hours = 33
    #        _existing_notes = "dsaf"

class RangeForm(Form):
    @classmethod
    def default_from_date(cls):
        return datetime.date.today().replace(day=1)

    @classmethod
    def default_to_date(cls):
        today = datetime.date.today()
        _, ndays = calendar.monthrange(today.year, today.month)
        return today.replace(day=ndays)

    from_date = DateField(
        u'Fra dato',
        default=lambda: RangeForm.default_from_date(),
        format='%d.%m.%Y')
    to_date = DateField(
        u'Til dato',
        default=lambda: RangeForm.default_to_date(),
        format='%d.%m.%Y')


def valid_user():
    return 'user' in session

def redirect_if_invalid_user():
    if not valid_user():
        flash(request.url, 'redirect')
        return redirect_to_login()
    return True

def redirect_to_login():
    return redirect(url_for('login'))

def do_ct_login(username, password):
    server = config.get("server", "ct_url")
    bsession = request.environ['beaker.session']
    ct = RangeAPI(server)
    logged_in = ct.login(username, password)
    if logged_in:
        session['user'] = username
        bsession['ct'] = ct
        #FIXME: for some reason this does not work
        bsession['projects'] = ct.get_projects()
        bsession.save()

    return logged_in

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    form = UserForm()
    if request.args.has_key("next"):
        form.next_page = HiddenField(default=request.args.get("next"))

    error = ""
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        logged_in = do_ct_login(username, password)
        g.user = User(username)
        #login_user(g.user)
        if logged_in:
            return form.redirect(endpoint=url_for('show_user', username=username))

    return render_template('login.html', form=form, error=error)

@app.route('/logout')
def logout():
    print session
    #logout_user()
    session.clear()
    return redirect(url_for('index', _external=True), 301)

@app.errorhandler(401)
def page_not_found(msg):
    return Response('<p>Login failed</p>')

@app.route('/hours', methods=['GET'])
@login_required
def hours_list():
    return Response('<p>Change me</p>')

@app.route('/view/day/', methods=['GET'])
@login_required
def view_today():
    return view_day(str(datetime.date.today())) #todo: return today date

@app.route('/view/day/<date>', methods=['GET'])
@login_required
def view_day(date):
    bsession = request.environ['beaker.session']
    projects = bsession['projects']
    ct = bsession['ct']

    date = time.strptime(date, "%Y-%m-%d")
    today = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    next_day = today + datetime.timedelta(1)

    activities = ct.get_activities(today, next_day)

    return render_template('view_day.html', projects=projects)

@app.route('/view/week', methods=['GET'])
@login_required
def view_current_week():
    projects = testAct.projects

    return render_template('view_week.html', projects=projects, random=random.randint(1,1000))

@app.route('/view/week/<week>', methods=['GET'])
@login_required
def view_week(week):
    bsession = request.environ['beaker.session']
    projects = bsession['projects']
    ct = bsession['ct']

    week = week + "-1"
    date = time.strptime(week, "%Y-%W-%w")
    monday = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    sunday = monday + datetime.timedelta(7)

    activities = ct.get_activities(monday, sunday)
    days = defaultdict(lambda: [])
    for activity in activities:
        activity.project_name = projects[activity.project_id].name
        days[activity.day].append(activity)

    projects = sorted(days.iteritems(), key=operator.itemgetter(0))

    return render_template('view_week.html', projects=projects, random=random.randint(1,1000))


@app.route('/view/month', methods=['GET'])
@login_required
def view_current_month():
    now = datetime.datetime.now()
    date = "%s.%s"  % (now.year, now.month)
    return view_month(date)

@app.route('/view/month/<month>', methods=['GET'])
@login_required
def view_month(month):
    bsession = request.environ['beaker.session']
    ct = bsession['ct']
    tmp_projects = bsession['projects']
    projects = {}

    for project in tmp_projects:
        projects[project.id] = project


    year, month = month.split(".")
    year = int(year)
    month = int(month)
    date = datetime.date(year, month, 1)
    todate = date + datetime.timedelta(calendar.monthrange(year, month)[1]-1)
    prev_month = date - datetime.timedelta(1)
    prev_month = "%s.%02d" % (prev_month.year, int(prev_month.month))
    next_month = date + datetime.timedelta(40)
    next_month = "%s.%02d" % (next_month.year, int(next_month.month))


    calendar_month = generate_calendar_month(date)

    activities = ct.get_activities(date, todate)
    days = defaultdict(lambda: [])
    for activity in activities:
        activity.project_name = projects[activity.project_id].name
        days[activity.day].append(activity)

    work_month = {}
    for week in calendar_month:
        work_month[week] = []
        for day_month, day_week in calendar_month[week]:
            if day_month == 0:
                work_month[week].append({ "day": day_month, "weekday": day_week, "hours": 0, "link": "%s-%s-%s" % (year, month, day_month) })
            elif day_week == 6:
                continue
            else:
                hours = 0
                for activity in days[datetime.date(year, month, day_month)]:
                    hours += activity.duration

                if day_week == 5 and [day_month+1, day_week+1] in calendar_month[week]:
                    hours_sunday = 0
                    for activity in days[datetime.date(year, month, day_month+1)]:
                        hours_sunday += activity.duration

                    work_month[week].append({ "day": day_month, "day_sunday": day_month+1, "weekday": day_week, "hours": hours,
                        "hours_sunday": hours_sunday, "link": "%s-%s-%s" % (year, month, day_month), "link_sunday": "%s-%s-%s" % (year, month, day_month+1) })
                else:
                    work_month[week].append({ "day": day_month, "weekday": day_week, "hours": hours, "link": "%s-%s-%s" % (year, month, day_month) })

    work_month = sorted(work_month.iteritems(), key=operator.itemgetter(0))


    return render_template('view_month.html', calendar=work_month, next_month=next_month, prev_month=prev_month)

@app.route('/activity/<id>', methods=['GET', 'POST'])
@login_required
def edit_activity(id):
    projects = testAct.projects
    form = ActivityForm()

    #oldData = testAct.projects[id]
    if request.method == 'POST' and form.validate():
        #if oldData.notes != testAct.notes and oldData.hours != oldData.hours:
        #    error = "Edited after you - aborting"
        #else:
        return redirect(request.args.get("next") or url_for('view_week'))

    return render_template('activity.html', form=form, id=id)

@app.route('/test', methods=['GET', 'POST'])
@login_required
def hello_test():
    #return render_template('test.html') if valid_user() else redirect_to_login()
    return render_template('test.html')

@app.route('/user/<username>')
@login_required
def show_user(username):
    return render_template('user.html', username=username)

#@login_manager.user_loader
#def load_user(userid):
#    g.user = User(userid)
#    return g.user


if __name__ == '__main__':
    host = config.get("server", "host")
    port = config.get("server", "port")
    app.run(host=host, port=int(port))
