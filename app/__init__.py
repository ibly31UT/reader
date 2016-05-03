# Copyright (c) 2016 William Connolly, Tyler Rocha, Justin Baiko

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE 
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from flask import Flask

app = Flask(__name__)
app.config.from_object("config")

from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = "index"

from celery import Celery

celery = Celery("tasks", broker='redis://localhost:6379')

from app import models
from app import views
from app import tasks

from .models import User, Reader, GlobalSettings
import json
import random
import datetime
import time
from admin import start_admin

start_admin(app, db)

db.drop_all()
db.create_all()
User.query.delete()
Reader.query.delete()

admin = User("admin", 99, "1111", "password")
user = User("Employee 1", 1, "2597032008", "password")
user2 = User("Employee 2", 1, "1451094320", "password")
guest = User("Employee 2's Wife", 0, "937948274", "password")
security = User("Security Guard #145", 2, "884060773", "password")
priority = User("CEO Matthews", 3, "3059873328", "password")
frontdesk = User("Front Desk Employee", 4, "612929485", "password")

db.session.add(admin)
db.session.add(user)
db.session.add(user2)
db.session.add(guest)
db.session.add(security)
db.session.add(priority)
db.session.add(frontdesk)

for i in range(0, 10):
	username = "User #" + str(int((random.random() * 999))).zfill(4)
	cardid = str(int(random.random() * 999999)).zfill(6)
	newUser = User(username, i % 5, cardid, "password")
	db.session.add(newUser)

db.session.commit()

starttime = datetime.time(5, 0, 0)
endtime = datetime.time(23, 59, 0)

firstAccessGroup = [admin.get_id(), user.get_id(), user2.get_id(), guest.get_id(), priority.get_id()]
secondAccessGroup = list(firstAccessGroup)
secondAccessGroup.remove(user.get_id())
secondAccessGroup.remove(user2.get_id())
secondAccessGroup.remove(guest.get_id())
thirdAccessGroup = list(secondAccessGroup)

frontdoorreader = Reader("Front Door", 7, json.dumps(firstAccessGroup), starttime, endtime)
backdoorreader = Reader("Back Door", 8, json.dumps(secondAccessGroup), starttime, endtime)

db.session.add(frontdoorreader)
db.session.add(backdoorreader)
db.session.commit()

accessLevels = '["Guest", "User", "Security", "Priority User", "Reception", "Employee", "Manager", "First", "Second"]'

globalSettings = GlobalSettings(accessLevels=accessLevels, multipleAdmins=True)
db.session.add(globalSettings)
db.session.commit()