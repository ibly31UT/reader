from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    access = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    
    def __init__(self, username, access, password):
        self.username = username
        self.access = access
        self.password = password

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
    active = db.Column(db.Boolean, nullable=False)
    users = db.Column(db.String(128), nullable=False)
    starttime = db.Column(db.Time, nullable=False)
    endtime = db.Column(db.Time, nullable=False)
    
    def __init__(self, name, active, users, starttime, endtime):
        self.name = name
        self.active = active
        self.users = users
        self.starttime = starttime
        self.endtime = endtime

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