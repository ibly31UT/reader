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
import random
import datetime

db.drop_all()
db.create_all()
User.query.delete()

cardid = []
facid = []

for i in range(0, 6):
	cardid.append(str(int(random.random() * 9999)))
	facid.append(str(int(random.random() * 9999)))

admin = User("Administmaster", 99, cardid[0], facid[0], "password")
user = User("Employee 1", 1, cardid[1], facid[1], "password")
user2 = User("Employee 2", 1, cardid[2], facid[2], "password")
guest = User("Employee 2's Wife", 0, cardid[3], facid[3], "password")
security = User("Security Guard #145", 3, cardid[4], facid[4], "password")
priority = User("CEO Matthews", 4, cardid[5], facid[5], "password")
db.session.add(admin)
db.session.add(user)
db.session.add(user2)
db.session.add(guest)
db.session.add(security)
db.session.add(priority)
db.session.commit()

starttime = datetime.time(5, 0, 0)
endtime = datetime.time(23, 59, 0)

firstAccessGroup = [admin.get_id(), user.get_id(), user2.get_id(), guest.get_id(), security.get_id(), priority.get_id()]
secondAccessGroup = list(firstAccessGroup)
secondAccessGroup.remove(user.get_id())
secondAccessGroup.remove(user2.get_id())
secondAccessGroup.remove(guest.get_id())
thirdAccessGroup = list(secondAccessGroup)

frontdoorreader = Reader("Front Door", True, json.dumps(firstAccessGroup), starttime, endtime)
backdoorreader = Reader("Back Door", False, json.dumps(secondAccessGroup), starttime, endtime)
sidedoorreader = Reader("Side Door", True, json.dumps(secondAccessGroup), starttime, endtime)
db.session.add(frontdoorreader)
db.session.add(backdoorreader)
db.session.add(sidedoorreader)
db.session.commit()