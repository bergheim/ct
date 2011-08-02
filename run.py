#!/usr/bin/env python

import calendar
import datetime
import time
import operator
import pprint
from collections import defaultdict
from functools import wraps
from decimal import Decimal

from flask import Flask, request, Response, session, g, redirect, url_for, \
     abort, render_template, flash, get_flashed_messages, current_app
from flaskext.wtf import Form, DateField, TextField, Required, validators, PasswordField, TextAreaField, DecimalField, HiddenField
import ConfigParser, random
#from flaskext.login import LoginManager, UserMixin, \
#    login_required, login_user, logout_user
from beaker.middleware import SessionMiddleware

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
        return redirect(get_redirect_target() or url_for(endpoint, **values))

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

if config.getboolean("server", "ct_cache"):
    from ctcache import RangeAPICache
else:
    from ct.apis import RangeAPI

session_opts = {
#    'session.type': 'ext:memcached',
#    'session.url': '127.0.0.1:11211',
    'session.data_dir': './cache',
}

app = Flask(__name__)
app.config['DEBUG'] = config.getboolean("server", "debug")
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

        iso_week = datetime.date(year, month, weekday).isocalendar()
        weeknumbers.append((iso_week[0], iso_week[1]))


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
        g.cache = config.getboolean("server", "ct_cache") #fixme: this should be placed elsewhere
        if not valid_user() or not bsession.has_key('ct') or not bsession['ct'].valid_session():
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

class UserForm(RedirectForm):
    username = TextField(u'Brukernavn', [validators.Length(min=3, max=25)], [], u'Ditt brukernavn')
    password = PasswordField(u'Passord', [], [], u'Minimum 4 tegn')

class ActivityForm(Form):
    duration = DecimalField()
    comment = TextAreaField()

    next = HiddenField()
    edit_timestamp = HiddenField()

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
    cache = config.getboolean("server", "ct_cache")
    bsession = request.environ['beaker.session']
    if cache:
        ct = RangeAPICache(server, config.get("server", "ct_cache_file"))
    else:
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
        if not "bouvet\\" in username:
            username = "bouvet\\" + username
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
    bsession = request.environ['beaker.session']
    bsession.delete()
    return redirect(url_for('index', _external=True), 301)

@app.errorhandler(401)
def page_not_found(msg):
    return Response('<p>Login failed</p>')

@app.route('/hours', methods=['GET'])
@login_required
def hours_list():
    return Response('<p>Change me</p>')

@app.route('/view/day', methods=['GET'])
@login_required
def view_current_day():
    return view_day(str(datetime.date.today())) #todo: return today date

@app.route('/view/day/<day>', methods=['GET'])
@login_required
def view_day(day):
    bsession = request.environ['beaker.session']
    ct = bsession['ct']
    tmp_projects = bsession['projects']
    projects = {}

    for project in tmp_projects:
        projects[project.id] = project

    date = time.strptime(day, "%Y-%m-%d")
    today = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    prev_day = today - datetime.timedelta(1)
    next_day = today + datetime.timedelta(1)

    activities = ct.get_activities(today, today)

    todays_activities = []

    for activity in activities:
        print "Act: ", activity
        activity.project_name = projects[activity.project_id].name.split("-")[-1].strip()
        activity.edit_link = url_for('edit_activity', date=day, id=activity.project_id)
        todays_activities.append(activity)

    if day == "%d-%d-%d" % (date.tm_year, date.tm_mon, date.tm_mday):
        current_day = False
    else:
        current_day = url_for('view_current_day')
    prev_day = url_for('view_day', day=prev_day)
    next_day = url_for('view_day', day=next_day)

    projects_url = url_for('projects', date=today)

    return render_template('view_day.html', projects=todays_activities, prev=prev_day, next=next_day, current=current_day, projects_url=projects_url, date=day)

@app.route('/view/week', methods=['GET'])
@login_required
def view_current_week():
    now = datetime.datetime.now()
    date = "%s-%s"  % (now.year, now.isocalendar()[1])
    return view_week(date)


@app.route('/view/week/<week>', methods=['GET'])
@login_required
def view_week(week):
    bsession = request.environ['beaker.session']
    ct = bsession['ct']
    tmp_projects = bsession['projects']
    projects = {}

    for project in tmp_projects:
        projects[project.id] = project

    week = week + "-1"
    date = time.strptime(week, "%Y-%W-%w")
    monday = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
    sunday = monday + datetime.timedelta(6)

    prev_week = monday - datetime.timedelta(7)
    prev_week = "%s-%02d" % (prev_week.year, int(prev_week.isocalendar()[1]))
    next_week = monday + datetime.timedelta(7)
    next_week = "%s-%02d" % (next_week.year, int(next_week.isocalendar()[1]))

    day_links = []
    for day in xrange(7):
        day_link = monday + datetime.timedelta(day)
        day_links.append(url_for('view_day', day="%s-%s-%s" % (day_link.year, day_link.month, day_link.day)))

    activities = ct.get_activities(monday, sunday)
    days = defaultdict(lambda: [])
    for activity in activities:
        activity.project_name = projects[activity.project_id].name.split("-")[-1].strip()
        day = activity.day.weekday()
        days[day].append(activity)

    projects = sorted(days.iteritems(), key=operator.itemgetter(0))

    projects_project_indexed = {}
    for day, activities in projects:
        for activity in activities:
            link = url_for('edit_activity', date=day, id=activity.project_id)
            key = activity.project_name
            if not projects_project_indexed.has_key(key):
                projects_project_indexed[key] = {}

            if day != 6:
                projects_project_indexed[key][day] = {"link": link, "duration": activity.duration, "comment": activity.comment}
            else:
                projects_project_indexed[key][day-1]["duration_sunday"] = activity.duration
                projects_project_indexed[key][day-1]["link_sunday"] = link
                projects_project_indexed[key][day-1]["comment_sunday"] = activity.comment


    for name, project in projects_project_indexed.iteritems():
        for day in range(6):
            #if day not in [d for d in project]:
            if day not in project.keys():
                project[day] = None
        #project = sorted(project.iteritems(), key=operator.itemgetter(0))

    prev_week = url_for('view_week', week=prev_week)
    next_week = url_for('view_week', week=next_week)

    this_week = datetime.datetime.now().isocalendar()
    if week == "%d-%d-%d" % (this_week[0], this_week[1], 1):
        current_week = False
    else:
        current_week = url_for('view_current_week')

    return render_template('view_week.html', projects=projects_project_indexed, next=next_week, prev=prev_week, current=current_week, day_links=day_links, date=monday)


