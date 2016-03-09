

from app import models
from app import views
<<<<<<< HEAD
from .models import User, Reader, GlobalSettings
=======

from .models import User, Reader
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

cardid = []
facid = []

for i in range(0, 7):
	cardid.append(str(int(random.random() * 9999)))
	facid.append(str(int(random.random() * 9999)))

admin = User("admin", 99, cardid[0], facid[0], "password")
user = User("Employee 1", 1, cardid[1], facid[1], "password")
user2 = User("Employee 2", 1, cardid[2], facid[2], "password")
guest = User("Employee 2's Wife", 0, cardid[3], facid[3], "password")
security = User("Security Guard #145", 2, cardid[4], facid[4], "password")
priority = User("CEO Matthews", 3, cardid[5], facid[5], "password")
frontdesk = User("Front Desk Employee", 4, cardid[6], facid[6], "password")

admin.cardid="1111"
admin.facid="1111"

db.session.add(admin)
db.session.add(user)
db.session.add(user2)
db.session.add(guest)
db.session.add(security)
db.session.add(priority)
db.session.add(frontdesk)
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
>>>>>>> parent of 8030dd7... User Authorization Dialog Additions
