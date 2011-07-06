from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
import ConfigParser
app = Flask(__name__)

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
    def __init__(self, name = None):
        self.name = name

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

@app.route('/')
def hello_world():
    return "Hello World no!"

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    return render_template('test.html')

@app.route('/hours', methods=['GET'])
def hours_list():
    pass


@app.route('/test')
def hello_test():
    return render_template('test.html')

@app.route('/user/<username>')
def show_user(username):
    return "Hello, %s!" % username

if __name__ == '__main__':
    host = config.get("server", "host")
    port = config.get("server", "port")
    app.run(debug=True, host=host, port=int(port))
