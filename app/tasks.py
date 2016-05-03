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


from .models import User, Reader, GlobalSettings
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from app import celery
from app import db

import random
import string
import time
import json
import datetime

@celery.task
def mainReaderTask():
	# Detect active readers
	for reader in db.session.query(Reader).all():
		message = reader.receiveMessage()
		if message == "Retry":
			time.sleep(0.5)
			print "Reader ", reader.id, " inactive."
			reader.status = 0
		else:
			reader.status = 1
			print "Reader ", reader.id, " active."

	db.session.commit()

	while True:
		maxSlaveAddress = -1
		for reader in db.session.query(Reader).all():
			if reader.i2caddress > maxSlaveAddress:
				maxSlaveAddress = reader.i2caddress

			if reader.status != 0:
				message = reader.receiveMessage()
				if message == "Retry":
					time.sleep(0.5)
					print "IO ERROR READ FLAGGED, RETRYING"
					message = reader.receiveMessage()
				print "Decrypted message: " + message
				print ":".join(x.encode('hex') for x in message)
				time.sleep(0.5)

		for reader in db.session.query(Reader).all():
			if reader.i2caddress == 5:
				reader.queueMessage("SetSlaveAddress", str(maxSlaveAddress + 1))
				print "Setting reader ", reader.id, " to slave address ", maxSlaveAddress + 1
				if reader.checkForMessages() == "Retry":
					print "IO ERROR WRITE FLAGGED, RETRYING"
					time.sleep(0.5)
					reader.checkForMessages()
				time.sleep(1.5)
			if reader.status != 0: # active or tampered
				if reader.checkForMessages() == "Retry":
					print "IO ERROR WRITE FLAGGED, RETRYING"
					time.sleep(0.5)
					reader.checkForMessages()
				time.sleep(0.5)

	
	""" old reader = Reader.query.get(int(1))
	while True:
		time.sleep(1.0)
		message = reader.receiveMessage()
		if message == "Retry":
			time.sleep(0.5)
			print "IO ERROR READ FLAGGED, RETRYING"
			message = reader.receiveMessage()
		print "Decrypted message: " + message
		print ":".join(x.encode('hex') for x in message)
		time.sleep(0.5)
		if reader.checkForMessages() == "Retry":
			print "IO ERROR WRITE FLAGGED, RETRYING"
			time.sleep(0.5)
			reader.checkForMessages()"""