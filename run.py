#!/usr/bin/env python

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, get_flashed_messages
from flaskext.wtf import Form, TextField, Required, validators, PasswordField
import ConfigParser

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
class User(object):
    def __init__(self, username = None):
        self.username = username
        session['username'] = username

    #def __del__(self):
    #    session.pop(username, None)

class UserForm(Form):
    username = TextField(u'Brukernavn', [validators.Length(min=3, max=25)], [], u'Ditt brukernavn')
    password = PasswordField(u'Passord', [], [], u'Minimum 4 tegn')

class Hours(object):
    def __init__(self, id = None, name = None):
        self.id = id
        self.name = name


app = Flask(__name__)
config = ConfigParser.ConfigParser()
config.read(["config.ini.sample", "config.ini"])
app.config['DEBUG'] = config.get("server", "debug")
app.config['SECRET_KEY'] = config.get("server", "secret_key")
app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)

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
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    form = UserForm()
    flashed = get_flashed_messages('redirect')
    if 'redirect' in flashed:
        form.redirect = flashed['redirect']
    if request.method == 'POST' and form.validate():
        g.user = User(form.username.data)
        session['user'] = g.uesr
        flash('Login OK')
        return redirect(url_for('show_user', username=g.user.username))

    return render_template('login.html', form=form)

@app.before_request
def before_request():
    g.user = None
    if 'username' in session:
        g.user = session['user']

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/hours', methods=['GET'])
def hours_list():
    pass

@app.route('/test')
def hello_test():
    return render_template('test.html') if valid_user() else redirect_to_login()

@app.route('/user/<username>')
def show_user(username):
    if 'username' in session:
        return render_template('user.html', username=username)

    return redirect(url_for('login'))

if __name__ == '__main__':
    host = config.get("server", "host")
    port = config.get("server", "port")
    app.run(host=host, port=int(port))
