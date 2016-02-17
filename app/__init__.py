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

from .models import User, Reader
import json
import datetime

db.drop_all()
db.create_all()
User.query.delete()

admin = User("admin", 2, "password")
regularuser = User("user", 1, "wordpass")
dumbuser = User("dumbuser", 0, "wordpass2")
dumberuser = User("dumberuser", 0, "wordpass3")
evendumberuser = User("evendumberuser", 0, "password")
db.session.add(admin)
db.session.add(regularuser)
db.session.add(dumbuser)
db.session.add(dumberuser)
db.session.add(evendumberuser)
db.session.commit()

starttime = datetime.time(5, 0, 0)
endtime = datetime.time(23, 59, 0)

frontdoorreader = Reader("Front Door", True, json.dumps([admin.get_id(), regularuser.get_id()]), starttime, endtime)
backdoorreader = Reader("Back Door", False, json.dumps([admin.get_id(), regularuser.get_id(), dumbuser.get_id()]), starttime, endtime)
sidedoorreader = Reader("Side Door", True, json.dumps([admin.get_id(), regularuser.get_id(), dumbuser.get_id(), dumberuser.get_id(), evendumberuser.get_id()]), starttime, endtime)
db.session.add(frontdoorreader)
db.session.add(backdoorreader)
db.session.add(sidedoorreader)
db.session.commit()