from flask import Flask
app = Flask(__name__)
app.config.from_object("config")

from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form

db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = "index"

from app import models
from app import views

from .models import User

db.create_all()
User.query.delete()

#admin = User("admin")
admin = User("admin", 2, "password")
regularuser = User("user", 1, "wordpass")
db.session.add(admin)
db.session.add(regularuser)
db.session.commit()