@app.route('/view/month', methods=['GET'])
@login_required
def view_current_month():
    now = datetime.datetime.now()
    date = "%s-%s"  % (now.year, now.month)
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


    year, month = month.split("-")
    year = int(year)
    month = int(month)
    date = datetime.date(year, month, 1)
    todate = date + datetime.timedelta(calendar.monthrange(year, month)[1]-1)


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
            if day_week == 6:
                continue
            elif day_month == 0:
                work_month[week].append({ "day": day_month, "weekday": day_week, "hours": 0, "link": "%s-%s-%s" % (year, month, day_month) })
            else:
                hours = 0
                for activity in days[datetime.date(year, month, day_month)]:
                    hours += activity.duration

                if day_week == 5:
                    hours_sunday = 0
                    for activity in days[datetime.date(year, month, day_month+1)]:
                        hours_sunday += activity.duration

                    work_month[week].append({ "day": day_month, "day_sunday": day_month+1, "weekday": day_week, "hours": hours,
                        "hours_sunday": hours_sunday, "link": "%s-%s-%s" % (year, month, day_month), "link_sunday": "%s-%s-%s" % (year, month, day_month+1) })
                else:
                    work_month[week].append({ "day": day_month, "weekday": day_week, "hours": hours, "link": "%s-%s-%s" % (year, month, day_month) })

    work_month = sorted(work_month.iteritems(), key=operator.itemgetter(0))

    prev_month = date - datetime.timedelta(1)
    prev_month = "%s-%02d" % (prev_month.year, int(prev_month.month))
    next_month = date + datetime.timedelta(40)
    next_month = "%s-%02d" % (next_month.year, int(next_month.month))

    prev_month = url_for('view_month', month=prev_month)
    next_month = url_for('view_month', month=next_month)

    this_month = datetime.datetime.now()
    if (year, month) == (this_month.year, this_month.month):
        current_month = False
    else:
        current_month = url_for('view_current_month')

    return render_template('view_month.html', calendar=work_month, next=next_month, prev=prev_month, current=current_month, date=date)

@app.route('/activity/<date>/<id>', methods=['GET', 'POST'])
@login_required
def edit_activity(date, id):
    bsession = request.environ['beaker.session']
    ct = bsession['ct']
    projects = bsession['projects']

    year, month, day = [int(d) for d in date.split("-")]
    date = datetime.date(year, month, day)

    activities = ct.get_activities(date, date)

    #if not id in [activity.project_id for activity in activities]:
    activity = None
    for a in activities:
        if id in a.project_id:
            activity = a
            break

    edit_timestamp = str(datetime.datetime.now())
    form = ActivityForm(duration=activity.duration, comment=activity.comment, next=url_for('view_day', day=date), edit_timestamp=edit_timestamp)

    if request.method == "GET":
        bsession["edit_timestamp"] = edit_timestamp
        bsession["edit_activity"] = activity
        bsession.save()

    #auto-complete lunch
    if activity.project_id == '1,1,3,0':
        activity._dict["duration"] = 0 if activity.duration else Decimal('0.5')
        activity._dict["comment"] = ''
        ct.report_activity(activity, bsession["edit_activity"])
        return redirect(form.next.data or url_for('view_current_week'))


    if form.validate_on_submit():
        #if oldData.notes != testAct.notes and oldData.hours != oldData.hours:
        #    error = "Edited after you - aborting"
        #else:
        print bsession
        if form.edit_timestamp.data != bsession["edit_timestamp"]:
            return Response("Form edit conflict (%s != %s)" % (form.edit_timestamp.data, bsession["edit_timestamp"])) #todo: add better handling

        activity._dict["duration"] = form.duration.data
        activity._dict["comment"] = form.comment.data
        #if config.getboolean("server", "ct_cache"):
        #    ct.report_activity(activity, bsession["edit_activity"], bsession)
        #else:
        ct.report_activity(activity, bsession["edit_activity"])
        return redirect(form.next.data or url_for('view_current_week'))

    post_url = url_for('edit_activity', date=date, id=id)

    return render_template('activity.html', form=form, id=id, post_url=post_url)

@app.route('/projects/<date>', methods=['GET', 'POST'])
@login_required
def projects(date):
    bsession = request.environ['beaker.session']
    ct = bsession['ct']
    projects = bsession['projects']

    #remove already added projects
    year, month, day = [int(d) for d in date.split("-")]
    date = datetime.date(year, month, day)
    activities = ct.get_activities(date, date)
    current_unique_projects = projects[:]

    for activity in activities:
        for project in current_unique_projects:
            if activity.project_id == project.id:
                current_unique_projects.remove(project)

    return render_template('projects.html', projects=current_unique_projects)

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
