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


from app import db
import json
import datetime
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from Crypto.Cipher import AES
import smbus
import subprocess

key = "passwordpasswordpasswordpassword"
iv = "1000000000000001"

bus = smbus.SMBus(1)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    access = db.Column(db.Integer, nullable=False)
    cardid = db.Column(db.String(64), nullable=False)
    passwordHash = db.Column(db.String(128), nullable=False)
    receptionCurrentReader = db.Column(db.String(64), nullable=True)
    
    def __init__(self, username, access, cardid, password):
        self.username = username
        self.access = access
        self.cardid = cardid
        self.receptionCurrentReader = None

        self.set_password(password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def set_password(self, password):
        self.passwordHash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passwordHash, password)

    def get_id(self):
    	try:
    		return unicode(self.id) #python 2
    	except NameError:
    		return str(self.id) #python 3

class Reader(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    users = db.Column(db.String(128), nullable=False)
    starttime = db.Column(db.Time, nullable=False)
    endtime = db.Column(db.Time, nullable=False)
    log = db.Column(db.String(256), nullable=False)
    i2caddress = db.Column(db.Integer, nullable=False)
    messagequeue = db.Column(db.String(256), nullable=False)
    lastmessages = db.Column(db.String(512), nullable=False)
    
    def __init__(self, name, address, users, starttime, endtime):
        self.name = name
        self.status = 1
        self.users = users
        self.starttime = starttime
        self.endtime = endtime
        self.log = json.dumps([{"user": 1, "time": str(datetime.datetime.now())}])
        self.i2caddress = address
        self.messagequeue = json.dumps([])
        self.lastmessages = json.dumps([])

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def checkForMessages(self):
        messageQueueString = self.messagequeue
        messageQueueArray = json.loads(messageQueueString)

        if len(messageQueueArray) > 0:
            message = messageQueueArray.pop(0)
            if self.sendMessage(message["messageType"], message["argument"]) == "Retry":
                return "Retry"  # return before message queue gets overwritten
            self.messagequeue = json.dumps(messageQueueArray)
            db.session.commit()
        else:
            # If there is no message to send, everything is ok
            if self.sendMessage("LastMessageReceivedCorrectly", "none") == "Retry":
                return "Retry"
        return "Success"

    def queueMessage(self, messageType, argument):
        messageQueueString = self.messagequeue
        messageQueueArray = json.loads(messageQueueString)

        message = {"messageType": messageType, "argument": argument}
        messageQueueArray.append(message)

        self.messagequeue = json.dumps(messageQueueArray)
        db.session.commit()

    def sendMessage(self, messageType, argument):
        messageCodes = {
            "ResetTamperStatus": "TR",
            "LastMessageReceivedCorrectly": "LM",
            "SetReaderStatus": "RS",
            "CorruptedMessagePleaseResend": "CM",
            "UserLogSuccess": "US",
            "UserLogFailure": "UF",
            "SetSlaveAddress": "SA"
        }

        msg = messageCodes.get(messageType, "error")
        if msg == "error":
            print "Error, invalid message type provided."
            return "Invalid"
        else:
            if len(argument) > 0:
                for char in argument:
                    msg = msg + char
            
            iv_chars = [random.choice(string.hexdigits) for n in xrange(15)]
            new_iv = "".join(iv_chars)
            new_iv += "X"   

            differenceBetweenCurrentAnd16 = 16 - len(msg)
            msg += "".zfill(differenceBetweenCurrentAnd16)

            print "Message short: " + msg
            
            aes = AES.new(key, AES.MODE_CBC, new_iv)
            msg = aes.encrypt(msg)

            #print "Message encrypted: "
            msg += new_iv
            #print ":".join(x.encode('hex') for x in msg)
            
            msg_byte_list = []
            for char in msg:
                msg_byte_list.append(ord(char))
            
            try:
                bus.write_i2c_block_data(self.i2caddress, 0x00, msg_byte_list)
            except IOError:
                subprocess.call(['i2cdetect', '-y', '1'])
                return "Retry"

            return "Success"


    def receiveMessage(self):
        try:
            msg_chars = bus.read_i2c_block_data(self.i2caddress, 0x00)
        except IOError:
            subprocess.call(['i2cdetect', '-y', '1'])
            return "Retry"

        msg = ""
        for charcode in msg_chars:
            if charcode != 255:
                msg += chr(charcode)
            else:
                break
        
        if len(msg) != 32:
            print "Message length is not 32, length is ", len(msg)
            return "Msg length not 32"

        if msg == "10000000000000000000000000000001":
            print "Default message"
            return "Default"

        iv = msg[16:]
        msg = msg[:16]

        aes = AES.new(key, AES.MODE_CBC, iv)
        msg = aes.decrypt(msg)

        if msg[:2] == "OK":
            print "Message OK"
        elif msg[:2] == "SC":
            # Card was scanned, append to reader log
            readerLogArray = json.loads(self.log)
            uniqueIDchars = msg[2:6]
            uniqueIDbytes = []
            for char in uniqueIDchars:
                uniqueIDbytes.append(ord(char))
            uniqueID = uniqueIDbytes[3]
            uniqueID += uniqueIDbytes[2] * 256
            uniqueID += uniqueIDbytes[1] * 256 * 256
            uniqueID += uniqueIDbytes[0] * 256 * 256 * 256

            print "Scanned card ID: ", uniqueID

            user = db.session.query(User).filter_by(cardid=str(uniqueID)).first()
            if user is None:
                print "Could not check in user, please ensure that user exists."
                self.queueMessage("UserLogFailure", str(uniqueID))
            else:
                userArray = json.loads(self.users)
                if str(user.id) in userArray:
                    readerLogArray.append({"user": user.id, "time": str(datetime.datetime.now())})
                    self.log = json.dumps(readerLogArray)
                    db.session.commit()
                    self.queueMessage("UserLogSuccess", user.username[:14])  # send first 14 characters of username
                else:
                    self.queueMessage("UserLogFailure", user.username[:14])  # send first 14 characters of username

        elif msg[:2] == "DT":
            print "Tamper detected"
            self.status = 2
            db.session.commit()
            # Potentially send admin an email?
        elif msg[:2] == "CM":
            print "Please resend"
        elif msg[:2] == "RF":
            print "Attempted tamper reset failed"
        elif msg[:2] == "SA":
            addressByte = msg[2]
            self.i2caddress = ord(addressByte)
            db.session.commit()
            print "Setting i2caddress to ", self.i2caddress
        else:
            print "Unrecognized message"
            self.queueMessage("CorruptedMessagePleaseResend", "")
            return "Unrecognized message"

        lastMessagesArray.insert(0, msg)

        if len(lastMessagesArray) >= 15:
            lastMessagesArray.pop()



        self.lastmessages = json.dumps(lastMessagesArray)
        db.session.commit()

        return msg

    def get_id(self):
        try:
            return unicode(self.id) #python 2
        except NameError:
            return str(self.id) #python 3

class GlobalSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accessLevels = db.Column(db.String(128), nullable=False)
    multipleAdmins = db.Column(db.Boolean, nullable=False)

    @property
    def is_anonymous(self):
        return False
    def __init__(self, accessLevels, multipleAdmins):
        self.accessLevels = accessLevels
        self.multipleAdmins = multipleAdmins

    def getSetting(self, key):
        if key == "accessLevels":
            return json.loads(self.accessLevels)
        elif key == "multipleAdmins":
            return self.multipleAdmins
        return None