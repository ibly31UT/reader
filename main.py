#!flask/bin/python
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

db.drop_all()
db.create_all()
User.query.delete()
Reader.query.delete()
GlobalSettings.query.delete()

cardid = []
facid = []

for i in range(0, 7):
	cardid.append(str(int(random.random() * 9999)))
	facid.append(str(int(random.random() * 9999)))

admin = User("admin", 99, "1111", "1111", "password")
user = User("Employee 1", 1, "4525", "4130", "password")
user2 = User("Employee 2", 1, "9062", "0982", "password")
guest = User("Employee 2's Wife", 0, "9842", "9379", "password")
security = User("Security Guard #145", 2, "6190", "4906", "password")
priority = User("CEO Matthews", 3, "4005", "4147", "password")
frontdesk = User("Front Desk Employee", 4, "6882", "6129", "password")

db.session.add(admin)
db.session.add(user)
db.session.add(user2)
db.session.add(guest)
db.session.add(security)
db.session.add(priority)
db.session.add(frontdesk)

for i in range(0, 100):
	username = "User #" + str(int((random.random() * 999))).zfill(4)
	facid = str(int(random.random() * 9999)).zfill(4)
	cardid = str(int(random.random() * 9999)).zfill(4)
	newUser = User(username, i % 5, cardid, facid, "password")
	db.session.add(newUser)

db.session.commit()

starttime = datetime.time(5, 0, 0)
endtime = datetime.time(23, 59, 0)

firstAccessGroup = [admin.get_id(), user.get_id(), user2.get_id(), guest.get_id(), security.get_id(), priority.get_id()]
secondAccessGroup = list(firstAccessGroup)
secondAccessGroup.remove(user.get_id())
secondAccessGroup.remove(user2.get_id())
secondAccessGroup.remove(guest.get_id())
thirdAccessGroup = list(secondAccessGroup)

frontdoorreader = Reader("Front Door", 1, json.dumps(firstAccessGroup), starttime, endtime)
backdoorreader = Reader("Back Door", 0, json.dumps(secondAccessGroup), starttime, endtime)
sidedoorreader = Reader("Side Door", 2, json.dumps(secondAccessGroup), starttime, endtime)
northwestdoorreader = Reader("North West Door", 2, json.dumps(firstAccessGroup), starttime, endtime)
southwestdoorreader = Reader("South West Door", 1, json.dumps(secondAccessGroup), starttime, endtime)
southdoorreader = Reader("South Door", 0, json.dumps(secondAccessGroup), starttime, endtime)

db.session.add(frontdoorreader)
db.session.add(backdoorreader)
db.session.add(sidedoorreader)
db.session.add(northwestdoorreader)
db.session.add(southwestdoorreader)
db.session.add(southdoorreader)
db.session.commit()

accessLevels = ["Guest", "User", "Security", "Priority User", "Reception", "Employee", "Manager", "Warehouse"]

defaultSettings = GlobalSettings(json.dumps(accessLevels), True)
db.session.add(defaultSettings)
db.session.commit()

print defaultSettings.getSetting("accessLevels")

from app import app
from app import models
from app import views
from app import admin
from .models import User, Reader, GlobalSettings
from .admin import start_admin
import json
import random
import datetime
import time

start_admin(app, db)


if __name__ == "__main__":
	app.run(debug=True)