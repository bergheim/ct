#!/usr/bin/env python

from flask import Flask, request, Response, session, g, redirect, url_for, \
     abort, render_template, flash, get_flashed_messages
from flaskext.wtf import Form, TextField, Required, validators, PasswordField
import ConfigParser, random
from flaskext.login import LoginManager, UserMixin, \
    login_required, login_user, logout_user

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

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.username = 'user' + str(id)
        self.password = self.username

    def __repr__(self):
        return "%d: %s/%s" % (self.id, self.username, self.password)

class UserForm(Form):
    username = TextField(u'Brukernavn', [validators.Length(min=3, max=25)], [], u'Ditt brukernavn')
    password = PasswordField(u'Passord', [], [], u'Minimum 4 tegn')

class Hours(object):
    def __init__(self, id = None, name = None):
        self.id = id
        self.name = name

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

@app.route('/login', methods=['GET','POST'])
def login():
    form = UserForm()
    if request.method == 'POST' and form.validate():
        g.user = User(form.username.data)
        login_user(g.user)
        #return redirect(
        return redirect(request.args.get("next") or url_for('show_user', username=g.user.username))

    return render_template('login.html', form=form)

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

@app.route('/test')
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
    g.user = User(userid)
    return g.user

if __name__ == '__main__':
    host = config.get("server", "host")
    port = config.get("server", "port")
    app.run(host=host, port=int(port))
