#!/usr/bin/env python

import ConfigParser, random
from flask import Flask, request, Response, session, g, redirect, url_for, \
     abort, render_template, flash, get_flashed_messages, current_app, \
     jsonify
from flaskext.wtf import Form, DateField, TextField, Required, validators, PasswordField, TextAreaField, DecimalField, HiddenField, SubmitInput


config = ConfigParser.ConfigParser()
config.read(["config.ini.sample", "config.ini"])

from ct.apis import RangeAPI

app = Flask(__name__)
app.config['DEBUG'] = config.getboolean("server", "debug")
app.config['SECRET_KEY'] = config.get("server", "secret_key")

@app.route('/')
def index():
    return render_template('jsclient-bootstrap.html')

if __name__ == '__main__':
    host = config.get("server", "host")
    port = config.get("server", "port")
    app.run(host=host, port=int(port))
