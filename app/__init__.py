import os

from flask import Flask

from flask_sqlalchemy import SQLAlchemy

from flask_login import LoginManager

from flask_openid import OpenID

from flask_mail import Mail
from config import basedir, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, ADMINS

app = Flask(__name__, static_folder = 'static', template_folder = 'templates')

app.config.from_object('config')

db = SQLAlchemy(app)

lm = LoginManager()

lm.init_app(app)

lm.login_view = 'login'

oid = OpenID(app, os.path.join(basedir, 'tmp'))

mail = Mail(app)

from app import views, models