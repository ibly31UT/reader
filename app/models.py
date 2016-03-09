from app import db
import json
import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    access = db.Column(db.Integer, nullable=False)
    cardid = db.Column(db.String(64), nullable=False)
    facid = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    receptionCurrentReader = db.Column(db.String(64), nullable=True)
    
    def __init__(self, username, access, cardid, facid, password):
        self.username = username
        self.access = access
        self.cardid = cardid
        self.facid = facid
        self.password = password
        self.receptionCurrentReader = None

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
    	try:
    		return unicode(self.id) #python 2
    	except NameError:
    		return str(self.id) #python 3

class Reader(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    users = db.Column(db.String(256), nullable=False)
    starttime = db.Column(db.Time, nullable=False)
    endtime = db.Column(db.Time, nullable=False)
    log = db.Column(db.String(256), nullable=False)
    
    def __init__(self, name, status, users, starttime, endtime):
        self.name = name
        self.status = status
        self.users = users
        self.starttime = starttime
        self.endtime = endtime
        self.log = json.dumps([{"user": 1, "time": str(datetime.datetime.now())}])

    def get_id(self):
        try:
            return unicode(self.id) #python 2
        except NameError:
            return str(self.id) #python 3

class GlobalSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accessLevels = db.Column(db.String(128), nullable=False)
    multipleAdmins = db.Column(db.Boolean, nullable=False)

    def __init__(self, accessLevels, multipleAdmins):
        self.accessLevels = accessLevels
        self.multipleAdmins = multipleAdmins

    def getSetting(self, key):
        if key == "accessLevels":
            return json.loads(self.accessLevels)
        elif key == "multipleAdmins":
            return self.multipleAdmins
        return None

    def get_id(self):
        try:
            return unicode(self.id) #python 2
        except NameError:
            return str(self.id) #python 3