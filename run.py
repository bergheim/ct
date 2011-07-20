#!/usr/bin/env python

import calendar
import datetime
from collections import defaultdict

from flask import Flask, request, Response, session, g, redirect, url_for, \
     abort, render_template, flash, get_flashed_messages, current_app
from flaskext.wtf import Form, DateField, TextField, Required, validators, PasswordField, TextAreaField, DecimalField
import ConfigParser, random
from flaskext.login import LoginManager, UserMixin, \
    login_required, login_user, logout_user
from ct.apis import RangeAPI

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


app = Flask(__name__)
config = ConfigParser.ConfigParser()
config.read(["config.ini.sample", "config.ini"])
app.config['DEBUG'] = config.get("server", "debug")
app.config['SECRET_KEY'] = config.get("server", "secret_key")
app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)

login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = "login"

class UserLogin(UserMixin):
    def __init__(self, id):
        self.id = id
        self.username = 'user' + str(id)
        self.password = self.username

    def __repr__(self):
        return "%d: %s/%s" % (self.id, self.username, self.password)

class UserForm(Form):
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


class Hours(object):
    def __init__(self, id = None, name = None):
        self.id = id
        self.name = name

class Activity(object):
    projects = []
    projects.append( {'name': 'Lunch', 'activity': [] } )
    projects.append( {'name': 'Internprosjekt', 'activity': [] } )

    projects[0]['activity'] = [
            { 'hours': 4, 'note': 'ingen' },
            { 'hours': 2, 'note': '' },
            { 'hours': 8, 'note': '' },
            { 'hours': 7, 'note': 'gjorde ditt, and then datt' },
            { 'hours': 2, 'note': 'dro tidlig' },
            { 'hours': 3, 'note': 'helgejobbing' }
            ]

    projects[1]['activity'] = [
            { 'hours': 1, 'note': '' },
            { 'hours': 2, 'note': '' },
            { 'hours': 3, 'note': '' },
            { 'hours': 4, 'note': '' },
            { 'hours': 5, 'note': 'lol' },
            { 'hours': 6, 'note': '' }
            ]

    #def __init__(self):
    #    for p in self.projects:
    #        activity = []
    #        for day in xrange(1,7):
    #            a = { 'hours': random.randint(0,7), 'note': "" }
    #            if a['hours'] is not 0 and random.random() > 0.7:
    #                a['note'] = 'random note'

    #            activity.append(a)

    #        p['activity'] = activity

testAct = Activity()

def valid_login(username, password):
    if not User.query.filter_by(username=username,password=password).first():
        return False

    return True

def valid_user():
    if 'username' in session:
        return True
    return False

def redirect_if_invalid_user():
    if not valid_user():
        flash(request.url, 'redirect')
        return redirect_to_login()
    return True

def redirect_to_login():
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

def do_ct_login(form):
    server = config.get("server", "ct_url")
    ct = RangeAPI(server)
    logged_in = ct.login(form.username.data, form.password.data)
    if logged_in:
        session['user'] = form.username.data
        session['ct'] = ct

    return logged_in

@app.route('/login', methods=['GET','POST'])
def login():
    form = UserForm()
    error = ""
    if request.method == 'POST' and form.validate():
        logged_in = do_ct_login(form)
        g.user = UserLogin(form.username.data)
        login_user(g.user)
        if logged_in:
            return redirect(request.args.get("next") or url_for('show_user', username=g.user.username))

    return render_template('login.html', form=form, error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
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
    return view_day(datetime.date.today()) #todo: return today date

@app.route('/view/day/<int:date>', methods=['GET'])
@login_required
def view_day(date):
    return render_template('view_day.html', projects=testAct.projects)

@app.route('/view/week', methods=['GET'])
@login_required
def view_week():
    projects = testAct.projects

    return render_template('view_week.html', projects=projects, random=random.randint(1,1000))

@app.route('/view/month', methods=['GET'])
@login_required
def view_month():
    ct = session['ct']
    form = RangeForm(formdata=request.args)

    now = datetime.datetime.now()

    c = calendar.LocaleHTMLCalendar(calendar.MONDAY)
    calendar_month = c.formatmonth(now.year, now.month)
    calendar_month = c.monthdays2calendar(now.year, now.month)

    calendar_header = c.formatweekheader()

    app.logger.debug(form.to_date.data)

    activities = ct.get_activities(form.from_date.data, form.to_date.data)


    days = defaultdict(lambda: [])
    for activity in activities:
        days[activity.day].append(activity)

    return render_template('view_month.html', calendar=calendar_month, calendar_header=calendar_header)

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

@login_manager.user_loader
def load_user(userid):
    g.user = UserLogin(userid)
    return g.user


if __name__ == '__main__':
    host = config.get("server", "host")
    port = config.get("server", "port")
    app.run(host=host, port=int(port))
